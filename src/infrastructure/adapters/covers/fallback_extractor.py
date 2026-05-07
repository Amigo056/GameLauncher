"""Estratégia: procura cover já existente no filesystem."""
import re
from pathlib import Path
from typing import Optional, Tuple

from src.domain.entities.game import Cover
from src.application.ports.cover_extractor import CoverExtractor


class FallbackCoverExtractor(CoverExtractor):
    """
    Procura covers em assets/covers/ e na pasta do ROM.
    Não extrai nada — só reutiliza o que já existe.
    """
    
    def __init__(self, covers_base_dir: Path = Path("assets/covers")):
        self.covers_dir = Path(covers_base_dir)
    
    @property
    def supported_extensions(self) -> list[str]:
        return [".png", ".jpg", ".jpeg"]  # Qualquer ROM pode ter cover local
    
    def can_extract(self, rom_path: Path) -> bool:
        return True  # Sempre tenta primeiro (chain of responsibility)
    
    def extract(self, rom_path: Path, game_id: str, output_dir: Path) -> Tuple[Optional[Cover], Optional[str]]:
        clean_name = self._sanitize_for_cover(rom_path.stem)
        
        candidates = [
            f"{game_id}.png",
            f"{game_id}_pic.png",    # ← falta isto
            f"{game_id}_icon.png",
            f"{rom_path.stem}.png",
            f"{rom_path.stem}_pic.png",
            f"{rom_path.stem}_icon.png",
            f"ppsspp_{clean_name}.png",
            f"melonds_{clean_name}.png",
            f"mupen64plus_{clean_name}.png",
        ]
        
        locations = [
            output_dir,
            self.covers_dir / rom_path.parent.name.lower(),  # psp, nds, n64
            self.covers_dir,
            rom_path.parent,
        ]
        
        for loc in locations:
            if not loc.exists():
                continue
            for candidate in candidates:
                path = loc / candidate
                if path.exists():
                    return Cover(local_path=path), None
        
        return None, None
    
    def _sanitize_for_cover(self, name: str) -> str:
        clean = re.sub(r'\s*\([^)]*\)', '', name)
        clean = re.sub(r'[^\w\s]', '', clean)
        return '_'.join(clean.strip().lower().split())
