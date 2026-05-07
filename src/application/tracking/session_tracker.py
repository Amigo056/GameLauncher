"""SessionTracker — conecta EventBus ao SQLiteSessionRepository.

Este módulo é o "glue" que permite tracking automático de tempo de jogo.
Subscreve-se aos eventos GameLaunched e GameClosed e persiste as sessões.
"""
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

from src.application.events import GameLaunched, GameClosed
from src.domain.entities.play_session import PlaySession
from src.infrastructure.persistence.session_repo import SQLiteSessionRepository


@dataclass
class _ActiveSession:
    """Sessão ativa em memória (antes de fechar)."""
    game_id: str
    emulator_id: str
    rom_path: Optional[Path]
    start_time: datetime = field(default_factory=datetime.now)


class SessionTracker:
    """
    Tracking automático de sessões de jogo.

    Subscreve-se ao EventBus e persiste sessões no repositório.
    Uso:
        tracker = SessionTracker(session_repo, event_bus)
        tracker.start()  # Inicia subscrições
        # ... jogos são lançados e fechados ...
        tracker.stop()   # Opcional: remove subscrições

    Attributes:
        session_repo: Repositório para persistir sessões
        event_bus: EventBus para subscrever eventos
        _active_sessions: Dict[game_id, _ActiveSession] — sessões em curso
    """

    def __init__(
        self,
        session_repo: SQLiteSessionRepository,
        event_bus=None,
    ):
        self.session_repo = session_repo
        self.event_bus = event_bus
        self._active_sessions: dict[str, _ActiveSession] = {}
        self._is_started = False

    def start(self):
        """Inicia subscrições no EventBus.

        Idempotente — pode ser chamado múltiplas vezes sem efeitos secundários.
        """
        if self._is_started or not self.event_bus:
            return

        self.event_bus.subscribe(GameLaunched, self._on_game_launched)
        self.event_bus.subscribe(GameClosed, self._on_game_closed)
        self._is_started = True
        print("[SessionTracker] Subscrições ativas")

    def stop(self):
        """Remove subscrições do EventBus."""
        # Nota: O EventBus atual não suporta unsubscribe,
        # mas guardamos estado para ignorar eventos futuros
        self._is_started = False
        print("[SessionTracker] Subscrições desativadas")

    def _on_game_launched(self, event: GameLaunched):
        """Handler para GameLaunched — inicia tracking em memória."""
        if not self._is_started:
            return

        session = _ActiveSession(
            game_id=event.game_id,
            emulator_id=event.emulator_id,
            rom_path=Path(event.rom_path) if event.rom_path else None,
        )
        self._active_sessions[event.game_id] = session
        print(f"[SessionTracker] Sessão iniciada: {event.game_id}")

    def _on_game_closed(self, event: GameClosed):
        """Handler para GameClosed — persiste sessão no SQLite."""
        if not self._is_started:
            return

        active = self._active_sessions.pop(event.game_id, None)
        if not active:
            print(f"[SessionTracker] Aviso: GameClosed sem GameLaunched para {event.game_id}")
            return

        end_time = datetime.now()
        duration = event.session_duration

        play_session = PlaySession(
            game_id=event.game_id,
            emulator_id=event.emulator_id,
            start_time=active.start_time,
            end_time=end_time,
            duration_seconds=int(duration) if duration > 0 else None,
            rom_path=active.rom_path,
        )

        try:
            self.session_repo.save(play_session)
            print(
                f"[SessionTracker] Sessão guardada: {event.game_id} "
                f"({duration:.0f}s)"
            )
        except Exception as e:
            print(f"[SessionTracker] Erro ao guardar sessão: {e}")

    # ─── Queries úteis para a UI ─────────────────────────────

    def get_total_playtime(self, game_id: str) -> str:
        """Retorna tempo total formatado (ex: '2h 15m')."""
        seconds = self.session_repo.get_total_playtime(game_id)
        return self._format_duration(seconds)

    def get_session_count(self, game_id: str) -> int:
        """Retorna número de sessões de um jogo."""
        return len(self.session_repo.get_by_game(game_id))

    def get_most_played(self, limit: int = 5) -> list[tuple[str, str]]:
        """Retorna jogos mais jogados (game_id, tempo_formatado)."""
        rows = self.session_repo.get_most_played(limit)
        return [(gid, self._format_duration(seconds)) for gid, seconds in rows]

    def get_recent_sessions(self, limit: int = 5) -> list[PlaySession]:
        """Retorna sessões recentes."""
        return self.session_repo.get_recent_sessions(limit)

    @staticmethod
    def _format_duration(seconds: int) -> str:
        """Formata segundos para human-readable."""
        if seconds < 60:
            return f"{seconds}s"
        if seconds < 3600:
            return f"{seconds // 60}m {seconds % 60}s"
        hours = seconds // 3600
        mins = (seconds % 3600) // 60
        return f"{hours}h {mins:02d}m"