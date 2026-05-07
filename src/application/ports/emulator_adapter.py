"""Porta para adaptadores de emuladores."""

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from src.domain.entities.emulator import Emulator
from src.domain.entities.game import Game
from src.domain.value_objects.graphics_profile import GraphicsProfile


@dataclass(frozen=True)
class EmulatorCapabilities:
    """Capacidades funcionais de um emulador."""

    supports_local_multiplayer: bool = False
    supports_remote_multiplayer: bool = False
    supports_controller_profiles: bool = False
    supports_graphics_profiles: bool = False
    max_local_players: int = 1


class EmulatorAdapter(Protocol):
    """Contrato que isola detalhes especificos de cada emulador."""

    emulator_id: str
    capabilities: EmulatorCapabilities

    def build_launch_command(self, emulator: Emulator, game: Game) -> str:
        """Constroi o comando para abrir um jogo."""
        ...

    def apply_graphics_profile(
        self,
        emulator: Emulator,
        profile: GraphicsProfile,
    ) -> None:
        """Aplica perfil grafico antes do jogo abrir."""
        ...

    def find_save_files(self, game: Game) -> list[Path]:
        """Encontra saves associados ao jogo."""
        ...
