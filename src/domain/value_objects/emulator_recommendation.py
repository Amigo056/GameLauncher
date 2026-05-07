"""Value objects para recomendacoes de emuladores por hardware."""

from dataclasses import dataclass
from enum import Enum


class PerformanceTier(Enum):
    """Peso esperado de um emulador/plataforma."""

    VERY_LIGHT = "muito_leve"
    LIGHT = "leve"
    MEDIUM = "medio"
    HEAVY = "pesado"
    VERY_HEAVY = "muito_pesado"

    @property
    def label(self) -> str:
        """Nome amigavel para UI."""
        labels = {
            self.VERY_LIGHT: "Muito leve",
            self.LIGHT: "Leve",
            self.MEDIUM: "Medio",
            self.HEAVY: "Pesado",
            self.VERY_HEAVY: "Muito pesado",
        }
        return labels[self]


class RecommendationStatus(Enum):
    """Resultado da recomendacao para o PC atual."""

    RECOMMENDED = "recommended"
    TUNE_SETTINGS = "tune_settings"
    NOT_RECOMMENDED = "not_recommended"

    @property
    def label(self) -> str:
        """Nome amigavel para UI."""
        labels = {
            self.RECOMMENDED: "Recomendado",
            self.TUNE_SETTINGS: "Pode rodar com ajustes",
            self.NOT_RECOMMENDED: "Provavelmente pesado",
        }
        return labels[self]


@dataclass(frozen=True)
class EmulatorRecommendation:
    """Recomendacao de um emulador para um perfil de hardware."""

    emulator_id: str
    tier: PerformanceTier
    status: RecommendationStatus
    suggested_graphics_profile: str
    reason: str
