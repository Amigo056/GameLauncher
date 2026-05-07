"""Contratos usados pela camada de aplicacao."""

from src.application.ports.cover_extractor import CoverExtractor
from src.application.ports.cover_provider import CoverProvider
from src.application.ports.controller_backend import ControllerBackend
from src.application.ports.emulator_adapter import EmulatorAdapter, EmulatorCapabilities
from src.application.ports.emulator_repository import EmulatorRepository
from src.application.ports.file_system import FileSystem
from src.application.ports.game_repository import (
    DuplicateRomError,
    GameRepository,
    RomNotFoundError,
)
from src.application.ports.graphics_config_writer import GraphicsConfigWriter
from src.application.ports.hardware_probe import HardwareProbe
from src.application.ports.process_manager import ProcessManager
from src.application.ports.session_repository import SessionRepository

__all__ = [
    "ControllerBackend",
    "CoverExtractor",
    "CoverProvider",
    "DuplicateRomError",
    "EmulatorAdapter",
    "EmulatorCapabilities",
    "EmulatorRepository",
    "FileSystem",
    "GameRepository",
    "GraphicsConfigWriter",
    "HardwareProbe",
    "ProcessManager",
    "RomNotFoundError",
    "SessionRepository",
]
