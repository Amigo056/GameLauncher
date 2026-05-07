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
