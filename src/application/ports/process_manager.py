"""Porta para gestao de processos do sistema."""

from typing import Optional, Protocol


class ProcessManager(Protocol):
    """Contrato para lancar e monitorizar processos externos."""

    def launch(self, command: str) -> int:
        """Lanca processo e retorna PID."""
        ...

    def is_running(self, pid: int) -> bool:
        """Verifica se processo ainda executa."""
        ...

    def wait_for_close(self, pid: int, timeout: Optional[float] = None) -> bool:
        """Aguarda fechamento do processo."""
        ...
