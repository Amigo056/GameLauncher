"""Entidade de dominio para sessoes de jogo."""
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional


@dataclass
class PlaySession:
    """Representa uma sessao de jogo completada ou em curso."""

    game_id: str
    emulator_id: str
    started_at: datetime
    ended_at: Optional[datetime] = None
    duration_seconds: float = 0.0
    rom_path: Optional[Path] = None

    @property
    def start_time(self) -> datetime:
        """Compatibilidade com codigo/testes antigos."""
        return self.started_at

    @property
    def end_time(self) -> Optional[datetime]:
        """Compatibilidade com codigo/testes antigos."""
        return self.ended_at
