"""Porta para escrita de configuracoes graficas por emulador."""

from typing import Protocol

from src.domain.entities.emulator import Emulator
from src.domain.value_objects.graphics_profile import GraphicsProfile


class GraphicsConfigWriter(Protocol):
    """Contrato para aplicar um perfil grafico num emulador concreto."""

    def apply(self, emulator: Emulator, profile: GraphicsProfile) -> None:
        """Aplica as settings do perfil no backend real do emulador."""
        ...
