"""Serviço de domínio: extração de covers. Define o contrato."""
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Tuple

from src.domain.entities.game import Cover


class CoverExtractor(ABC):
    """
    Contrato para extratores de cover.
    Cada plataforma implementa a sua estratégia.
    """
    
    @property
    @abstractmethod
    def supported_extensions(self) -> list[str]:
        """Extensões que este extrator suporta."""
        pass
    
    @abstractmethod
    def can_extract(self, rom_path: Path) -> bool:
        """Verifica se consegue extrair cover desta ROM."""
        pass
    
    @abstractmethod
    def extract(self, rom_path: Path, game_id: str, output_dir: Path) -> Tuple[Optional[Cover], Optional[str]]:
        """
        Extrai cover e título real.
        Retorna: (Cover, título_real_ou_None)
        """
        pass