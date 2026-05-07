"""Caso de uso: escanear biblioteca e enriquecer com covers/títulos."""
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import List, Optional, Callable

from src.domain.entities.game import Game
from src.domain.entities.emulator import Emulator
from src.application.ports.game_repository import GameRepository
from src.application.services.cover_service import CoverService


@dataclass
class ScanProgress:
    """Estado do progresso do scan."""
    total: int = 0
    completed: int = 0
    current_game: str = ""
    
    @property
    def percent(self) -> float:
        if self.total == 0:
            return 0.0
        return (self.completed / self.total) * 100


class ScanLibraryUseCase:
    """
    Orquestra o scan de jogos + enriquecimento com covers e títulos reais.
    
    Usa ThreadPoolExecutor para extrair covers em paralelo,
    melhorando significativamente a performance para bibliotecas grandes.
    """

    # Número máximo de workers para I/O bound tasks
    # 4 é um bom equilíbrio entre performance e uso de recursos
    MAX_WORKERS = 4
    
    # Tamanho do chunk para processamento em batch
    # Processa jogos em grupos para permitir atualizações de UI intermediárias
    CHUNK_SIZE = 8

    def __init__(self, game_repo: GameRepository, cover_service: CoverService):
        self.game_repo = game_repo
        self.cover_service = cover_service

    def execute(
        self,
        emulator: Emulator,
        progress_callback: Optional[Callable[[ScanProgress], None]] = None
    ) -> List[Game]:
        """
        1. Scan filesystem (repo)
        2. Para cada jogo, tentar obter cover e título real (PARALELO)
        3. Retornar jogos enriquecidos
        
        Args:
            emulator: Configuração do emulador
            progress_callback: Chamado a cada chunk processado com o estado atual
        
        Returns:
            Lista de jogos enriquecidos com covers e títulos
        """
        games = self.game_repo.get_installed_games(emulator)
        
        if not games:
            return []
        
        # Se poucos jogos, usar processamento sequencial (overhead do thread pool não vale a pena)
        if len(games) <= 4:
            return self._enrich_sequential(games, emulator, progress_callback)
        
        return self._enrich_parallel(games, emulator, progress_callback)

    def _enrich_sequential(
        self,
        games: List[Game],
        emulator: Emulator,
        progress_callback: Optional[Callable[[ScanProgress], None]] = None
    ) -> List[Game]:
        """Processamento sequencial para poucos jogos."""
        progress = ScanProgress(total=len(games))
        
        for game in games:
            if not game.rom:
                progress.completed += 1
                continue
            
            progress.current_game = game.title
            self._enrich_single_game(game, emulator.id)
            progress.completed += 1
            
            if progress_callback:
                progress_callback(progress)
        
        return games

    def _enrich_parallel(
        self,
        games: List[Game],
        emulator: Emulator,
        progress_callback: Optional[Callable[[ScanProgress], None]] = None
    ) -> List[Game]:
        """Processamento paralelo com ThreadPoolExecutor."""
        progress = ScanProgress(total=len(games))
        
        # Filtrar apenas jogos com ROM
        games_with_rom = [(idx, game) for idx, game in enumerate(games) if game.rom]
        games_without_rom = [(idx, game) for idx, game in enumerate(games) if not game.rom]
        
        # Atualizar progresso para jogos sem ROM
        for _ in games_without_rom:
            progress.completed += 1
        
        # Processar em chunks para permitir atualizações de UI
        results = {}
        
        for chunk_start in range(0, len(games_with_rom), self.CHUNK_SIZE):
            chunk = games_with_rom[chunk_start:chunk_start + self.CHUNK_SIZE]
            chunk_results = self._process_chunk(chunk, emulator.id)
            results.update(chunk_results)
            
            # Atualizar progresso
            progress.completed += len(chunk)
            if chunk:
                progress.current_game = chunk[-1][1].title
            
            if progress_callback:
                progress_callback(progress)
        
        # Aplicar resultados aos jogos
        for idx, game in games_with_rom:
            if idx in results:
                cover, title = results[idx]
                if cover:
                    game.cover = cover
                if title:
                    game.title = title
        
        return games

    def _process_chunk(
        self,
        chunk: List[tuple[int, Game]],
        emulator_id: str
    ) -> dict[int, tuple]:
        """Processa um chunk de jogos em paralelo."""
        results = {}
        
        with ThreadPoolExecutor(max_workers=self.MAX_WORKERS) as executor:
            # Submeter todas as tarefas do chunk
            future_to_idx = {
                executor.submit(
                    self._enrich_single_game_safe,
                    game,
                    emulator_id
                ): idx
                for idx, game in chunk
            }
            
            # Recolher resultados à medida que completam
            for future in as_completed(future_to_idx):
                idx = future_to_idx[future]
                try:
                    results[idx] = future.result()
                except Exception as e:
                    # Log do erro mas não quebra o scan
                    print(f"[Scan] Erro a processar jogo {idx}: {e}")
                    results[idx] = (None, None)
        
        return results

    def _enrich_single_game(self, game: Game, emulator_id: str) -> None:
        """Enriquece um único jogo (versão in-place)."""
        if not game.rom:
            return
        
        cover, real_title = self.cover_service.resolve_cover(
            rom_path=game.rom.file_path,
            game_id=game.id,
            emulator_id=emulator_id
        )

        if cover:
            game.cover = cover
        if real_title:
            game.title = real_title

    def _enrich_single_game_safe(
        self,
        game: Game,
        emulator_id: str
    ) -> tuple:
        """Versão thread-safe que retorna tuplo em vez de modificar in-place.
        
        Importante: CoverExtractor pode não ser thread-safe, por isso
        capturamos exceções e retornamos (cover, title) como tuplo.
        """
        try:
            cover, real_title = self.cover_service.resolve_cover(
                rom_path=game.rom.file_path,
                game_id=game.id,
                emulator_id=emulator_id
            )
            return (cover, real_title)
        except Exception as e:
            print(f"[Scan] Erro a extrair cover para {game.id}: {e}")
            return (None, None)

    def force_refresh(
        self,
        emulator: Emulator,
        progress_callback: Optional[Callable[[ScanProgress], None]] = None
    ) -> List[Game]:
        """
        Igual a execute() mas invalida o cache do repositório primeiro.
        Usado pelo botão 'Atualizar' na UI.
        """
        if hasattr(self.game_repo, 'clear_cache'):
            self.game_repo.clear_cache()
        return self.execute(emulator, progress_callback)
