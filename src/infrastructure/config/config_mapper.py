"""Mapper de configurações: converte dicts → objetos de domínio."""
from pathlib import Path
from typing import Any

from src.domain.entities.emulator import Emulator, Platform, EmulatorConfig


class ConfigMapper:
    """Converte dicionários de configuração em entidades de domínio."""

    @staticmethod
    def to_emulator(data: dict[str, Any]) -> Emulator:
        """Converte dict de config em entidade Emulator."""
        platform_map = {
            'nintendo-ds': Platform.NINTENDO_DS,
            'playstation-portable': Platform.PLAYSTATION_PORTABLE,
            'nintendo-64': Platform.NINTENDO_64,
            'game-boy-advance': Platform.GAME_BOY_ADVANCE,
        }
        return Emulator(
            id=data['id'],
            name=data['name'],
            platform=platform_map.get(data.get('platform', ''), Platform.UNKNOWN),
            icon_path=Path(data['icon']) if data.get('icon') else None,
            executable_path=None,
            executable_names=data.get('executable_names', []),
            default_install_paths=[Path(p) for p in data.get('default_install_paths', [])],
            supported_extensions=data.get('rom_extensions', []),
            roms_folder=Path(data.get('roms_folder', 'roms')),
            launch_args_template=data.get('launch_args', '"{rom_path}"'),
            config=EmulatorConfig(
                safe_settings=data.get('safe_settings', {}),
                config_file_path=Path(data['config_file']) if data.get('config_file') else None,
            ),
        )

    @staticmethod
    def from_emulator(emulator: Emulator) -> dict[str, Any]:
        """Converte entidade Emulator em dict."""
        return {
            'id': emulator.id,
            'name': emulator.name,
            'platform': emulator.platform.value,
            'icon': str(emulator.icon_path) if emulator.icon_path else None,
            'executable_names': emulator.executable_names,
            'default_install_paths': [str(p) for p in emulator.default_install_paths],
            'rom_extensions': emulator.supported_extensions,
            'roms_folder': str(emulator.roms_folder),
            'launch_args': emulator.launch_args_template,
        }