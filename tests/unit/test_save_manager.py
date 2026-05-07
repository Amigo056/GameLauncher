"""Testes para SaveManager."""
from pathlib import Path

from src.application.services.save_manager import SaveManager
from src.domain.entities.game import Game, Rom


def test_list_current_saves_finds_matching_files(tmp_path):
    rom_path = tmp_path / "Pokemon.gba"
    rom_path.write_bytes(b"rom")
    save_path = tmp_path / "Pokemon.sav"
    save_path.write_bytes(b"save")

    manager = SaveManager(slots_dir=tmp_path / "slots")
    game = Game(
        id="pokemon",
        title="Pokemon",
        rom=Rom(file_path=rom_path, file_size=rom_path.stat().st_size),
    )

    assert manager.list_current_saves(game) == [save_path]


def test_create_save_slot_copies_current_saves(tmp_path):
    rom_path = tmp_path / "Mario.nds"
    rom_path.write_bytes(b"rom")
    save_path = tmp_path / "Mario.sav"
    save_path.write_bytes(b"save-data")

    manager = SaveManager(slots_dir=tmp_path / "slots")
    game = Game(
        id="mario",
        title="Mario",
        rom=Rom(file_path=rom_path, file_size=rom_path.stat().st_size),
    )

    slot = manager.create_save_slot(game, "manual")

    assert slot.file_size == len(b"save-data")
    assert (slot.file_path / "Mario.sav").read_bytes() == b"save-data"
    assert manager.list_save_slots(game)[0].name == "manual"
