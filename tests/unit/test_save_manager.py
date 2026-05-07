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


def test_create_manual_slot_uses_next_number(tmp_path):
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

    slot_1 = manager.create_manual_slot(game)
    save_path.write_bytes(b"save-data-2")
    slot_2 = manager.create_manual_slot(game)

    assert slot_1.name == "Slot 1"
    assert slot_1.slot_number == 1
    assert slot_1.slot_type == "manual"
    assert (slot_1.file_path / "Mario.sav").read_bytes() == b"save-data"
    assert slot_2.name == "Slot 2"
    assert slot_2.slot_number == 2

    slots = manager.list_save_slots(game)
    assert [slot.name for slot in slots] == ["Slot 1", "Slot 2"]


def test_create_save_slot_manual_alias_uses_numbered_slots(tmp_path):
    rom_path = tmp_path / "Mario.nds"
    rom_path.write_bytes(b"rom")
    (tmp_path / "Mario.sav").write_bytes(b"save-data")

    manager = SaveManager(slots_dir=tmp_path / "slots")
    game = Game(
        id="mario",
        title="Mario",
        rom=Rom(file_path=rom_path, file_size=rom_path.stat().st_size),
    )

    slot = manager.create_save_slot(game, "manual")

    assert slot.name == "Slot 1"


def test_create_auto_backup_replaces_single_slot(tmp_path):
    rom_path = tmp_path / "Pokemon.gba"
    rom_path.write_bytes(b"rom")
    save_path = tmp_path / "Pokemon.sav"
    save_path.write_bytes(b"first")

    manager = SaveManager(slots_dir=tmp_path / "slots")
    game = Game(
        id="pokemon",
        title="Pokemon",
        rom=Rom(file_path=rom_path, file_size=rom_path.stat().st_size),
    )

    first = manager.create_auto_backup(game)
    save_path.write_bytes(b"second")
    second = manager.create_auto_backup(game)

    assert first.name == "Backup automatico"
    assert second.name == "Backup automatico"
    assert first.file_path == second.file_path
    assert (second.file_path / "Pokemon.sav").read_bytes() == b"second"

    slots = manager.list_save_slots(game)
    assert len(slots) == 1
    assert slots[0].slot_type == "auto"


def test_list_save_slots_orders_auto_before_manual(tmp_path):
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

    manager.create_manual_slot(game)
    manager.create_auto_backup(game)
    manager.create_manual_slot(game)

    assert [slot.name for slot in manager.list_save_slots(game)] == [
        "Backup automatico",
        "Slot 1",
        "Slot 2",
    ]


def test_restore_manual_slot_updates_auto_backup_before_restore(tmp_path):
    rom_path = tmp_path / "Pokemon.gba"
    rom_path.write_bytes(b"rom")
    save_path = tmp_path / "Pokemon.sav"
    save_path.write_bytes(b"slot-one")

    manager = SaveManager(slots_dir=tmp_path / "slots")
    game = Game(
        id="pokemon",
        title="Pokemon",
        rom=Rom(file_path=rom_path, file_size=rom_path.stat().st_size),
    )
    manual_slot = manager.create_manual_slot(game)

    save_path.write_bytes(b"current-before-restore")

    assert manager.restore_save_slot(game, manual_slot) is True

    assert save_path.read_bytes() == b"slot-one"
    auto_slot = manager.list_save_slots(game)[0]
    assert auto_slot.slot_type == "auto"
    assert (auto_slot.file_path / "Pokemon.sav").read_bytes() == b"current-before-restore"


def test_delete_auto_slot_is_not_allowed(tmp_path):
    rom_path = tmp_path / "Pokemon.gba"
    rom_path.write_bytes(b"rom")
    (tmp_path / "Pokemon.sav").write_bytes(b"save")

    manager = SaveManager(slots_dir=tmp_path / "slots")
    game = Game(
        id="pokemon",
        title="Pokemon",
        rom=Rom(file_path=rom_path, file_size=rom_path.stat().st_size),
    )
    auto_slot = manager.create_auto_backup(game)

    assert manager.delete_save_slot(auto_slot) is False
    assert auto_slot.file_path.exists()
