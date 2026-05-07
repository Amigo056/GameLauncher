"""Caso de uso: aplicar perfil grafico num emulador."""

from dataclasses import dataclass

from src.application.ports.graphics_config_writer import GraphicsConfigWriter
from src.domain.entities.emulator import Emulator
from src.domain.value_objects.graphics_profile import GraphicsProfile


@dataclass
class ApplyGraphicsProfileUseCase:
    """Aplica um perfil grafico usando a porta de escrita adequada."""

    graphics_writer: GraphicsConfigWriter

    def execute(self, emulator: Emulator, profile: GraphicsProfile) -> None:
        """Valida e aplica perfil grafico."""
        if profile.emulator_id != emulator.id:
            raise ValueError(
                f"Perfil {profile.id} nao pertence ao emulador {emulator.id}"
            )
        self.graphics_writer.apply(emulator, profile)
