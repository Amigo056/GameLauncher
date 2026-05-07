"""Smoke tests para imports de apresentacao."""


def test_game_card_imports_without_evaluated_callable_error():
    from src.presentation.widgets.game_card import GameCard

    assert GameCard is not None


def test_app_navigator_imports_with_detail_dialog():
    from src.presentation.app_navigator import AppNavigator

    assert AppNavigator is not None
