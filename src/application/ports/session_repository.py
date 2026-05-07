"""Porta de persistencia de sessoes de jogo."""

from datetime import timedelta
from typing import Protocol

from src.domain.entities.play_session import PlaySession


class SessionRepository(Protocol):
    """Contrato para historico e estatisticas de sessoes."""

    def record_session(self, session: PlaySession) -> int:
        """Regista uma sessao completada."""
        ...

    def get_by_game(self, game_id: str) -> list[PlaySession]:
        """Retorna sessoes de um jogo."""
        ...

    def get_total_playtime(self, game_id: str) -> timedelta:
        """Retorna tempo total de jogo."""
        ...

    def get_session_count(self, game_id: str) -> int:
        """Retorna numero de sessoes."""
        ...

    def get_recent_sessions(self, limit: int = 20) -> list[PlaySession]:
        """Retorna sessoes recentes."""
        ...
