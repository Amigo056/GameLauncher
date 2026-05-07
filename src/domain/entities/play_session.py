from dataclasses import dataclass
import datetime
from typing import Optional


@dataclass
class PlaySession:
    game_id: str
    emulator_id: str
    started_at: datetime
    ended_at: Optional[datetime] # type: ignore
    duration_seconds: float