"""Caso de uso: recomendar emuladores com base no hardware."""

from dataclasses import dataclass

from src.domain.value_objects.emulator_recommendation import (
    EmulatorRecommendation,
    PerformanceTier,
    RecommendationStatus,
)
from src.domain.value_objects.graphics_profile import GraphicsProfileLevel
from src.domain.value_objects.hardware_profile import HardwareProfile


@dataclass
class RecommendEmulatorsUseCase:
    """Gera recomendacoes iniciais por tier de desempenho."""

    emulator_tiers: dict[str, PerformanceTier]

    def execute(self, hardware: HardwareProfile) -> list[EmulatorRecommendation]:
        """Retorna recomendacoes para todos os emuladores conhecidos."""
        capability_score = self._score_hardware(hardware)
        recommendations = []

        for emulator_id, tier in self.emulator_tiers.items():
            status = self._status_for(capability_score, tier)
            recommendations.append(
                EmulatorRecommendation(
                    emulator_id=emulator_id,
                    tier=tier,
                    status=status,
                    suggested_graphics_profile=self._graphics_profile_for(status),
                    reason=self._reason_for(hardware, tier, status),
                )
            )

        return recommendations

    def _score_hardware(self, hardware: HardwareProfile) -> int:
        """Score simples e conservador para recomendacoes iniciais."""
        score = 0

        if hardware.cpu_cores >= 8:
            score += 2
        elif hardware.cpu_cores >= 4:
            score += 1

        if hardware.ram_gb >= 16:
            score += 2
        elif hardware.ram_gb >= 8:
            score += 1

        if hardware.gpu_name and hardware.gpu_name != "Unknown":
            score += 1

        return score

    def _status_for(
        self,
        score: int,
        tier: PerformanceTier,
    ) -> RecommendationStatus:
        required = {
            PerformanceTier.VERY_LIGHT: 0,
            PerformanceTier.LIGHT: 1,
            PerformanceTier.MEDIUM: 2,
            PerformanceTier.HEAVY: 4,
            PerformanceTier.VERY_HEAVY: 5,
        }[tier]

        if score >= required:
            return RecommendationStatus.RECOMMENDED
        if score + 1 >= required:
            return RecommendationStatus.TUNE_SETTINGS
        return RecommendationStatus.NOT_RECOMMENDED

    def _graphics_profile_for(self, status: RecommendationStatus) -> str:
        if status is RecommendationStatus.RECOMMENDED:
            return GraphicsProfileLevel.BALANCED.value
        if status is RecommendationStatus.TUNE_SETTINGS:
            return GraphicsProfileLevel.PERFORMANCE.value
        return GraphicsProfileLevel.PERFORMANCE.value

    def _reason_for(
        self,
        hardware: HardwareProfile,
        tier: PerformanceTier,
        status: RecommendationStatus,
    ) -> str:
        return (
            f"{tier.label}: {status.label}. "
            f"Baseado em {hardware.cpu_cores} cores e {hardware.ram_gb:.1f} GB RAM."
        )
