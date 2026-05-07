"""Invalidador automático de cache baseado em eventos."""
from pathlib import Path
from typing import Callable, Optional

from src.application.events import event_bus, GameLaunched, GameClosed
from src.infrastructure.cache.cover_cache import CoverCache


class CacheInvalidator:
    """Invalida cache automaticamente quando eventos relevantes ocorrem."""

    def __init__(self, cover_cache: Optional[CoverCache] = None):
        self.cover_cache = cover_cache or CoverCache()
        self._subscribed = False

    def start_listening(self):
        """Inicia subscrição no EventBus."""
        if self._subscribed:
            return
        event_bus.subscribe(GameLaunched, self._on_game_launched)
        event_bus.subscribe(GameClosed, self._on_game_closed)
        self._subscribed = True

    def stop_listening(self):
        """Para subscrição no EventBus."""
        if not self._subscribed:
            return
        event_bus.unsubscribe(GameLaunched, self._on_game_launched)
        event_bus.unsubscribe(GameClosed, self._on_game_closed)
        self._subscribed = False

    def _on_game_launched(self, event: GameLaunched):
        """Nada a fazer no lançamento."""
        pass

    def _on_game_closed(self, event: GameClosed):
        """Após fechar jogo, verificar se ROM foi modificada."""
        pass

    def periodic_cleanup(self):
        """Executa limpeza periódica do cache."""
        removed = self.cover_cache.cleanup()
        if removed > 0:
            print(f"[Cache] {removed} entradas órfãs/expiradas removidas")