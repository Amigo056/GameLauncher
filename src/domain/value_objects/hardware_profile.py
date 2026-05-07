"""Value object com informacao basica do PC."""

from dataclasses import dataclass


@dataclass(frozen=True)
class HardwareProfile:
    """Resumo do hardware usado para recomendacoes de emuladores."""

    os_name: str
    os_version: str
    cpu_name: str
    cpu_cores: int
    ram_gb: float
    gpu_name: str = "Unknown"
    vram_gb: float | None = None

    @property
    def summary(self) -> str:
        """Resumo curto para UI/logs."""
        return (
            f"{self.cpu_name} | {self.cpu_cores} cores | "
            f"{self.ram_gb:.1f} GB RAM | GPU: {self.gpu_name}"
        )
