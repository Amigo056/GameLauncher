"""Testes para estrategias de fallback de capas."""
from pathlib import Path

from PIL import Image

from src.infrastructure.adapters.covers.fallback_extractor import FallbackCoverExtractor
from src.infrastructure.adapters.covers.generated_extractor import GeneratedCoverExtractor
from src.infrastructure.adapters.covers.nds_extractor import NDSCoverExtractor


def test_fallback_finds_manual_cover_by_game_id(tmp_path):
    covers_dir = tmp_path / "assets" / "covers"
    manual_dir = covers_dir / "manual" / "mgba"
    manual_dir.mkdir(parents=True)
    cover_path = manual_dir / "pokemon-fire-red.png"
    cover_path.write_bytes(b"fake-image")

    extractor = FallbackCoverExtractor(covers_base_dir=covers_dir)
    cover, title = extractor.extract(
        rom_path=tmp_path / "roms" / "Pokemon Fire Red (USA).gba",
        game_id="pokemon-fire-red",
        output_dir=covers_dir / "mgba",
    )

    assert cover is not None
    assert cover.local_path == cover_path
    assert title is None


def test_fallback_finds_manual_cover_by_clean_rom_name(tmp_path):
    covers_dir = tmp_path / "assets" / "covers"
    manual_dir = covers_dir / "manual"
    manual_dir.mkdir(parents=True)
    cover_path = manual_dir / "mario_kart_ds_cover.jpg"
    cover_path.write_bytes(b"fake-image")

    extractor = FallbackCoverExtractor(covers_base_dir=covers_dir)
    cover, _ = extractor.extract(
        rom_path=tmp_path / "roms" / "Mario Kart DS [Europe].nds",
        game_id="mario-kart-ds-europe",
        output_dir=covers_dir / "melonds",
    )

    assert cover is not None
    assert cover.local_path == cover_path


def test_generated_cover_creates_image_and_clean_title(tmp_path):
    rom_path = tmp_path / "Pokemon Emerald (USA).gba"
    rom_path.write_bytes(b"rom")
    output_dir = tmp_path / "covers" / "mgba"

    cover, title = GeneratedCoverExtractor().extract(
        rom_path=rom_path,
        game_id="pokemon-emerald-usa",
        output_dir=output_dir,
    )

    assert title == "Pokemon Emerald"
    assert cover is not None
    assert cover.local_path.exists()

    image = Image.open(cover.local_path)
    assert image.size == (300, 200)


def test_nds_icon_usefulness_rejects_transparent_icon():
    extractor = NDSCoverExtractor()
    icon = Image.new("RGBA", (128, 128), (0, 0, 0, 0))

    assert extractor._is_icon_useful(icon) is False


def test_nds_icon_usefulness_accepts_visible_icon():
    extractor = NDSCoverExtractor()
    icon = Image.new("RGBA", (128, 128), (0, 0, 0, 0))
    for x in range(20, 80):
        for y in range(20, 80):
            icon.putpixel((x, y), (255, 0, 0, 255))

    assert extractor._is_icon_useful(icon) is True
