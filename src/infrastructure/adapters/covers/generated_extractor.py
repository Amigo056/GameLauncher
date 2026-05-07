"""Fallback visual gerado para jogos sem capa real."""
import hashlib
import re
from pathlib import Path
from typing import Optional, Tuple

from PIL import Image, ImageDraw, ImageFont

from src.application.ports.cover_extractor import CoverExtractor
from src.domain.entities.game import Cover


class GeneratedCoverExtractor(CoverExtractor):
    """Gera uma capa simples e estavel quando nenhuma capa local/extrativa existe."""

    EMULATOR_LAYOUTS = {
        "melonds": {
            "size": (256, 256),
            "label": "Nintendo DS",
            "palette": ("#263238", "#4db6ac", "#f7f7f2"),
        },
        "mgba": {
            "size": (300, 200),
            "label": "Game Boy",
            "palette": ("#2f3a2f", "#9ccc65", "#f7f7f2"),
        },
        "mupen64plus": {
            "size": (280, 210),
            "label": "Nintendo 64",
            "palette": ("#2b2d42", "#ef476f", "#f7f7f2"),
        },
        "ppsspp": {
            "size": (320, 180),
            "label": "PSP",
            "palette": ("#1f2933", "#64b5f6", "#f7f7f2"),
        },
    }
    DEFAULT_LAYOUT = {
        "size": (280, 210),
        "label": "Retro",
        "palette": ("#272727", "#f9a03f", "#f7f7f2"),
    }

    @property
    def supported_extensions(self) -> list[str]:
        return ["*"]

    def can_extract(self, rom_path: Path) -> bool:
        return rom_path.suffix.lower() in {
            ".nds",
            ".gba",
            ".gb",
            ".gbc",
            ".z64",
            ".n64",
            ".v64",
            ".iso",
            ".cso",
            ".pbp",
            ".zip",
        }

    def extract(
        self,
        rom_path: Path,
        game_id: str,
        output_dir: Path,
    ) -> Tuple[Optional[Cover], Optional[str]]:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        cover_path = output_dir / f"{game_id}_generated.png"
        title = self._clean_title(rom_path.stem)

        rom_mtime = rom_path.stat().st_mtime if rom_path.exists() else 0
        if not cover_path.exists() or cover_path.stat().st_mtime < rom_mtime:
            emulator_id = output_dir.name.lower()
            image = self._create_cover(title, emulator_id, game_id)
            image.save(cover_path, "PNG")

        return Cover(local_path=cover_path), title

    def _create_cover(self, title: str, emulator_id: str, game_id: str) -> Image.Image:
        layout = self.EMULATOR_LAYOUTS.get(emulator_id, self.DEFAULT_LAYOUT)
        width, height = layout["size"]
        base, accent, text = self._palette_for_game(
            game_id,
            layout["palette"],
        )

        image = Image.new("RGBA", (width, height), base)
        draw = ImageDraw.Draw(image)

        draw.rectangle((0, 0, width, height), fill=base)
        draw.rectangle((0, 0, width, 10), fill=accent)
        draw.rectangle((0, height - 10, width, height), fill=accent)

        badge_size = min(width, height) // 4
        draw.rounded_rectangle(
            (18, 22, 18 + badge_size, 22 + badge_size),
            radius=10,
            fill=accent,
        )
        draw.text(
            (18 + badge_size / 2, 22 + badge_size / 2),
            self._initials(title),
            fill=text,
            font=self._font(28, bold=True),
            anchor="mm",
        )

        draw.text(
            (18, height - 34),
            layout["label"],
            fill=accent,
            font=self._font(15, bold=True),
        )

        title_font = self._font(24, bold=True)
        lines = self._wrap_text(title, title_font, width - 40, max_lines=4)
        text_height = len(lines) * 30
        y = max(76, (height - text_height) // 2)

        for line in lines:
            draw.text((18, y), line, fill=text, font=title_font)
            y += 30

        return image

    def _palette_for_game(
        self,
        game_id: str,
        palette: tuple[str, str, str],
    ) -> tuple[str, str, str]:
        base, accent, text = palette
        digest = hashlib.sha1(game_id.encode("utf-8")).hexdigest()
        variants = [accent, "#ffd166", "#06d6a0", "#ef476f", "#64b5f6"]
        return base, variants[int(digest[:2], 16) % len(variants)], text

    def _clean_title(self, title: str) -> str:
        clean = re.sub(r"\s*[\(\[][^\)\]]*[\)\]]", "", title)
        clean = re.sub(r"[_\.]+", " ", clean)
        clean = " ".join(clean.split())
        return clean or title

    def _initials(self, title: str) -> str:
        words = [word for word in re.split(r"\W+", title) if word]
        if not words:
            return "GL"
        return "".join(word[0].upper() for word in words[:2])

    def _wrap_text(
        self,
        text: str,
        font: ImageFont.ImageFont,
        max_width: int,
        max_lines: int,
    ) -> list[str]:
        draw = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
        words = text.split()
        lines: list[str] = []
        current = ""

        for word in words:
            candidate = f"{current} {word}".strip()
            if draw.textlength(candidate, font=font) <= max_width:
                current = candidate
                continue

            if current:
                lines.append(current)
            current = word

            if len(lines) >= max_lines:
                break

        if current and len(lines) < max_lines:
            lines.append(current)

        if len(lines) == max_lines and len(" ".join(words)) > len(" ".join(lines)):
            lines[-1] = lines[-1].rstrip(".") + "..."

        return lines or [text]

    def _font(self, size: int, bold: bool = False) -> ImageFont.ImageFont:
        candidates = [
            "segoeuib.ttf" if bold else "segoeui.ttf",
            "arialbd.ttf" if bold else "arial.ttf",
        ]
        for candidate in candidates:
            try:
                return ImageFont.truetype(candidate, size)
            except OSError:
                continue
        return ImageFont.load_default()
