"""Pattern Observable simples para data binding MVVM."""
from typing import List, Callable, Any


class Observable:
    """Valor observável que notifica subscribers quando muda."""
    
    def __init__(self, initial_value: Any = None):
        self._value = initial_value
        self._callbacks: List[Callable] = []
    
    @property
    def value(self):
        return self._value
    
    def set(self, new_value: Any):
        if self._value != new_value:
            self._value = new_value
            self._notify()
    
    def _notify(self):
        for callback in self._callbacks:
            try:
                callback(self._value)
            except Exception as e:
                print(f"Erro em observer: {e}")
    
    def subscribe(self, callback: Callable):
        self._callbacks.append(callback)
        callback(self._value)  # Chamar imediatamente com valor atual
    
    def unsubscribe(self, callback: Callable):
        if callback in self._callbacks:
            self._callbacks.remove(callback)