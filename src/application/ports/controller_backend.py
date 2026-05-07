"""Porta para backends de controlos."""

from typing import Protocol


class ControllerBackend(Protocol):
    """Contrato para detetar e ler comandos/controlos."""

    def list_controllers(self) -> list[object]:
        """Lista controlos ligados."""
        ...
