"""Repositório SQLite para persistência de sessões de jogo."""
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional

from src.domain.entities.play_session import PlaySession


@dataclass
class GameStats:
    """Estatísticas agregadas de um jogo."""
    game_id: str
    emulator_id: str
    total_sessions: int
    total_playtime_seconds: float
    last_played: Optional[datetime]
    average_session_seconds: float


class SQLiteSessionRepository:
    """
    Repositório de sessões de jogo usando SQLite.
    
    Persiste tempo de jogo, estatísticas e histórico de sessões.
    """

    DB_PATH = Path("data/sessions.db")

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = Path(db_path) if db_path else self.DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        """Retorna conexão com row factory para acesso por nome."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """Cria tabelas se não existirem."""
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS play_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    game_id TEXT NOT NULL,
                    emulator_id TEXT NOT NULL,
                    started_at TIMESTAMP NOT NULL,
                    ended_at TIMESTAMP,
                    duration_seconds REAL DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_sessions_game 
                ON play_sessions(game_id)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_sessions_emulator 
                ON play_sessions(emulator_id)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_sessions_started 
                ON play_sessions(started_at DESC)
            """)
            
            conn.commit()

    def record_session(self, session: PlaySession) -> int:
        """
        Regista uma sessão de jogo completada.
        
        Returns:
            ID da sessão registada
        """
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO play_sessions 
                (game_id, emulator_id, started_at, ended_at, duration_seconds)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    session.game_id,
                    session.emulator_id,
                    session.started_at.isoformat(),
                    session.ended_at.isoformat() if session.ended_at else None,
                    session.duration_seconds,
                )
            )
            conn.commit()
            return cursor.lastrowid

    def get_total_playtime(self, game_id: str) -> timedelta:
        """
        Retorna tempo total de jogo para um jogo.
        
        Args:
            game_id: ID do jogo
            
        Returns:
            timedelta com tempo total
        """
        with self._get_connection() as conn:
            row = conn.execute(
                """
                SELECT COALESCE(SUM(duration_seconds), 0) as total
                FROM play_sessions
                WHERE game_id = ?
                """,
                (game_id,)
            ).fetchone()
            
            return timedelta(seconds=row["total"] if row else 0)

    def get_session_count(self, game_id: str) -> int:
        """Retorna número de sessões de um jogo."""
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT COUNT(*) as count FROM play_sessions WHERE game_id = ?",
                (game_id,)
            ).fetchone()
            return row["count"] if row else 0

    def get_most_played(self, limit: int = 10) -> List[GameStats]:
        """
        Retorna jogos mais jogados ordenados por tempo total.
        
        Args:
            limit: Número máximo de resultados
            
        Returns:
            Lista de GameStats
        """
        with self._get_connection() as conn:
            rows = conn.execute(
                """
                SELECT 
                    game_id,
                    emulator_id,
                    COUNT(*) as total_sessions,
                    COALESCE(SUM(duration_seconds), 0) as total_seconds,
                    MAX(started_at) as last_played,
                    COALESCE(AVG(duration_seconds), 0) as avg_seconds
                FROM play_sessions
                GROUP BY game_id, emulator_id
                ORDER BY total_seconds DESC
                LIMIT ?
                """,
                (limit,)
            ).fetchall()
            
            return [
                GameStats(
                    game_id=row["game_id"],
                    emulator_id=row["emulator_id"],
                    total_sessions=row["total_sessions"],
                    total_playtime_seconds=row["total_seconds"],
                    last_played=datetime.fromisoformat(row["last_played"]) if row["last_played"] else None,
                    average_session_seconds=row["avg_seconds"],
                )
                for row in rows
            ]

    def get_recent_sessions(self, limit: int = 20) -> List[PlaySession]:
        """
        Retorna sessões mais recentes.
        
        Args:
            limit: Número máximo de resultados
        """
        with self._get_connection() as conn:
            rows = conn.execute(
                """
                SELECT game_id, emulator_id, started_at, ended_at, duration_seconds
                FROM play_sessions
                ORDER BY started_at DESC
                LIMIT ?
                """,
                (limit,)
            ).fetchall()
            
            return [
                PlaySession(
                    game_id=row["game_id"],
                    emulator_id=row["emulator_id"],
                    started_at=datetime.fromisoformat(row["started_at"]),
                    ended_at=datetime.fromisoformat(row["ended_at"]) if row["ended_at"] else None,
                    duration_seconds=row["duration_seconds"],
                )
                for row in rows
            ]

    def get_game_stats(self, game_id: str) -> Optional[GameStats]:
        """Retorna estatísticas completas de um jogo específico."""
        with self._get_connection() as conn:
            row = conn.execute(
                """
                SELECT 
                    game_id,
                    emulator_id,
                    COUNT(*) as total_sessions,
                    COALESCE(SUM(duration_seconds), 0) as total_seconds,
                    MAX(started_at) as last_played,
                    COALESCE(AVG(duration_seconds), 0) as avg_seconds
                FROM play_sessions
                WHERE game_id = ?
                GROUP BY game_id, emulator_id
                """,
                (game_id,)
            ).fetchone()
            
            if not row:
                return None
            
            return GameStats(
                game_id=row["game_id"],
                emulator_id=row["emulator_id"],
                total_sessions=row["total_sessions"],
                total_playtime_seconds=row["total_seconds"],
                last_played=datetime.fromisoformat(row["last_played"]) if row["last_played"] else None,
                average_session_seconds=row["avg_seconds"],
            )

    def cleanup_old_sessions(self, days: int = 365) -> int:
        """
        Remove sessões mais antigas que N dias.
        
        Returns:
            Número de sessões removidas
        """
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        with self._get_connection() as conn:
            cursor = conn.execute(
                "DELETE FROM play_sessions WHERE started_at < ?",
                (cutoff,)
            )
            conn.commit()
            return cursor.rowcount