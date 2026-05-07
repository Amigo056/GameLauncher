"""Porta para analisar hardware do PC."""

from typing import Protocol

from src.domain.value_objects.hardware_profile import HardwareProfile


class HardwareProbe(Protocol):
    """Contrato para obter um perfil de hardware."""

    def inspect(self) -> HardwareProfile:
        """Analisa o PC atual."""
        ...
