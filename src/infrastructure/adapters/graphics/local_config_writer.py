"""Writer local de perfis graficos para emuladores suportados."""

import logging
from pathlib import Path

from src.application.ports.graphics_config_writer import GraphicsConfigWriter
from src.domain.entities.emulator import Emulator
from src.domain.value_objects.graphics_profile import (
    GraphicsProfile,
    GraphicsProfileLevel,
)
from src.infrastructure.adapters.graphics.noop_config_writer import NoopGraphicsConfigWriter


logger = logging.getLogger(__name__)


class LocalGraphicsConfigWriter(GraphicsConfigWriter):
    """Aplica perfis graficos em ficheiros de config locais."""

    def __init__(self, fallback: GraphicsConfigWriter | None = None):
        self.fallback = fallback or NoopGraphicsConfigWriter()

    def apply(self, emulator: Emulator, profile: GraphicsProfile) -> None:
        """Aplica perfil no emulador suportado ou delega para fallback."""
        if emulator.id == "mgba":
            self._apply_mgba(emulator, profile.level)
            return
        if emulator.id == "melonds":
            self._apply_melonds(emulator, profile.level)
            return

        self.fallback.apply(emulator, profile)

    def _emulator_dir(self, emulator: Emulator) -> Path | None:
        if not emulator.executable_path:
            return None
        return emulator.executable_path.parent

    def _apply_mgba(self, emulator: Emulator, level: GraphicsProfileLevel) -> None:
        emu_dir = self._emulator_dir(emulator)
        if not emu_dir:
            return

        config_path = emu_dir / "config.ini"
        settings = self._mgba_settings(level)
        self._update_section_values(config_path, "ports.qt", settings)

    def _apply_melonds(self, emulator: Emulator, level: GraphicsProfileLevel) -> None:
        emu_dir = self._emulator_dir(emulator)
        if not emu_dir:
            return

        config_path = emu_dir / "melonDS.toml"
        settings_by_section = self._melonds_settings(level)
        for section, values in settings_by_section.items():
            self._update_section_values(config_path, section, values)

    def _mgba_settings(self, level: GraphicsProfileLevel) -> dict[str, str]:
        if level is GraphicsProfileLevel.PERFORMANCE:
            return {
                "fullscreen": "1",
                "frameskip": "1",
                "hwaccelVideo": "1",
                "videoSync": "0",
                "resampleVideo": "0",
                "interframeBlending": "0",
            }
        if level is GraphicsProfileLevel.QUALITY:
            return {
                "fullscreen": "1",
                "frameskip": "0",
                "hwaccelVideo": "1",
                "videoSync": "1",
                "resampleVideo": "1",
                "interframeBlending": "1",
                "lockAspectRatio": "1",
            }
        return {
            "fullscreen": "1",
            "frameskip": "0",
            "hwaccelVideo": "1",
            "videoSync": "0",
            "resampleVideo": "0",
            "interframeBlending": "1",
        }

    def _melonds_settings(
        self,
        level: GraphicsProfileLevel,
    ) -> dict[str, dict[str, str]]:
        if level is GraphicsProfileLevel.PERFORMANCE:
            return {
                "3D": {"Renderer": "0"},
                "3D.Soft": {"Threaded": "true"},
                "3D.GL": {"ScaleFactor": "1", "BetterPolygons": "false"},
                "Screen": {"UseGL": "false", "VSync": "false"},
            }
        if level is GraphicsProfileLevel.QUALITY:
            return {
                "3D": {"Renderer": "1"},
                "3D.Soft": {"Threaded": "true"},
                "3D.GL": {
                    "ScaleFactor": "2",
                    "BetterPolygons": "true",
                    "HiresCoordinates": "true",
                },
                "Screen": {"UseGL": "true", "VSync": "true"},
            }
        return {
            "3D": {"Renderer": "1"},
            "3D.Soft": {"Threaded": "true"},
            "3D.GL": {"ScaleFactor": "1", "BetterPolygons": "false"},
            "Screen": {"UseGL": "true", "VSync": "false"},
        }

    def _update_section_values(
        self,
        config_path: Path,
        section: str,
        values: dict[str, str],
    ) -> None:
        """Atualiza chaves simples em ficheiros INI/TOML preservando o resto."""
        if not config_path.exists():
            logger.debug("Config grafica nao encontrada: %s", config_path)
            return

        lines = config_path.read_text(encoding="utf-8").splitlines()
        output: list[str] = []
        in_section = False
        seen_keys: set[str] = set()
        section_found = False

        for line in lines:
            stripped = line.strip()
            is_section = stripped.startswith("[") and stripped.endswith("]")

            if is_section:
                if in_section:
                    for key, value in values.items():
                        if key not in seen_keys:
                            output.append(f"{key} = {value}" if config_path.suffix == ".toml" else f"{key}={value}")

                current = stripped[1:-1]
                in_section = current == section
                section_found = section_found or in_section
                if in_section:
                    seen_keys = set()
                output.append(line)
                continue

            if in_section and "=" in line and not stripped.startswith("#"):
                key = line.split("=", 1)[0].strip()
                if key in values:
                    seen_keys.add(key)
                    sep = " = " if config_path.suffix == ".toml" else "="
                    output.append(f"{key}{sep}{values[key]}")
                    continue

            output.append(line)

        if in_section:
            for key, value in values.items():
                if key not in seen_keys:
                    output.append(f"{key} = {value}" if config_path.suffix == ".toml" else f"{key}={value}")

        if not section_found:
            output.append("")
            output.append(f"[{section}]")
            for key, value in values.items():
                output.append(f"{key} = {value}" if config_path.suffix == ".toml" else f"{key}={value}")

        config_path.write_text("\n".join(output) + "\n", encoding="utf-8")
