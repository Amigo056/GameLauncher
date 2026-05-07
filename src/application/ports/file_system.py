"""Porta de filesystem para casos de uso testaveis."""

from pathlib import Path
from typing import Protocol


class FileSystem(Protocol):
    """Contrato minimo para I/O de ficheiros."""

    def exists(self, path: Path) -> bool:
        """Verifica existencia."""
        ...

    def mkdir(self, path: Path, parents: bool = True, exist_ok: bool = True) -> None:
        """Cria diretorio."""
        ...

    def list_files(self, path: Path, pattern: str = "*") -> list[Path]:
        """Lista ficheiros por padrao."""
        ...

    def read_text(self, path: Path, encoding: str = "utf-8") -> str:
        """Le texto."""
        ...

    def write_text(self, path: Path, content: str, encoding: str = "utf-8") -> None:
        """Escreve texto."""
        ...
