"""Porta para extratores/provedores de capas."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Tuple

from src.domain.entities.game import Cover


class CoverExtractor(ABC):
    """Contrato para estrategias de obtencao de capas."""

    @property
    @abstractmethod
    def supported_extensions(self) -> list[str]:
        """Extensoes suportadas pelo extrator."""
        pass

    @abstractmethod
    def can_extract(self, rom_path: Path) -> bool:
        """Verifica se o extrator consegue tratar esta ROM."""
        pass

    @abstractmethod
    def extract(
        self,
        rom_path: Path,
        game_id: str,
        output_dir: Path,
    ) -> Tuple[Optional[Cover], Optional[str]]:
        """Retorna cover e titulo real, quando disponiveis."""
        pass
