"""Caso de uso: escanear biblioteca e enriquecer com covers/títulos."""
from typing import List

from src.domain.entities.game import Game
from src.domain.entities.emulator import Emulator
from src.domain.repositories.game_repository import GameRepository
from src.application.services.cover_service import CoverService


class ScanLibraryUseCase:
    """
    Orquestra o scan de jogos + enriquecimento com covers e títulos reais.
    """

    def __init__(self, game_repo: GameRepository, cover_service: CoverService):
        self.game_repo = game_repo
        self.cover_service = cover_service

    def execute(self, emulator: Emulator) -> List[Game]:
        """
        1. Scan filesystem (repo)
        2. Para cada jogo, tentar obter cover e título real
        3. Retornar jogos enriquecidos
        """
        games = self.game_repo.get_installed_games(emulator)

        for game in games:
            if not game.rom:
                continue

            cover, real_title = self.cover_service.resolve_cover(
                rom_path=game.rom.file_path,
                game_id=game.id,
                emulator_id=emulator.id
            )

            if cover:
                game.cover = cover
            if real_title:
                game.title = real_title

        return games

    def force_refresh(self, emulator: Emulator) -> List[Game]:
        """
        Igual a execute() mas invalida o cache do repositório primeiro.
        Usado pelo botão 'Atualizar' na UI.
        """
        if hasattr(self.game_repo, 'clear_cache'):
            self.game_repo.clear_cache()
        return self.execute(emulator)