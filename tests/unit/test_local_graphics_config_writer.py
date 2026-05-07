"""Testes para LocalGraphicsConfigWriter."""

from pathlib import Path

from src.domain.entities.emulator import Emulator, Platform
from src.domain.value_objects.graphics_profile import (
    GraphicsProfile,
    GraphicsProfileLevel,
)
from src.infrastructure.adapters.graphics.local_config_writer import LocalGraphicsConfigWriter


def test_mgba_performance_profile_updates_config(tmp_path):
    emu_dir = tmp_path / "mGBA"
    emu_dir.mkdir()
    (emu_dir / "mGBA.exe").write_text("", encoding="utf-8")
    config = emu_dir / "config.ini"
    config.write_text(
        "[ports.qt]\nfullscreen=0\nframeskip=0\nvideoSync=1\nuntouched=yes\n",
        encoding="utf-8",
    )
    emulator = Emulator(
        id="mgba",
        name="mGBA",
        platform=Platform.GAME_BOY_ADVANCE,
        executable_path=emu_dir / "mGBA.exe",
    )
    profile = GraphicsProfile("mgba", GraphicsProfileLevel.PERFORMANCE)

    LocalGraphicsConfigWriter().apply(emulator, profile)

    content = config.read_text(encoding="utf-8")
    assert "fullscreen=1" in content
    assert "frameskip=1" in content
    assert "videoSync=0" in content
    assert "untouched=yes" in content


def test_melonds_quality_profile_updates_toml(tmp_path):
    emu_dir = tmp_path / "melonDS"
    emu_dir.mkdir()
    (emu_dir / "melonDS.exe").write_text("", encoding="utf-8")
    config = emu_dir / "melonDS.toml"
    config.write_text(
        "[3D]\nRenderer = 0\n\n[3D.GL]\nScaleFactor = 1\n\n[Screen]\nUseGL = false\nVSync = false\n",
        encoding="utf-8",
    )
    emulator = Emulator(
        id="melonds",
        name="melonDS",
        platform=Platform.NINTENDO_DS,
        executable_path=emu_dir / "melonDS.exe",
    )
    profile = GraphicsProfile("melonds", GraphicsProfileLevel.QUALITY)

    LocalGraphicsConfigWriter().apply(emulator, profile)

    content = config.read_text(encoding="utf-8")
    assert "Renderer = 1" in content
    assert "ScaleFactor = 2" in content
    assert "BetterPolygons = true" in content
    assert "UseGL = true" in content
    assert "VSync = true" in content
