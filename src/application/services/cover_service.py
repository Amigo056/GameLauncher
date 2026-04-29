"""Serviço de aplicação: coordena extratores de covers."""
from pathlib import Path
from typing import Optional, Tuple

from src.domain.entities.game import Cover
from src.domain.services.cover_extractor import CoverExtractor


class CoverService:
    """
    Coordena múltiplos extratores de cover.
    Usa Chain of Responsibility: tenta cada extrator até um funcionar.
    """
    
    def __init__(self, extractors: list[CoverExtractor], output_dir: Path):
        self.extractors = extractors  # Ordenados por prioridade
        self.output_dir = Path(output_dir)
    
    def resolve_cover(self, rom_path: Path, game_id: str, emulator_id: str) -> Tuple[Optional[Cover], Optional[str]]:
        """
        Tenta extrair/obter cover e título real.
        Retorna: (Cover, título_real)
        """
        # Pasta específica do emulador
        emu_output = self.output_dir / emulator_id.lower()
        
        for extractor in self.extractors:
            if extractor.can_extract(rom_path):
                cover, title = extractor.extract(rom_path, game_id, emu_output)
                if cover and cover.is_local:
                    return cover, title
        
        return None, None