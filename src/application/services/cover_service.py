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
        emu_output = self.output_dir / emulator_id.lower()
        rom_checksum = self._quick_checksum(rom_path) if self.cover_cache else ""
        resolved_title: Optional[str] = None

        pre_cache_extractors = [
            extractor
            for extractor in self.extractors
            if getattr(extractor, "prefer_before_cache", False)
        ]

        for extractor in pre_cache_extractors:
            if not extractor.can_extract(rom_path):
                continue

            cover, title = extractor.extract(rom_path, game_id, emu_output)
            if title and not resolved_title:
                resolved_title = title
            if cover and cover.is_local:
                if self.cover_cache:
                    self.cover_cache.put(game_id, emulator_id, cover, rom_checksum)
                return cover, resolved_title
        
        if self.cover_cache:
            cached_cover = self.cover_cache.get(game_id, emulator_id, rom_checksum)
            if cached_cover:
                return cached_cover, None

        for extractor in self.extractors:
            if extractor in pre_cache_extractors:
                continue
            if extractor.can_extract(rom_path):
                cover, title = extractor.extract(rom_path, game_id, emu_output)
                if title and not resolved_title:
                    resolved_title = title
                if cover and cover.is_local:
                    if self.cover_cache:
                        self.cover_cache.put(game_id, emulator_id, cover, rom_checksum)
                    return cover, resolved_title or title
        
        return None, resolved_title
    
    def _quick_checksum(self, rom_path: Path) -> str:
        """Checksum rápido para invalidação — usa mtime + size em vez de MD5 completo."""
        stat = rom_path.stat()
        return f"{stat.st_mtime}:{stat.st_size}"
