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
    slot_type: str = "manual"
    slot_number: Optional[int] = None


class SaveManager:
    """
    Gestiona slots de save para jogos.
    
    Permite criar múltiplos backups do save atual,
    restaurar para um slot anterior, e listar todos os slots.
    """

    SLOTS_DIR = Path("saves/slots")
    AUTO_SLOT_DIR = "_auto"
    AUTO_SLOT_NAME = "Backup automatico"
    MANUAL_SLOT_PREFIX = "slot_"
    SAV_EXTENSIONS = {
        ".sav",
        ".srm",
        ".state",
        ".st0",
        ".st1",
        ".st2",
        ".st3",
        ".st4",
        ".st5",
    }

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

    def create_auto_backup(self, game: Game) -> Optional[SaveSlot]:
        """Atualiza o unico backup automatico do jogo."""
        save_files = self.list_current_saves(game)
        if not save_files:
            return None

        slots_dir = self._get_game_slots_dir(game)
        slot_dir = slots_dir / self.AUTO_SLOT_DIR
        created_at = datetime.now()
        total_size = self._copy_save_files(save_files, slot_dir, replace=True)

        return SaveSlot(
            name=self.AUTO_SLOT_NAME,
            game_id=game.id,
            emulator_id=self._emulator_id_for_game(game),
            created_at=created_at,
            file_path=slot_dir,
            file_size=total_size,
            slot_type="auto",
        )

    def create_manual_slot(self, game: Game) -> Optional[SaveSlot]:
        """Cria o proximo slot manual numerado: Slot 1, Slot 2, ..."""
        save_files = self.list_current_saves(game)
        if not save_files:
            return None

        slots_dir = self._get_game_slots_dir(game)
        slot_number = self._next_manual_slot_number(slots_dir)
        slot_dir = slots_dir / f"{self.MANUAL_SLOT_PREFIX}{slot_number:03d}"
        created_at = datetime.now()
        total_size = self._copy_save_files(save_files, slot_dir, replace=False)

        return SaveSlot(
            name=f"Slot {slot_number}",
            game_id=game.id,
            emulator_id=self._emulator_id_for_game(game),
            created_at=created_at,
            file_path=slot_dir,
            file_size=total_size,
            slot_type="manual",
            slot_number=slot_number,
        )

    def create_save_slot(self, game: Game, slot_name: str) -> SaveSlot:
        """
        Cria um novo slot de save copiando os saves atuais do jogo.
        
        Args:
            game: Jogo cujos saves serão copiados
            slot_name: Nome identificador do slot (ex: "Antes Elite 4")
            
        Returns:
            SaveSlot criado
        """
        if slot_name == "manual":
            slot = self.create_manual_slot(game)
            if slot is None:
                raise ValueError("Nao existem saves atuais para copiar")
            return slot

        slots_dir = self._get_game_slots_dir(game)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        slot_dir = slots_dir / f"{timestamp}_{slot_name}"
        slot_dir.mkdir(parents=True, exist_ok=True)
        
        total_size = self._copy_save_files(
            self.list_current_saves(game),
            slot_dir,
            replace=False,
        )
        
        return SaveSlot(
            name=slot_name,
            game_id=game.id,
            emulator_id=self._emulator_id_for_game(game),
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
        
        for slot_dir in sorted(slots_dir.iterdir(), key=lambda path: path.name.lower()):
            if not slot_dir.is_dir():
                continue

            slots.append(self._slot_from_dir(game, slots_dir, slot_dir))
        
        return sorted(slots, key=self._slot_sort_key)

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
        
        if slot.slot_type != "auto":
            self.create_auto_backup(game)
        
        # Copiar ficheiros do slot para a pasta da ROM
        for save_file in slot.file_path.iterdir():
            if save_file.is_file():
                dest = rom_dir / save_file.name
                shutil.copy2(save_file, dest)
        
        return True

    def delete_save_slot(self, slot: SaveSlot) -> bool:
        """Elimina um slot de save permanentemente."""
        if slot.slot_type == "auto":
            return False

        try:
            if slot.file_path.exists():
                shutil.rmtree(slot.file_path)
            return True
        except Exception:
            return False

    def _copy_save_files(
        self,
        save_files: List[Path],
        slot_dir: Path,
        replace: bool,
    ) -> int:
        """Copia ficheiros de save para um slot."""
        if replace and slot_dir.exists():
            shutil.rmtree(slot_dir)
        slot_dir.mkdir(parents=True, exist_ok=True)

        total_size = 0
        for save_file in save_files:
            dest = slot_dir / save_file.name
            shutil.copy2(save_file, dest)
            total_size += dest.stat().st_size
        return total_size

    def _next_manual_slot_number(self, slots_dir: Path) -> int:
        numbers = [
            slot.slot_number
            for slot in self._list_slots_from_dir(slots_dir)
            if slot.slot_type == "manual" and slot.slot_number is not None
        ]
        return (max(numbers) + 1) if numbers else 1

    def _list_slots_from_dir(self, slots_dir: Path) -> List[SaveSlot]:
        slots: List[SaveSlot] = []
        if not slots_dir.exists():
            return slots

        fake_game = Game(id=slots_dir.name, title=slots_dir.name)
        for slot_dir in slots_dir.iterdir():
            if slot_dir.is_dir():
                slots.append(self._slot_from_dir(fake_game, slots_dir, slot_dir))
        return slots

    def _slot_from_dir(self, game: Game, slots_dir: Path, slot_dir: Path) -> SaveSlot:
        name_part = slot_dir.name
        slot_type = "manual"
        slot_number: Optional[int] = None
        created_at = datetime.fromtimestamp(slot_dir.stat().st_ctime)

        if name_part == self.AUTO_SLOT_DIR:
            slot_name = self.AUTO_SLOT_NAME
            slot_type = "auto"
        elif name_part.startswith(self.MANUAL_SLOT_PREFIX):
            raw_number = name_part.removeprefix(self.MANUAL_SLOT_PREFIX)
            try:
                slot_number = int(raw_number)
                slot_name = f"Slot {slot_number}"
            except ValueError:
                slot_name = name_part
        elif "_" in name_part:
            slot_name, created_at = self._parse_legacy_slot_name(name_part, created_at)
        else:
            slot_name = name_part

        total_size = sum(f.stat().st_size for f in slot_dir.iterdir() if f.is_file())
        return SaveSlot(
            name=slot_name,
            game_id=game.id,
            emulator_id=slots_dir.parent.name,
            created_at=created_at,
            file_path=slot_dir,
            file_size=total_size,
            slot_type=slot_type,
            slot_number=slot_number,
        )

    def _parse_legacy_slot_name(
        self,
        name_part: str,
        fallback_created_at: datetime,
    ) -> tuple[str, datetime]:
        parts = name_part.split("_", 2)
        if len(parts) < 3:
            return name_part, fallback_created_at

        timestamp_str = f"{parts[0]}_{parts[1]}"
        try:
            created_at = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
        except ValueError:
            created_at = fallback_created_at
        return parts[2], created_at

    def _slot_sort_key(self, slot: SaveSlot) -> tuple:
        if slot.slot_type == "auto":
            return (0, 0, 0)
        if slot.slot_number is not None:
            return (1, slot.slot_number, 0)
        return (2, 0, -slot.created_at.timestamp())

    def _emulator_id_for_game(self, game: Game) -> str:
        return game.rom.file_path.parent.name.lower() if game.rom else "unknown"
