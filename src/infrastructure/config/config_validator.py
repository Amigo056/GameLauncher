"""Validador de configurações."""
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