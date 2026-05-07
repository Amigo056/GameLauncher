"""Value object para perfis graficos de emuladores."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class GraphicsProfileLevel(Enum):
    """Niveis padrao de configuracao grafica."""

    PERFORMANCE = "performance"
    BALANCED = "balanced"
    QUALITY = "quality"

    @property
    def label(self) -> str:
        """Nome amigavel para UI."""
        labels = {
            self.PERFORMANCE: "Performance",
            self.BALANCED: "Equilibrado",
            self.QUALITY: "Qualidade",
        }
        return labels[self]


@dataclass(frozen=True)
class GraphicsProfile:
    """Perfil grafico independente do backend concreto do emulador."""

    emulator_id: str
    level: GraphicsProfileLevel
    settings: dict[str, Any] = field(default_factory=dict)
    description: str = ""

    @property
    def id(self) -> str:
        """Identificador estavel do perfil."""
        return f"{self.emulator_id}:{self.level.value}"
