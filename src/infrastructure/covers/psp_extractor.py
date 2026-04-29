"""Estratégia: extrai covers de ISOs de PSP usando pycdlib."""
from pathlib import Path
from typing import Optional, Tuple

from src.domain.entities.game import Cover
from src.domain.services.cover_extractor import CoverExtractor


class PSPCoverExtractor(CoverExtractor):
    """
    Extrai ICON0.PNG, PIC1.PNG e título do PARAM.SFO de ISOs de PSP.
    """
    
    PSP_FILES = {
        'icon': 'PSP_GAME/ICON0.PNG',
        'pic': 'PSP_GAME/PIC1.PNG',
        'param': 'PSP_GAME/PARAM.SFO',
    }
    
    @property
    def supported_extensions(self) -> list[str]:
        return [".iso", ".cso"]  # CSO requer descompressão primeiro
    
    def can_extract(self, rom_path: Path) -> bool:
        if rom_path.suffix.lower() not in ['.iso', '.cso']:
            return False
        # Verificar magic do ISO
        return self._is_psp_iso(rom_path)
    
    def extract(self, rom_path: Path, game_id: str, output_dir: Path) -> Tuple[Optional[Cover], Optional[str]]:
        try:
            import pycdlib
        except ImportError:
            print(f"[PSP] pycdlib não instalado")
            return None, None
        
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"[PSP] A tentar extrair: {rom_path.name}")
        print(f"[PSP] can_extract: {self.can_extract(rom_path)}")

        iso = pycdlib.PyCdlib()
        iso.open(str(rom_path))
        
        try:
            cover_path = None
            title = None
            
            # PIC1.PNG (capa principal 480x272)
            pic_data = self._read_iso_file(iso, self.PSP_FILES['pic'])
            print(f"[PSP] PIC1.PNG data: {len(pic_data) if pic_data else None}")

            if pic_data:
                cover_path = output_dir / f"{game_id}_pic.png"
                cover_path.write_bytes(pic_data)
            else:
                # Fallback: ICON0.PNG (144x80)
                icon_data = self._read_iso_file(iso, self.PSP_FILES['icon'])
                print(f"[PSP] ICON0.PNG data: {len(icon_data) if icon_data else None}")
                if icon_data:
                    cover_path = output_dir / f"{game_id}_icon.png"
                    cover_path.write_bytes(icon_data)
            
            # Título do PARAM.SFO
            param_data = self._read_iso_file(iso, self.PSP_FILES['param'])
            print(f"[PSP] PARAM.SFO data: {len(param_data) if param_data else None}")
            if param_data:
                title = self._parse_sfo_title(param_data)
            
            cover = Cover(local_path=cover_path) if cover_path else None
            return cover, title
            
        finally:
            iso.close()
    
    def _read_iso_file(self, iso, iso_path: str) -> Optional[bytes]:
        import io

        # pycdlib exige slash inicial
        path = '/' + iso_path.lstrip('/')

        # PSP ISOs podem usar Joliet, Rock Ridge ou ISO 9660 puro
        # Tentar os três até um funcionar
        for path_type in ['joliet_path', 'iso_path', 'rr_path']:
            try:
                buf = io.BytesIO()
                iso.get_file_from_iso_fp(buf, **{path_type: path})
                data = buf.getvalue()
                if data:
                    return data
            except Exception:
                continue

        return None
    
    def _parse_sfo_title(self, data: bytes) -> Optional[str]:
        try:
            import struct
            if len(data) < 20 or data[0:4] != b'\x00PSF':
                return None
            
            key_table_start = struct.unpack('<I', data[8:12])[0]
            data_table_start = struct.unpack('<I', data[12:16])[0]
            index_entries = struct.unpack('<I', data[16:20])[0]
            
            offset = 20
            for _ in range(index_entries):
                if offset + 16 > len(data):
                    break
                
                key_offset = struct.unpack('<H', data[offset:offset+2])[0]
                val_offset = struct.unpack('<I', data[offset+12:offset+16])[0]
                
                key_abs = key_table_start + key_offset
                key_end = data.find(b'\x00', key_abs)
                key = data[key_abs:key_end].decode('ascii', errors='ignore')
                
                if key == 'TITLE':
                    val_abs = data_table_start + val_offset
                    val_end = data.find(b'\x00', val_abs)
                    if val_end == -1:
                        val_end = val_abs + 64
                    title = data[val_abs:val_end].decode('utf-8', errors='ignore').strip()
                    if title:
                        return title
                
                offset += 16
            
            return None
        except Exception:
            return None
    
    def _is_psp_iso(self, iso_path: Path) -> bool:
        try:
            with open(iso_path, 'rb') as f:
                f.seek(0)
                data = f.read(65536)
                return b'PSP_GAME' in data
        except Exception:
            return False