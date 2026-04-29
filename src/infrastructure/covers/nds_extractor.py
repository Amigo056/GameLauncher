"""Estratégia: extrai covers de ROMs Nintendo DS (.nds)."""
import struct
from pathlib import Path
from typing import Optional, Tuple
from PIL import Image

from src.domain.entities.game import Cover
from src.domain.services.cover_extractor import CoverExtractor


class NDSCoverExtractor(CoverExtractor):
    """
    Extrai ícone (32x32) e título de ROMs Nintendo DS.

    Formato do banner NDS (versão 1):
    - Offset 0x000: versão (2 bytes)
    - Offset 0x002: CRC16 (2 bytes)
    - Offset 0x004: reservado (28 bytes)
    - Offset 0x020: tile data (512 bytes, 4bpp)
    - Offset 0x220: paleta (32 bytes, 16 cores BGR555)
    - Offset 0x240: títulos em várias línguas (6 x 256 bytes UTF-16LE)

    Versão 2/3 (DSi enhanced):
    - Tile data animado maior
    - Mais idiomas
    """

    # Pointer para o banner dentro do header da ROM
    BANNER_OFFSET_LOC = 0x068

    # Tamanhos mínimos do banner por versão
    BANNER_SIZE_V1 = 0x840

    # Tamanho máximo a ler (versão DSi)
    BANNER_READ_SIZE = 0x23C0

    # Dimensões do ícone NDS
    NDS_ICON_WIDTH  = 32
    NDS_ICON_HEIGHT = 32
    TILE_SIZE       = 8   # tiles são 8×8 pixels

    @property
    def supported_extensions(self) -> list[str]:
        return [".nds"]

    def can_extract(self, rom_path: Path) -> bool:
        """
        Valida de forma leve se o ficheiro é uma ROM NDS com banner válido.
        Não usa o campo de 'header size' em 0x15E — esse campo não existe
        no formato NDS e causava rejeição de todos os ROMs válidos.
        """
        if rom_path.suffix.lower() != ".nds":
            return False
        try:
            with open(rom_path, "rb") as f:
                # O ficheiro tem de ter pelo menos o header básico (0x200 bytes)
                file_size = f.seek(0, 2)
                if file_size < 0x200:
                    return False

                # Ler o pointer para o banner
                f.seek(self.BANNER_OFFSET_LOC)
                raw = f.read(4)
                if len(raw) < 4:
                    return False

                banner_offset = struct.unpack("<I", raw)[0]

                # Banner offset tem de existir e caber dentro do ficheiro
                return 0 < banner_offset < (file_size - self.BANNER_SIZE_V1)

        except Exception:
            return False

    def extract(
        self, rom_path: Path, game_id: str, output_dir: Path
    ) -> Tuple[Optional[Cover], Optional[str]]:
        try:
            with open(rom_path, "rb") as f:
                f.seek(self.BANNER_OFFSET_LOC)
                banner_offset = struct.unpack("<I", f.read(4))[0]

                if banner_offset == 0:
                    return None, None

                f.seek(banner_offset)
                banner_data = f.read(self.BANNER_READ_SIZE)

            if len(banner_data) < self.BANNER_SIZE_V1:
                return None, None

            version = struct.unpack("<H", banner_data[0:2])[0]

            icon_img = self._extract_icon(banner_data, version)
            title    = self._extract_title(banner_data)

            if icon_img:
                output_dir = Path(output_dir)
                output_dir.mkdir(parents=True, exist_ok=True)

                cover_path = output_dir / f"{game_id}_icon.png"
                icon_img.save(cover_path, "PNG")
                return Cover(local_path=cover_path), title

            return None, title

        except Exception as e:
            print(f"[NDS] Erro a extrair de {rom_path.name}: {e}")
            return None, None

    # ─────────────────────────────────────────────
    # ÍCONE
    # ─────────────────────────────────────────────

    def _extract_icon(
        self, banner_data: bytes, version: int
    ) -> Optional[Image.Image]:
        """Extrai ícone 32×32 do banner e devolve uma imagem RGBA 128×128."""
        try:
            tile_offset    = 0x020
            palette_offset = 0x220  # versão 1 (DS standard)

            if version in (2, 3):
                # DSi enhanced: tile data animado maior, paleta diferente
                tile_data    = banner_data[tile_offset : tile_offset + 0x1200]
                palette_data = banner_data[0x1240 : 0x1240 + 0x200]
            else:
                tile_data    = banner_data[tile_offset : tile_offset + 0x200]
                palette_data = banner_data[palette_offset : palette_offset + 0x20]

            palette = self._decode_palette(palette_data)
            pixels  = self._decode_tiles(tile_data, palette)

            img = Image.new("RGBA", (self.NDS_ICON_WIDTH, self.NDS_ICON_HEIGHT))
            img.putdata(pixels)

            # Escalar para 128×128 com NEAREST para manter o look pixel-art
            img = img.resize((128, 128), Image.Resampling.NEAREST)
            return img

        except Exception as e:
            print(f"[NDS] Erro a decodificar ícone: {e}")
            return None

    def _decode_palette(self, palette_data: bytes) -> list[tuple]:
        """
        Converte paleta BGR555 para lista de tuplos RGBA.
        Índice 0 é SEMPRE transparente no formato NDS,
        independentemente do valor armazenado.
        """
        palette: list[tuple] = []
        for idx, offset in enumerate(range(0, len(palette_data), 2)):
            if offset + 1 >= len(palette_data):
                break
            if idx == 0:
                palette.append((0, 0, 0, 0))   # índice 0 = transparente
                continue
            color = struct.unpack("<H", palette_data[offset : offset + 2])[0]
            r = ((color >>  0) & 0x1F) << 3
            g = ((color >>  5) & 0x1F) << 3
            b = ((color >> 10) & 0x1F) << 3
            palette.append((r, g, b, 255))
        return palette

    def _decode_tiles(self, tile_data: bytes, palette: list) -> list:
        """Decodifica tiles 4bpp (8×8) para lista plana de pixels RGBA 32×32."""
        pixels   = [(0, 0, 0, 0)] * (self.NDS_ICON_WIDTH * self.NDS_ICON_HEIGHT)
        tiles_x  = self.NDS_ICON_WIDTH  // self.TILE_SIZE   # 4
        tiles_y  = self.NDS_ICON_HEIGHT // self.TILE_SIZE   # 4
        tile_idx = 0

        for ty in range(tiles_y):
            for tx in range(tiles_x):
                tile_base = tile_idx * 32   # 32 bytes por tile (4bpp, 8×8)

                for py in range(self.TILE_SIZE):
                    for px in range(0, self.TILE_SIZE, 2):
                        byte_offset = tile_base + py * 4 + px // 2
                        if byte_offset >= len(tile_data):
                            continue

                        byte = tile_data[byte_offset]

                        # nibble baixo → pixel esquerdo
                        idx1   = byte & 0x0F
                        color1 = palette[idx1] if idx1 < len(palette) else (0, 0, 0, 0)

                        # nibble alto → pixel direito
                        idx2   = (byte >> 4) & 0x0F
                        color2 = palette[idx2] if idx2 < len(palette) else (0, 0, 0, 0)

                        x   = tx * self.TILE_SIZE + px
                        y   = ty * self.TILE_SIZE + py
                        pos = y * self.NDS_ICON_WIDTH + x

                        if pos < len(pixels):
                            pixels[pos] = color1
                        if pos + 1 < len(pixels):
                            pixels[pos + 1] = color2

                tile_idx += 1

        return pixels

    # ─────────────────────────────────────────────
    # TÍTULO
    # ─────────────────────────────────────────────

    def _extract_title(self, banner_data: bytes) -> Optional[str]:
        """
        Tenta extrair o título por ordem de preferência de idioma.
        Cada entrada tem 256 bytes em UTF-16LE.

        Offsets:
            0x240 Japonês
            0x340 Inglês   ← preferido
            0x440 Francês
            0x540 Alemão
            0x640 Italiano
            0x740 Espanhol
        """
        language_offsets = [
            ("english",  0x340),
            ("japanese", 0x240),
            ("french",   0x440),
            ("spanish",  0x740),
        ]

        for _lang, offset in language_offsets:
            end = offset + 256
            if end > len(banner_data):
                continue

            raw = banner_data[offset:end]
            try:
                text = raw.decode("utf-16-le", errors="ignore")
                # Remover null-terminators e espaços
                text = text.replace("\x00", "").strip()
                # Substituir quebras de linha (títulos multi-linha) por espaço
                text = " ".join(text.splitlines()).strip()
                if text and len(text) > 1:
                    return text
            except Exception:
                continue

        return None