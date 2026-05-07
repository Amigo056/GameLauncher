"""Servico para gerir pastas de capas manuais."""
from pathlib import Path


class ManualCoverService:
    """Resolve e cria diretorios onde o utilizador pode colocar capas manuais."""

    DEFAULT_BASE_DIR = Path("assets/covers/manual")

    def __init__(self, base_dir: Path = DEFAULT_BASE_DIR):
        self.base_dir = Path(base_dir)

    def emulator_dir(self, emulator_id: str) -> Path:
        """Retorna a pasta de capas manuais de um emulador."""
        return self.base_dir / emulator_id.lower()

    def ensure_emulator_dir(self, emulator_id: str) -> Path:
        """Cria e retorna a pasta de capas manuais de um emulador."""
        path = self.emulator_dir(emulator_id)
        path.mkdir(parents=True, exist_ok=True)
        return path
