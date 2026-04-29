# src/infrastructure/container.py — DI Container simples
from pathlib import Path

from src.application.services.cover_service import CoverService
from src.infrastructure.covers.fallback_extractor import FallbackCoverExtractor
from src.infrastructure.covers.nds_extractor import NDSCoverExtractor
from src.infrastructure.covers.psp_extractor import PSPCoverExtractor
from src.infrastructure.persistence.local_game_repo import LocalGameRepository


class Container:
    def __init__(self):
        self._game_repo = None
        self._cover_service = None
    
    @property
    def game_repo(self) -> LocalGameRepository:
        if not self._game_repo:
            self._game_repo = LocalGameRepository(Path("roms"))
        return self._game_repo
    
    @property
    def cover_service(self) -> CoverService:
        if not self._cover_service:
            self._cover_service = CoverService(
                extractors=[
                    FallbackCoverExtractor(), 
                    NDSCoverExtractor(), 
                    PSPCoverExtractor()
                ],
                output_dir=Path("assets/covers")
            )
        return self._cover_service

container = Container()  # Singleton