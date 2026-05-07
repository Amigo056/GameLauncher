"""Container de Injeção de Dependências (DI) manual."""
from pathlib import Path
from typing import Optional

from src.infrastructure.covers.fallback_extractor import FallbackCoverExtractor
from src.application.events import EventBus
from src.infrastructure.persistence.local_game_repo import LocalGameRepository
from src.infrastructure.persistence.session_repo import SQLiteSessionRepository
from src.infrastructure.cache.cover_cache import CoverCache
from src.infrastructure.config.config_loader import ConfigLoader
from src.infrastructure.config.config_validator import ConfigValidator
from src.infrastructure.config.config_mapper import ConfigMapper
from src.application.services.cover_service import CoverService
from src.application.services.settings_service import SettingsService
from src.application.use_cases.scan_library import ScanLibraryUseCase
from src.application.tracking.session_tracker import SessionTracker
from src.infrastructure.covers.nds_extractor import NDSCoverExtractor
from src.infrastructure.covers.psp_extractor import PSPCoverExtractor
from src.infrastructure.covers.gba_extractor import GBAScreenshotExtractor


class Container:
    """Container DI manual — lazy initialization."""

    def __init__(self):
        self._game_repo: Optional[LocalGameRepository] = None
        self._session_repo: Optional[SQLiteSessionRepository] = None
        self._cover_service: Optional[CoverService] = None
        self._event_bus: Optional[EventBus] = None
        self._session_tracker: Optional[SessionTracker] = None
        self._settings_service: Optional[SettingsService] = None
        self._config_loader: Optional[ConfigLoader] = None
        self._config_validator: Optional[ConfigValidator] = None
        self._config_mapper: Optional[ConfigMapper] = None
        self._cover_cache: Optional[CoverCache] = None
        self._mgba_path: Optional[Path] = None

    @property
    def event_bus(self) -> EventBus:
        if self._event_bus is None:
            self._event_bus = EventBus()
        return self._event_bus

    @property
    def game_repo(self) -> LocalGameRepository:
        if self._game_repo is None:
            self._game_repo = LocalGameRepository(
                base_path=Path("roms"),
                calculate_checksums=False,
            )
        return self._game_repo

    @property
    def session_repo(self) -> SQLiteSessionRepository:
        if self._session_repo is None:
            self._session_repo = SQLiteSessionRepository(
                db_path=Path("data/sessions.db")
            )
        return self._session_repo

    @property
    def cover_cache(self) -> CoverCache:
        if self._cover_cache is None:
            self._cover_cache = CoverCache()
        return self._cover_cache

    @property
    def cover_service(self) -> CoverService:
        if self._cover_service is None:
            extractors = [
                NDSCoverExtractor(),
                PSPCoverExtractor(),
                FallbackCoverExtractor(),
            ]
            #gba = self._resolve_mgba_path()
            #if gba:
             #   extractors.append(GBAScreenshotExtractor(mgba_path=gba))
            self._cover_service = CoverService(
                extractors=extractors,
                output_dir=Path("assets/covers"),
                cover_cache=self.cover_cache,
            )
        return self._cover_service

    @property
    def settings_service(self) -> SettingsService:
        if self._settings_service is None:
            self._settings_service = SettingsService()
        return self._settings_service

    @property
    def session_tracker(self) -> SessionTracker:
        if self._session_tracker is None:
            self._session_tracker = SessionTracker(
                session_repo=self.session_repo,
                event_bus=self.event_bus,
            )
        return self._session_tracker

    @property
    def config_loader(self) -> ConfigLoader:
        if self._config_loader is None:
            self._config_loader = ConfigLoader(config_dir=Path("config"))
        return self._config_loader

    @property
    def config_validator(self) -> ConfigValidator:
        if self._config_validator is None:
            self._config_validator = ConfigValidator()
        return self._config_validator

    @property
    def config_mapper(self) -> ConfigMapper:
        if self._config_mapper is None:
            self._config_mapper = ConfigMapper()
        return self._config_mapper

    def _resolve_mgba_path(self) -> Optional[Path]:
        if self._mgba_path is None:
            try:
                from src.domain.entities.emulator import load_emulator_from_json
                emu = load_emulator_from_json("mgba")
                if emu and emu.executable_path and emu.executable_path.exists():
                    self._mgba_path = emu.executable_path
            except Exception:
                pass
        return self._mgba_path

    def create_scan_use_case(self) -> ScanLibraryUseCase:
        return ScanLibraryUseCase(
            game_repo=self.game_repo,
            cover_service=self.cover_service,
        )

    def initialize_tracking(self):
        """Inicializa o tracking de sessões no startup."""
        self.session_tracker.start()
        print("[Container] Tracking de sessões inicializado")


container = Container()