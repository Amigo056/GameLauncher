"""Testes para SettingsService."""

from src.application.services.settings_service import SettingsService
from src.domain.value_objects.graphics_profile import GraphicsProfileLevel


def test_graphics_profile_defaults_to_balanced(tmp_path):
    service = SettingsService(config_path=tmp_path / "settings.json")

    assert service.get_graphics_profile("mgba") is GraphicsProfileLevel.BALANCED


def test_save_and_load_graphics_profile(tmp_path):
    service = SettingsService(config_path=tmp_path / "settings.json")

    service.save_graphics_profile("mgba", GraphicsProfileLevel.PERFORMANCE)

    reloaded = SettingsService(config_path=tmp_path / "settings.json")
    assert reloaded.get_graphics_profile("mgba") is GraphicsProfileLevel.PERFORMANCE


def test_invalid_graphics_profile_falls_back_to_default(tmp_path):
    settings_path = tmp_path / "settings.json"
    settings_path.write_text(
        '{"graphics_profiles": {"mgba": "turbo-potato"}}',
        encoding="utf-8",
    )
    service = SettingsService(config_path=settings_path)

    assert service.get_graphics_profile("mgba") is GraphicsProfileLevel.BALANCED


def test_favorite_games_can_be_toggled(tmp_path):
    service = SettingsService(config_path=tmp_path / "settings.json")

    assert service.is_favorite_game("mgba", "pokemon-fire-red") is False

    assert service.toggle_favorite_game("mgba", "pokemon-fire-red") is True
    assert service.is_favorite_game("mgba", "pokemon-fire-red") is True
    assert service.get_favorite_games("mgba") == {"pokemon-fire-red"}

    reloaded = SettingsService(config_path=tmp_path / "settings.json")
    assert reloaded.is_favorite_game("mgba", "pokemon-fire-red") is True

    assert reloaded.toggle_favorite_game("mgba", "pokemon-fire-red") is False
    assert reloaded.get_favorite_games("mgba") == set()


def test_invalid_favorites_shape_falls_back_to_empty(tmp_path):
    settings_path = tmp_path / "settings.json"
    settings_path.write_text(
        '{"favorite_games": ["not", "a", "dict"]}',
        encoding="utf-8",
    )
    service = SettingsService(config_path=settings_path)

    assert service.get_favorite_games("mgba") == set()
