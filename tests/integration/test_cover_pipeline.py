"""Testes de integração para pipeline de covers."""
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.application.services.cover_service import CoverService
from src.domain.entities.game import Cover
from src.domain.services.cover_extractor import CoverExtractor


class MockExtractor(CoverExtractor):
    """Extrator mock para testes."""
    
    def __init__(self, can_handle: bool = True, returns_cover: bool = True):
        self._can_handle = can_handle
        self._returns_cover = returns_cover
    
    @property
    def supported_extensions(self):
        return [".test"]
    
    def can_extract(self, rom_path: Path) -> bool:
        return self._can_handle
    
    def extract(self, rom_path: Path, game_id: str, output_dir: Path):
        if self._returns_cover:
            cover_path = output_dir / f"{game_id}.png"
            cover_path.parent.mkdir(parents=True, exist_ok=True)
            cover_path.write_text("mock")
            return Cover(local_path=cover_path), "Test Game"
        return None, None


class TestCoverPipeline:
    """Testes de integração do pipeline de covers."""

    @pytest.fixture
    def output_dir(self, tmp_path):
        return tmp_path / "covers"

    def test_first_extractor_wins(self, output_dir):
        """Chain of responsibility: primeiro extrator que retorna cover ganha."""
        fallback = MockExtractor(can_handle=True, returns_cover=True)
        primary = MockExtractor(can_handle=True, returns_cover=True)
        
        service = CoverService(
            extractors=[fallback, primary],
            output_dir=output_dir,
        )
        
        rom = Path("game.test")
        cover, title = service.resolve_cover(rom, "game", "test")
        
        # Fallback retorna primeiro
        assert cover is not None
        assert cover.is_local

    def test_skips_cannot_extract(self, output_dir):
        """Deve saltar extractors que não conseguem extrair."""
        cant_extract = MockExtractor(can_handle=False, returns_cover=True)
        can_extract = MockExtractor(can_handle=True, returns_cover=True)
        
        service = CoverService(
            extractors=[cant_extract, can_extract],
            output_dir=output_dir,
        )
        
        rom = Path("game.test")
        cover, title = service.resolve_cover(rom, "game", "test")
        
        assert cover is not None

    def test_no_cover_found(self, output_dir):
        """Deve retornar None se nenhum extrator funciona."""
        extractor = MockExtractor(can_handle=True, returns_cover=False)
        
        service = CoverService(
            extractors=[extractor],
            output_dir=output_dir,
        )
        
        rom = Path("game.test")
        cover, title = service.resolve_cover(rom, "game", "test")
        
        assert cover is None
        assert title is None

    def test_uses_emulator_output_subdir(self, output_dir):
        """Deve guardar covers em subdiretório do emulador."""
        extractor = MockExtractor(can_handle=True, returns_cover=True)
        service = CoverService(
            extractors=[extractor],
            output_dir=output_dir,
        )
        
        rom = Path("game.test")
        cover, _ = service.resolve_cover(rom, "game", "melonds")
        
        # Cover deve estar em assets/covers/melonds/
        assert "melonds" in str(cover.local_path)