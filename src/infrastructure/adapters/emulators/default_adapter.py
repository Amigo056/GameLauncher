"""Adaptador padrao para emuladores sem comportamento especializado."""

from pathlib import Path

from src.application.ports.emulator_adapter import EmulatorAdapter, EmulatorCapabilities
from src.domain.entities.emulator import Emulator
from src.domain.entities.game import Game
from src.domain.value_objects.graphics_profile import GraphicsProfile


class DefaultEmulatorAdapter(EmulatorAdapter):
    """Adaptador minimo que delega o lancamento para a entidade Emulator."""

    emulator_id = "default"
    capabilities = EmulatorCapabilities()

    def build_launch_command(self, emulator: Emulator, game: Game) -> str:
        """Constroi comando usando a configuracao base do emulador."""
        if not game.rom:
            raise ValueError("Jogo sem ROM associada")
        return emulator.build_launch_command(game.rom.file_path)

    def apply_graphics_profile(
        self,
        emulator: Emulator,
        profile: GraphicsProfile,
    ) -> None:
        """Adaptador padrao ainda nao escreve configuracoes graficas."""
        _ = (emulator, profile)

    def find_save_files(self, game: Game) -> list[Path]:
        """Sem regras especificas, procura saves ao lado da ROM."""
        if not game.rom:
            return []

        rom_path = game.rom.file_path
        candidates = []
        for ext in (".sav", ".srm", ".state"):
            save_path = rom_path.with_suffix(ext)
            if save_path.exists():
                candidates.append(save_path)
        return candidates
