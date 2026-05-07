"""Eventos de dominio: comunicacao desacoplada entre camadas."""
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from threading import RLock
from typing import Callable, Optional
from uuid import uuid4


@dataclass(frozen=True, kw_only=True)
class DomainEvent:
    """Classe base para todos os eventos."""
    timestamp: datetime = field(default_factory=datetime.now)
    event_id: str = field(default_factory=lambda: str(uuid4()))

# === Eventos de Emulação ===

@dataclass(frozen=True, kw_only=True)
class GameLaunched(DomainEvent):
    """Emulador iniciado com jogo."""
    game_id: str
    emulator_id: str
    rom_path: Path
    process_id: Optional[int] = None  # PID se disponível


@dataclass(frozen=True, kw_only=True)
class GameClosed(DomainEvent):
    """Emulador encerrado."""
    game_id: str
    emulator_id: str
    session_duration: float = 0.0  # segundos


# === Bus/Event Dispatcher (Simples) ===

class EventBus:
    """Barramento de eventos simples (pub/sub) para desacoplar UI."""
    
    def __init__(self):
        self._handlers: dict[type, list[Callable]] = {}
        self._lock = RLock()
    
    def subscribe(self, event_type: type, handler: Callable) -> None:
        """Regista handler para tipo de evento."""
        with self._lock:
            if event_type not in self._handlers:
                self._handlers[event_type] = []
            if handler not in self._handlers[event_type]:
                self._handlers[event_type].append(handler)
    
    def unsubscribe(self, event_type: type, handler: Callable) -> None:
        """Remove handler."""
        with self._lock:
            if event_type in self._handlers:
                self._handlers[event_type] = [
                    h for h in self._handlers[event_type] if h != handler
                ]
    
    def emit(self, event: DomainEvent) -> None:
        """Dispara evento para todos os subscribers."""
        event_type = type(event)
        with self._lock:
            handlers = list(self._handlers.get(event_type, []))

        for handler in handlers:
            try:
                handler(event)
            except Exception as e:
                # Log mas nao quebra a cadeia
                print(f"Erro em handler de {event_type.__name__}: {e}")

    def publish(self, event: DomainEvent) -> None:
        """Alias retrocompativel para emit()."""
        self.emit(event)
    
    def clear(self) -> None:
        """Remove todos os handlers."""
        with self._lock:
            self._handlers.clear()


# Instância global do bus (padrão Singleton para aplicação)
event_bus = EventBus()
