"""Testes para SessionTracker e tracking de tempo de jogo."""
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock
import time

import pytest

from src.application.events import EventBus, GameLaunched, GameClosed
from src.domain.entities.play_session import PlaySession
from src.application.tracking.session_tracker import SessionTracker, _ActiveSession


class MockSessionRepository:
    def __init__(self):
        self.sessions: list[PlaySession] = []

    def save(self, session: PlaySession) -> None:
        self.sessions.append(session)

    def get_by_game(self, game_id: str) -> list[PlaySession]:
        return [s for s in self.sessions if s.game_id == game_id]

    def get_total_playtime(self, game_id: str) -> int:
        return sum(s.duration_seconds or 0 for s in self.sessions if s.game_id == game_id)

    def get_recent_sessions(self, limit: int = 10) -> list[PlaySession]:
        return sorted(self.sessions, key=lambda s: s.start_time, reverse=True)[:limit]

    def get_most_played(self, limit: int = 10) -> list[tuple[str, int]]:
        from collections import defaultdict
        totals = defaultdict(int)
        for s in self.sessions:
            if s.duration_seconds:
                totals[s.game_id] += s.duration_seconds
        return sorted(totals.items(), key=lambda x: x[1], reverse=True)[:limit]


class TestSessionTracker:
    @pytest.fixture
    def event_bus(self):
        return EventBus()

    @pytest.fixture
    def mock_repo(self):
        return MockSessionRepository()

    @pytest.fixture
    def tracker(self, event_bus, mock_repo):
        t = SessionTracker(session_repo=mock_repo, event_bus=event_bus)
        t.start()
        return t

    def test_start_subscribes_to_events(self, event_bus, mock_repo):
        tracker = SessionTracker(session_repo=mock_repo, event_bus=event_bus)
        tracker.start()
        event_bus.publish(GameLaunched(
            game_id="test-game", emulator_id="melonds", rom_path="roms/test.nds"
        ))
        assert "test-game" in tracker._active_sessions

    def test_game_launched_creates_active_session(self, tracker):
        tracker._on_game_launched(GameLaunched(
            game_id="game-1", emulator_id="melonds", rom_path="roms/game1.nds"
        ))
        assert "game-1" in tracker._active_sessions
        assert tracker._active_sessions["game-1"].emulator_id == "melonds"

    def test_game_closed_persists_session(self, tracker, mock_repo):
        tracker._on_game_launched(GameLaunched(
            game_id="game-1", emulator_id="melonds", rom_path="roms/game1.nds"
        ))
        tracker._on_game_closed(GameClosed(
            game_id="game-1", emulator_id="melonds", session_duration=120.5
        ))
        assert len(mock_repo.sessions) == 1
        session = mock_repo.sessions[0]
        assert session.game_id == "game-1"
        assert session.duration_seconds == 120
        assert session.emulator_id == "melonds"

    def test_game_closed_without_launch_warns(self, tracker, mock_repo, capsys):
        tracker._on_game_closed(GameClosed(
            game_id="orphan-game", emulator_id="melonds", session_duration=60.0
        ))
        assert len(mock_repo.sessions) == 0
        captured = capsys.readouterr()
        assert "Aviso" in captured.out

    def test_multiple_sessions_accumulate_time(self, tracker, mock_repo):
        for i in range(3):
            tracker._on_game_launched(GameLaunched(
                game_id="game-1", emulator_id="melonds", rom_path="roms/game1.nds"
            ))
            tracker._on_game_closed(GameClosed(
                game_id="game-1", emulator_id="melonds", session_duration=300.0
            ))
        total = mock_repo.get_total_playtime("game-1")
        assert total == 900

    def test_concurrent_games_tracked_separately(self, tracker, mock_repo):
        tracker._on_game_launched(GameLaunched(
            game_id="game-a", emulator_id="melonds", rom_path="a.nds"
        ))
        tracker._on_game_closed(GameClosed(
            game_id="game-a", emulator_id="melonds", session_duration=100.0
        ))
        tracker._on_game_launched(GameLaunched(
            game_id="game-b", emulator_id="ppsspp", rom_path="b.iso"
        ))
        tracker._on_game_closed(GameClosed(
            game_id="game-b", emulator_id="ppsspp", session_duration=200.0
        ))
        assert len(mock_repo.sessions) == 2
        assert mock_repo.get_total_playtime("game-a") == 100
        assert mock_repo.get_total_playtime("game-b") == 200

    def test_format_duration(self):
        assert SessionTracker._format_duration(45) == "45s"
        assert SessionTracker._format_duration(125) == "2m 5s"
        assert SessionTracker._format_duration(3665) == "1h 01m"
        assert SessionTracker._format_duration(7200) == "2h 00m"

    def test_stop_ignores_events(self, tracker, mock_repo):
        tracker.stop()
        tracker._on_game_launched(GameLaunched(
            game_id="game-1", emulator_id="melonds", rom_path="game.nds"
        ))
        assert len(mock_repo.sessions) == 0
        assert len(tracker._active_sessions) == 0

    def test_event_bus_integration(self, event_bus, mock_repo):
        tracker = SessionTracker(session_repo=mock_repo, event_bus=event_bus)
        tracker.start()
        event_bus.publish(GameLaunched(
            game_id="real-game", emulator_id="mupen64plus", rom_path="roms/game.z64"
        ))
        time.sleep(0.01)
        event_bus.publish(GameClosed(
            game_id="real-game", emulator_id="mupen64plus", session_duration=45.0
        ))
        assert len(mock_repo.sessions) == 1
        assert mock_repo.sessions[0].game_id == "real-game"

    def test_get_most_played(self, tracker, mock_repo):
        for game_id, duration in [("game-a", 100), ("game-b", 300), ("game-c", 200)]:
            tracker._on_game_launched(GameLaunched(
                game_id=game_id, emulator_id="melonds", rom_path=f"{game_id}.nds"
            ))
            tracker._on_game_closed(GameClosed(
                game_id=game_id, emulator_id="melonds", session_duration=float(duration)
            ))
        most_played = tracker.get_most_played(limit=2)
        assert len(most_played) == 2
        assert most_played[0][0] == "game-b"
        assert most_played[1][0] == "game-c"