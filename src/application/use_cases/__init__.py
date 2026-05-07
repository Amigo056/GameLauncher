"""Casos de uso da aplicacao."""

from src.application.use_cases.analyze_hardware import AnalyzeHardwareUseCase
from src.application.use_cases.apply_graphics_profile import ApplyGraphicsProfileUseCase
from src.application.use_cases.launch_game import LaunchGameUseCase, LaunchResult
from src.application.use_cases.recommend_emulators import RecommendEmulatorsUseCase
from src.application.use_cases.scan_library import ScanLibraryUseCase, ScanProgress

__all__ = [
    "AnalyzeHardwareUseCase",
    "ApplyGraphicsProfileUseCase",
    "LaunchGameUseCase",
    "LaunchResult",
    "RecommendEmulatorsUseCase",
    "ScanLibraryUseCase",
    "ScanProgress",
]
