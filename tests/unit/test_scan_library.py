"""Testes para ScanLibraryUseCase com processamento paralelo."""
from pathlib import Path
from unittest.mock import MagicMock, patch
from concurrent.futures import ThreadPoolExecutor
import time

import pytest

from src.application.use_cases.scan_library import ScanLibraryUseCase, ScanProgress
from src.domain.entities.game import Game, Rom, Cover
from src.domain.entities.emulator import Emulator, Platform


class MockCoverService:
    """Mock do CoverService para testes."""
    
    def __init__(self, delay: float = 0.01):
        self.delay = delay
        self.call_count = 0
    
    def resolve_cover(self, rom_path: Path, game_id: str, emulator_id: str):
        self.call_count += 1
        time.sleep(self.delay)  # Simula I/O
        return Cover(local_path=Path(f"covers/{game_id}.png")), f"Real {game_id}"


class MockGameRepository:
    """Mock do GameRepository para testes."""
    
    def __init__(self, games: list[Game] = None):
        self._games = games or []
        self.clear_cache_called = False
    
    def get_installed_games(self, emulator=None):
        return self._games.copy()
    
    def clear_cache(self):
        self.clear_cache_called = True


class TestScanLibraryParallel:
    """Testes para scan paralelo."""

    @pytest.fixture
    def emulator(self):
        return Emulator(
            id="melonds",
            name="Nintendo DS",
            platform=Platform.NINTENDO_DS,
            executable_path=Path("emu.exe"),
            supported_extensions=[".nds"],
        )

    @pytest.fixture
    def mock_games(self):
        """Cria 10 jogos mock para testes."""
        games = []
        for i in range(10):
            game = Game(
                id=f"game-{i}",
                title=f"Game {i}",
                rom=Rom(file_path=Path(f"roms/game{i}.nds")),
            )
            games.append(game)
        return games

    def test_sequential_for_small_libraries(self, emulator, mock_games):
        """Bibliotecas pequenas (<=4 jogos) devem usar processamento sequencial."""
        small_games = mock_games[:3]
        repo = MockGameRepository(small_games)
        cover_service = MockCoverService(delay=0.01)
        
        use_case = ScanLibraryUseCase(repo, cover_service)
        
        start = time.time()
        result = use_case.execute(emulator)
        elapsed = time.time() - start
        
        assert len(result) == 3
        assert cover_service.call_count == 3
        # Sequencial: 3 * 0.01s = ~0.03s
        assert elapsed >= 0.03

    def test_parallel_for_large_libraries(self, emulator, mock_games):
        """Bibliotecas grandes (>4 jogos) devem usar processamento paralelo."""
        repo = MockGameRepository(mock_games)
        cover_service = MockCoverService(delay=0.01)
        
        use_case = ScanLibraryUseCase(repo, cover_service)
        
        start = time.time()
        result = use_case.execute(emulator)
        elapsed = time.time() - start
        
        assert len(result) == 10
        assert cover_service.call_count == 10
        # Paralelo com 4 workers: ~0.03s (3 chunks de 4, 4, 2)
        # Deve ser significativamente mais rápido que sequencial (0.1s)
        assert elapsed < 0.08, f"Scan paralelo demorou {elapsed:.3f}s, esperado < 0.08s"

    def test_progress_callback_called(self, emulator, mock_games):
        """O callback de progresso deve ser chamado durante o scan."""
        repo = MockGameRepository(mock_games)
        cover_service = MockCoverService(delay=0.001)
        
        use_case = ScanLibraryUseCase(repo, cover_service)
        
        progress_calls = []
        def callback(progress: ScanProgress):
            progress_calls.append(progress)
        
        use_case.execute(emulator, progress_callback=callback)
        
        # Deve haver pelo menos uma chamada por chunk
        assert len(progress_calls) > 0
        # Última chamada deve ter 100%
        assert progress_calls[-1].percent == 100.0
        assert progress_calls[-1].completed == 10

    def test_force_refresh_clears_cache(self, emulator, mock_games):
        """force_refresh deve limpar o cache antes de scanear."""
        repo = MockGameRepository(mock_games)
        cover_service = MockCoverService()
        
        use_case = ScanLibraryUseCase(repo, cover_service)
        use_case.force_refresh(emulator)
        
        assert repo.clear_cache_called is True

    def test_empty_library(self, emulator):
        """Biblioteca vazia deve retornar lista vazia rapidamente."""
        repo = MockGameRepository([])
        cover_service = MockCoverService()
        
        use_case = ScanLibraryUseCase(repo, cover_service)
        result = use_case.execute(emulator)
        
        assert result == []
        assert cover_service.call_count == 0

    def test_error_handling(self, emulator, mock_games):
        """Erros em extratores individuais não devem quebrar o scan."""
        repo = MockGameRepository(mock_games)
        
        # Mock que falha no jogo 5
        def failing_resolve(rom_path, game_id, emulator_id):
            if "game-5" in game_id:
                raise RuntimeError("Simulated extraction error")
            return Cover(local_path=Path(f"covers/{game_id}.png")), f"Real {game_id}"
        
        cover_service = MagicMock()
        cover_service.resolve_cover = failing_resolve
        
        use_case = ScanLibraryUseCase(repo, cover_service)
        result = use_case.execute(emulator)
        
        # Todos os 10 jogos devem estar presentes, mesmo com erro no 5
        assert len(result) == 10
        # Jogo 5 não deve ter cover
        assert result[5].cover.local_path is None

    def test_thread_safety(self, emulator, mock_games):
        """Verifica que o scan paralelo não corrompe dados."""
        repo = MockGameRepository(mock_games)
        cover_service = MockCoverService(delay=0.005)
        
        use_case = ScanLibraryUseCase(repo, cover_service)
        
        # Executar múltiplas vezes para verificar consistência
        for _ in range(3):
            result = use_case.execute(emulator)
            assert len(result) == 10
            # Verificar que todos os IDs são únicos
            ids = [g.id for g in result]
            assert len(set(ids)) == 10

    def test_chunk_processing(self, emulator):
        """Verifica que jogos são processados em chunks."""
        # Criar 20 jogos para garantir múltiplos chunks
        games = []
        for i in range(20):
            games.append(Game(
                id=f"game-{i}",
                title=f"Game {i}",
                rom=Rom(file_path=Path(f"roms/game{i}.nds")),
            ))
        
        repo = MockGameRepository(games)
        cover_service = MockCoverService(delay=0.001)
        
        use_case = ScanLibraryUseCase(repo, cover_service)
        
        progress_calls = []
        def callback(progress: ScanProgress):
            progress_calls.append(progress)
        
        use_case.execute(emulator, progress_callback=callback)
        
        # Com CHUNK_SIZE=8 e 20 jogos: 3 chunks (8, 8, 4)
        # Deve haver pelo menos 3 chamadas de progresso
        assert len(progress_calls) >= 3