"""Caso de uso: analisar hardware do PC."""

from dataclasses import dataclass

from src.application.ports.hardware_probe import HardwareProbe
from src.domain.value_objects.hardware_profile import HardwareProfile


@dataclass
class AnalyzeHardwareUseCase:
    """Orquestra a leitura de hardware atraves de uma porta."""

    hardware_probe: HardwareProbe

    def execute(self) -> HardwareProfile:
        """Retorna o perfil de hardware atual."""
        return self.hardware_probe.inspect()
