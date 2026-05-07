"""Carregador de configurações de ficheiros JSON/YAML."""
import json
from pathlib import Path
from typing import Any, Optional


class ConfigLoader:
    """
    Carrega ficheiros de configuração.
    
    Suporta JSON nativo. YAML pode ser adicionado futuro.
    """

    @staticmethod
    def load_json(path: Path) -> Optional[dict[str, Any]]:
        """Carrega ficheiro JSON. Retorna None se não existir ou inválido."""
        if not path.exists():
            return None
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return None

    @staticmethod
    def save_json(path: Path, data: dict[str, Any]) -> bool:
        """Guarda dados em JSON. Retorna True se sucesso."""
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except OSError:
            return False
'''

config_mapper_py = '''"""Mapper de configurações: converte dicts → objetos de domínio."""
from pathlib import Path
from typing import Any

from src.domain.entities.emulator import Emulator, Platform, EmulatorConfig


class ConfigMapper:
    """
    Converte dicionários de configuração em entidades de domínio.
    
    Responsabilidade única: transformação de dados brutos → objetos tipados.
    """

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
            executable_path=None,  # Resolvido posteriormente
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
        """Converte entidade Emulator em dict (para serialização)."""
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
'''

config_validator_py = '''"""Validador de configurações."""
from pathlib import Path
from typing import Any, List, Tuple


class ConfigValidator:
    """
    Valida configurações antes de serem aplicadas.
    
    Retorna lista de erros (vazia = válido).
    """

    @staticmethod
    def validate_emulator_config(data: dict[str, Any]) -> List[str]:
        """Valida configuração de um emulador."""
        errors: List[str] = []

        required_fields = ['id', 'name', 'rom_extensions', 'roms_folder']
        for field in required_fields:
            if field not in data or not data[field]:
                errors.append(f"Campo obrigatório ausente: '{field}'")

        if 'id' in data and not isinstance(data['id'], str):
            errors.append("'id' deve ser uma string")

        if 'rom_extensions' in data:
            if not isinstance(data['rom_extensions'], list):
                errors.append("'rom_extensions' deve ser uma lista")
            elif not data['rom_extensions']:
                errors.append("'rom_extensions' não pode estar vazio")

        if 'roms_folder' in data:
            folder = Path(data['roms_folder'])
            if '..' in str(folder):
                errors.append("'roms_folder' não pode conter '..' (path traversal)")

        return errors

    @staticmethod
    def validate_emulators_file(data: dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Valida ficheiro emulators.json completo.
        
        Returns:
            (is_valid, list_of_errors)
        """
        errors: List[str] = []

        if 'emulators' not in data:
            return False, ["Chave 'emulators' não encontrada no ficheiro"]

        if not isinstance(data['emulators'], list):
            return False, ["'emulators' deve ser uma lista"]

        if not data['emulators']:
            errors.append("Lista de emuladores está vazia")

        seen_ids = set()
        for idx, emu in enumerate(data['emulators']):
            emu_errors = ConfigValidator.validate_emulator_config(emu)
            for err in emu_errors:
                errors.append(f"Emulador [{idx}] ({emu.get('id', '?')}): {err}")

            emu_id = emu.get('id')
            if emu_id in seen_ids:
                errors.append(f"ID duplicado: '{emu_id}'")
            seen_ids.add(emu_id)

        return len(errors) == 0, errors