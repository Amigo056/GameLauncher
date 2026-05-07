"""Serviço de aplicação: coordena extratores de covers."""
from pathlib import Path
from typing import Optional, Tuple

from src.infrastructure.cache.cover_cache import CoverCache
from src.domain.entities.game import Cover
from src.application.ports.cover_extractor import CoverExtractor


class CoverService:
    """
    Coordena múltiplos extratores de cover.
    Usa Chain of Responsibility: tenta cada extrator até um funcionar.
    """
    
    def __init__(
        self,
        extractors: list[CoverExtractor],
        output_dir: Path,
        cover_cache: Optional[CoverCache] = None,
    ):
        self.extractors = extractors
        self.output_dir = Path(output_dir)
        self.cover_cache = cover_cache
    
    def resolve_cover(
        self, 
        rom_path: Path, 
        game_id: str, 
        emulator_id: str
    ): 
        """
        Tenta extrair/obter cover e título real.
        Retorna: (Cover, título_real)
        """
        # Pasta específica do emulador
        emu_output = self.output_dir / emulator_id.lower()
        
        if self.cover_cache:
            # Calcular checksum rápido (ou usar modificação do ficheiro)
            rom_checksum = self._quick_checksum(rom_path)
            cached_cover = self.cover_cache.get(game_id, emulator_id, rom_checksum)
            if cached_cover:
                return cached_cover, None  # Título não está em cache
        
        # Chain of responsibility (extratores nativos)
        for extractor in self.extractors:
            if extractor.can_extract(rom_path):
                cover, title = extractor.extract(rom_path, game_id, emu_output)
                if cover and cover.is_local:
                    if self.cover_cache:
                        self.cover_cache.put(game_id, emulator_id, cover, rom_checksum)
                    return cover, title
        
        return None, None
    
    def _quick_checksum(self, rom_path: Path) -> str:
        """Checksum rápido para invalidação — usa mtime + size em vez de MD5 completo."""
        stat = rom_path.stat()
        return f"{stat.st_mtime}:{stat.st_size}"
