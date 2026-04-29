from typing import Optional, Protocol


class ProcessManager(Protocol):
    """
    Protocolo para gerenciamento de processos.
    Implementação: infrastructure/system/process_manager.py
    """
    def launch(self, command: str) -> int:
        """Lança processo e retorna PID."""
        ...

    def is_running(self, pid: int) -> bool:
        """Verifica se processo ainda executa."""
        ...

    def wait_for_close(self, pid: int, timeout: Optional[float] = None) -> bool:
        """Aguarda fechamento do processo."""
        ...