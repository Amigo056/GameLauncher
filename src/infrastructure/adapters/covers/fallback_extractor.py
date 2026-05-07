"""Estrategia: procura cover ja existente no filesystem."""
import re
import unicodedata
from pathlib import Path
from typing import Optional, Tuple

from src.domain.entities.game import Cover
from src.application.ports.cover_extractor import CoverExtractor


class FallbackCoverExtractor(CoverExtractor):
    """
    Procura capas manuais/locais antes de qualquer extracao ou cache.

    Pastas suportadas:
    - assets/covers/manual/<emulator_id>
    - assets/covers/manual
    - assets/covers/<emulator_id>
    - assets/covers
    - pasta_da_rom/covers
    - pasta_da_rom
    """

    prefer_before_cache = True
    IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".webp")
    
    def __init__(self, covers_base_dir: Path = Path("assets/covers")):
        self.covers_dir = Path(covers_base_dir)
    
    @property
    def supported_extensions(self) -> list[str]:
        return list(self.IMAGE_EXTENSIONS)
    
    def can_extract(self, rom_path: Path) -> bool:
        return True  # Sempre tenta primeiro (chain of responsibility)
    
    def extract(
        self,
        rom_path: Path,
        game_id: str,
        output_dir: Path,
    ) -> Tuple[Optional[Cover], Optional[str]]:
        emulator_id = Path(output_dir).name.lower()

        for loc in self._locations(rom_path, output_dir, emulator_id):
            if not loc.exists():
                continue
            for candidate in self._candidate_names(rom_path, game_id, emulator_id):
                path = loc / candidate
                if path.is_file():
                    return Cover(local_path=path), None
        
        return None, None

    def _locations(
        self,
        rom_path: Path,
        output_dir: Path,
        emulator_id: str,
    ) -> list[Path]:
        return [
            self.covers_dir / "manual" / emulator_id,
            self.covers_dir / "manual",
            Path(output_dir),
            self.covers_dir / emulator_id,
            self.covers_dir,
            rom_path.parent / "covers",
            rom_path.parent,
        ]

    def _candidate_names(
        self,
        rom_path: Path,
        game_id: str,
        emulator_id: str,
    ) -> list[str]:
        original = rom_path.stem
        clean_name = self._sanitize_for_cover(original)
        slug = self._slugify(original)
        compact = clean_name.replace("_", "")

        stems = [
            game_id,
            slug,
            clean_name,
            compact,
            original,
            f"{emulator_id}_{game_id}",
            f"{emulator_id}_{slug}",
            f"{emulator_id}_{clean_name}",
        ]

        suffixes = ["", "_cover", "_front", "_box", "_pic", "_icon", "_title"]
        names: list[str] = []
        seen: set[str] = set()
        for stem in stems:
            if not stem:
                continue
            for suffix in suffixes:
                for extension in self.IMAGE_EXTENSIONS:
                    candidate = f"{stem}{suffix}{extension}"
                    key = candidate.lower()
                    if key not in seen:
                        seen.add(key)
                        names.append(candidate)
        return names

    def _sanitize_for_cover(self, name: str) -> str:
        clean = re.sub(r'\s*\([^)]*\)', '', name)
        clean = re.sub(r'\s*\[[^\]]*\]', '', clean)
        clean = re.sub(r'[^\w\s]', '', clean)
        return '_'.join(clean.strip().lower().split())

    def _slugify(self, name: str) -> str:
        normalized = unicodedata.normalize("NFKD", name)
        normalized = normalized.encode("ascii", "ignore").decode("ascii")
        normalized = re.sub(r"\s*[\(\[][^\)\]]*[\)\]]", "", normalized)
        normalized = re.sub(r"[^\w\s-]", "", normalized)
        normalized = re.sub(r"[\s_]+", "-", normalized.strip().lower())
        return normalized
