"""Adaptadores de comandos/controlos."""

from src.infrastructure.adapters.controllers.controller_detector import (
    ControllerDetector,
    ControllerInfo,
)
from src.infrastructure.adapters.controllers.profile_manager import ProfileManager
from src.infrastructure.adapters.controllers.sdl_to_n64_mapper import (
    N64ControllerProfile,
    SDLMapping,
    SDLToN64Mapper,
)

__all__ = [
    "ControllerDetector",
    "ControllerInfo",
    "N64ControllerProfile",
    "ProfileManager",
    "SDLMapping",
    "SDLToN64Mapper",
]
