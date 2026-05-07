"""Testes para ManualCoverService."""
from src.application.services.manual_cover_service import ManualCoverService


def test_emulator_dir_is_nested_by_emulator_id(tmp_path):
    service = ManualCoverService(base_dir=tmp_path / "manual")

    assert service.emulator_dir("mGBA") == tmp_path / "manual" / "mgba"


def test_ensure_emulator_dir_creates_directory(tmp_path):
    service = ManualCoverService(base_dir=tmp_path / "manual")

    path = service.ensure_emulator_dir("melonds")

    assert path.exists()
    assert path.is_dir()
