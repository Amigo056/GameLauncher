"""Writer grafico neutro para emuladores ainda nao implementados."""

import logging

from src.application.ports.graphics_config_writer import GraphicsConfigWriter
from src.domain.entities.emulator import Emulator
from src.domain.value_objects.graphics_profile import GraphicsProfile


logger = logging.getLogger(__name__)


class NoopGraphicsConfigWriter(GraphicsConfigWriter):
    """Nao escreve configs, mas preserva o fluxo arquitetural."""

    def apply(self, emulator: Emulator, profile: GraphicsProfile) -> None:
        """Regista que o perfil foi escolhido, sem alterar ficheiros ainda."""
        logger.debug(
            "Graphics profile selected but no writer is implemented yet: %s/%s",
            emulator.id,
            profile.level.value,
        )
