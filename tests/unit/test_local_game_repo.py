"""Testes unitários para LocalGameRepository."""
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from src.infrastructure.persistence.local_game_repo import LocalGameRepository
from src.domain.entities.game import Game, Region


class TestLocalGameRepository:
    """Testes para repositório de jogos locais."""

    @pytest.fixture
    def repo(self, tmp_path):
        return LocalGameRepository(base_path=tmp_path)

    def test_scan_directory_empty(self, repo, tmp_path):
        """Deve retornar lista vazia para pasta vazia."""
        games = repo.scan_directory(tmp_path, [".nds"])
        assert games == []

    def test_scan_directory_finds_roms(self, repo, tmp_path):
        """Deve encontrar ROMs na pasta."""
        # Criar ficheiros mock
        (tmp_path / "game1.nds").write_text("mock")
        (tmp_path / "game2.nds").write_text("mock")
        
        games = repo.scan_directory(tmp_path, [".nds"])
        assert len(games) == 2
        assert all(isinstance(g, Game) for g in games)

    def test_scan_directory_filters_extensions(self, repo, tmp_path):
        """Deve filtrar por extensão."""
        (tmp_path / "game.nds").write_text("mock")
        (tmp_path / "readme.txt").write_text("mock")
        
        games = repo.scan_directory(tmp_path, [".nds"])
        assert len(games) == 1
        assert games[0].rom.file_path.suffix == ".nds"

    def test_filename_to_id(self, repo):
        """Deve converter nomes para slugs."""
        assert repo._filename_to_id("Super Mario Bros") == "super-mario-bros"
        assert repo._filename_to_id("Pokémon Red") == "pokemon-red"
        assert repo._filename_to_id("Game (USA)") == "game-usa"

    def test_detect_region_usa(self, repo):
        """Deve detetar região USA."""
        assert repo._detect_region_from_filename("Game (USA).nds") == Region.USA
        assert repo._detect_region_from_filename("Game (U).nds") == Region.USA

    def test_detect_region_europe(self, repo):
        """Deve detetar região Europe."""
        assert repo._detect_region_from_filename("Game (EUR).nds") == Region.EUROPE
        assert repo._detect_region_from_filename("Game (E).nds") == Region.EUROPE

    def test_detect_region_unknown(self, repo):
        """Deve retornar UNKNOWN sem região."""
        assert repo._detect_region_from_filename("Game.nds") == Region.UNKNOWN

    def test_clear_cache(self, repo, tmp_path):
        """Deve limpar cache."""
        (tmp_path / "game.nds").write_text("mock")
        repo.scan_directory(tmp_path, [".nds"])
        assert len(repo._cache) > 0
        
        repo.clear_cache()
        assert len(repo._cache) == 0
        assert repo._last_scan is None
