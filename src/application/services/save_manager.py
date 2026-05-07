"""Serviço de aplicação: gestão de slots de save."""
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from src.domain.entities.game import Game


@dataclass
class SaveSlot:
    """Representa um slot de save para um jogo."""
    name: str
    game_id: str
    emulator_id: str
    created_at: datetime
    file_path: Path
    file_size: int = 0


class SaveManager:
    """
    Gestiona slots de save para jogos.
    
    Permite criar múltiplos backups do save atual,
    restaurar para um slot anterior, e listar todos os slots.
    """

    SLOTS_DIR = Path("saves/slots")
    SAV_EXTENSIONS = {".sav", ".srm", ".state", ".st0", ".st1", ".st2", ".st3", ".st4", ".st5"}

    def __init__(self, slots_dir: Optional[Path] = None):
        self.slots_dir = Path(slots_dir) if slots_dir else self.SLOTS_DIR
        self.slots_dir.mkdir(parents=True, exist_ok=True)

    def _get_game_slots_dir(self, game: Game) -> Path:
        """Retorna pasta de slots para um jogo específico."""
        if not game.rom:
            raise ValueError("Jogo não tem ROM associada")
        emu_id = game.rom.file_path.parent.name.lower()
        game_dir = self.slots_dir / emu_id / game.id
        game_dir.mkdir(parents=True, exist_ok=True)
        return game_dir

    def _find_save_files(self, game: Game) -> List[Path]:
        """Encontra todos os ficheiros de save associados à ROM."""
        if not game.rom:
            return []
        
        rom_path = game.rom.file_path
        rom_dir = rom_path.parent
        rom_stem = rom_path.stem
        
        saves = []
        for ext in self.SAV_EXTENSIONS:
            # Save com mesmo nome da ROM
            candidate = rom_dir / f"{rom_stem}{ext}"
            if candidate.exists():
                saves.append(candidate)
            # Saves numerados (MyBoy style)
            for i in range(10):
                numbered = rom_dir / f"{rom_stem}.st{i}"
                if numbered.exists():
                    saves.append(numbered)
                numbered_png = rom_dir / f"{rom_stem}.st{i}.png"
                if numbered_png.exists():
                    saves.append(numbered_png)
        
        return saves

    def list_current_saves(self, game: Game) -> List[Path]:
        """Lista ficheiros de save atualmente ao lado da ROM."""
        return sorted(set(self._find_save_files(game)))

    def create_save_slot(self, game: Game, slot_name: str) -> SaveSlot:
        """
        Cria um novo slot de save copiando os saves atuais do jogo.
        
        Args:
            game: Jogo cujos saves serão copiados
            slot_name: Nome identificador do slot (ex: "Antes Elite 4")
            
        Returns:
            SaveSlot criado
        """
        slots_dir = self._get_game_slots_dir(game)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        slot_dir = slots_dir / f"{timestamp}_{slot_name}"
        slot_dir.mkdir(parents=True, exist_ok=True)
        
        save_files = self._find_save_files(game)
        total_size = 0
        
        for save_file in save_files:
            dest = slot_dir / save_file.name
            shutil.copy2(save_file, dest)
            total_size += dest.stat().st_size
        
        return SaveSlot(
            name=slot_name,
            game_id=game.id,
            emulator_id=game.rom.file_path.parent.name.lower() if game.rom else "unknown",
            created_at=datetime.now(),
            file_path=slot_dir,
            file_size=total_size,
        )

    def list_save_slots(self, game: Game) -> List[SaveSlot]:
        """
        Lista todos os slots de save de um jogo.
        
        Returns:
            Lista ordenada por data de criação (mais recente primeiro)
        """
        slots_dir = self._get_game_slots_dir(game)
        slots: List[SaveSlot] = []
        
        if not slots_dir.exists():
            return slots
        
        for slot_dir in sorted(slots_dir.iterdir(), reverse=True):
            if not slot_dir.is_dir():
                continue
            
            # Parse nome: YYYYMMDD_HHMMSS_slot_name
            name_part = slot_dir.name
            if '_' in name_part:
                parts = name_part.split('_', 2)
                if len(parts) >= 3:
                    timestamp_str = f"{parts[0]}_{parts[1]}"
                    slot_name = parts[2]
                    try:
                        created_at = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                    except ValueError:
                        created_at = datetime.fromtimestamp(slot_dir.stat().st_ctime)
                else:
                    slot_name = name_part
                    created_at = datetime.fromtimestamp(slot_dir.stat().st_ctime)
            else:
                slot_name = name_part
                created_at = datetime.fromtimestamp(slot_dir.stat().st_ctime)
            
            total_size = sum(f.stat().st_size for f in slot_dir.iterdir() if f.is_file())
            
            slots.append(SaveSlot(
                name=slot_name,
                game_id=game.id,
                emulator_id=slots_dir.parent.name,
                created_at=created_at,
                file_path=slot_dir,
                file_size=total_size,
            ))
        
        return slots

    def restore_save_slot(self, game: Game, slot: SaveSlot) -> bool:
        """
        Restaura um slot de save para a pasta da ROM.
        
        Args:
            game: Jogo alvo da restauração
            slot: Slot a restaurar
            
        Returns:
            True se sucesso
        """
        if not game.rom:
            return False
        
        if not slot.file_path.exists():
            return False
        
        rom_dir = game.rom.file_path.parent
        
        # Backup do save atual antes de restaurar
        self.create_save_slot(game, "auto_backup_before_restore")
        
        # Copiar ficheiros do slot para a pasta da ROM
        for save_file in slot.file_path.iterdir():
            if save_file.is_file():
                dest = rom_dir / save_file.name
                shutil.copy2(save_file, dest)
        
        return True

    def delete_save_slot(self, slot: SaveSlot) -> bool:
        """Elimina um slot de save permanentemente."""
        try:
            if slot.file_path.exists():
                shutil.rmtree(slot.file_path)
            return True
        except Exception:
            return False
