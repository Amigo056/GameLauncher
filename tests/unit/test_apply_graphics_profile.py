"""Testes para ApplyGraphicsProfileUseCase."""

from pathlib import Path

import pytest

from src.application.use_cases.apply_graphics_profile import ApplyGraphicsProfileUseCase
from src.domain.entities.emulator import Emulator, Platform
from src.domain.value_objects.graphics_profile import (
    GraphicsProfile,
    GraphicsProfileLevel,
)


class MockGraphicsWriter:
    def __init__(self):
        self.calls = []

    def apply(self, emulator, profile):
        self.calls.append((emulator, profile))


def test_apply_graphics_profile_calls_writer():
    writer = MockGraphicsWriter()
    use_case = ApplyGraphicsProfileUseCase(graphics_writer=writer)
    emulator = Emulator(
        id="mgba",
        name="mGBA",
        platform=Platform.GAME_BOY_ADVANCE,
        executable_path=Path("mgba.exe"),
    )
    profile = GraphicsProfile(
        emulator_id="mgba",
        level=GraphicsProfileLevel.BALANCED,
    )

    use_case.execute(emulator, profile)

    assert writer.calls == [(emulator, profile)]


def test_apply_graphics_profile_rejects_wrong_emulator():
    writer = MockGraphicsWriter()
    use_case = ApplyGraphicsProfileUseCase(graphics_writer=writer)
    emulator = Emulator(
        id="mgba",
        name="mGBA",
        platform=Platform.GAME_BOY_ADVANCE,
        executable_path=Path("mgba.exe"),
    )
    profile = GraphicsProfile(
        emulator_id="melonds",
        level=GraphicsProfileLevel.BALANCED,
    )

    with pytest.raises(ValueError):
        use_case.execute(emulator, profile)

    assert writer.calls == []
