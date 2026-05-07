"""Registry inicial de perfis graficos por emulador."""

from src.domain.value_objects.graphics_profile import (
    GraphicsProfile,
    GraphicsProfileLevel,
)


class GraphicsProfileRegistry:
    """Fornece perfis graficos padrao enquanto nao ha storage dedicado."""

    def get_profiles(self, emulator_id: str) -> list[GraphicsProfile]:
        """Retorna os tres perfis padrao para um emulador."""
        return [
            GraphicsProfile(
                emulator_id=emulator_id,
                level=GraphicsProfileLevel.PERFORMANCE,
                settings=self._default_settings(emulator_id, GraphicsProfileLevel.PERFORMANCE),
                description="Prioriza FPS, estabilidade e menor uso de recursos.",
            ),
            GraphicsProfile(
                emulator_id=emulator_id,
                level=GraphicsProfileLevel.BALANCED,
                settings=self._default_settings(emulator_id, GraphicsProfileLevel.BALANCED),
                description="Equilibrio entre imagem limpa e desempenho.",
            ),
            GraphicsProfile(
                emulator_id=emulator_id,
                level=GraphicsProfileLevel.QUALITY,
                settings=self._default_settings(emulator_id, GraphicsProfileLevel.QUALITY),
                description="Prioriza resolucao, filtros e qualidade visual.",
            ),
        ]

    def get_profile(
        self,
        emulator_id: str,
        level: GraphicsProfileLevel,
    ) -> GraphicsProfile:
        """Retorna um perfil especifico."""
        for profile in self.get_profiles(emulator_id):
            if profile.level is level:
                return profile
        raise ValueError(f"Perfil grafico invalido: {emulator_id}/{level.value}")

    def _default_settings(
        self,
        emulator_id: str,
        level: GraphicsProfileLevel,
    ) -> dict[str, object]:
        """Settings neutras para arrancar a arquitetura."""
        common = {
            "fullscreen": True,
            "profile_level": level.value,
        }

        if emulator_id == "ppsspp":
            return common | self._ppsspp_settings(level)
        if emulator_id == "mupen64plus":
            return common | self._mupen64plus_settings(level)
        if emulator_id == "mgba":
            return common | self._mgba_settings(level)
        if emulator_id == "melonds":
            return common | self._melonds_settings(level)

        return common

    def _ppsspp_settings(self, level: GraphicsProfileLevel) -> dict[str, object]:
        if level is GraphicsProfileLevel.PERFORMANCE:
            return {"internal_resolution": "1x", "frameskip": "auto", "texture_scaling": False}
        if level is GraphicsProfileLevel.QUALITY:
            return {"internal_resolution": "3x", "frameskip": "off", "texture_scaling": True}
        return {"internal_resolution": "2x", "frameskip": "off", "texture_scaling": False}

    def _mupen64plus_settings(self, level: GraphicsProfileLevel) -> dict[str, object]:
        if level is GraphicsProfileLevel.PERFORMANCE:
            return {"resolution_scale": "native", "vsync": False}
        if level is GraphicsProfileLevel.QUALITY:
            return {"resolution_scale": "2x", "vsync": True}
        return {"resolution_scale": "display", "vsync": True}

    def _mgba_settings(self, level: GraphicsProfileLevel) -> dict[str, object]:
        if level is GraphicsProfileLevel.PERFORMANCE:
            return {"video_filter": "nearest", "frame_blending": False}
        if level is GraphicsProfileLevel.QUALITY:
            return {"video_filter": "linear", "frame_blending": True}
        return {"video_filter": "nearest", "frame_blending": True}

    def _melonds_settings(self, level: GraphicsProfileLevel) -> dict[str, object]:
        if level is GraphicsProfileLevel.PERFORMANCE:
            return {"renderer": "software", "internal_resolution": "native"}
        if level is GraphicsProfileLevel.QUALITY:
            return {"renderer": "opengl", "internal_resolution": "2x"}
        return {"renderer": "opengl", "internal_resolution": "native"}
