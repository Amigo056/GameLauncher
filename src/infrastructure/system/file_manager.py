"""Adaptador para abrir pastas no gestor de ficheiros do sistema."""
import os
import platform
import subprocess
from pathlib import Path


class FileManager:
    """Abre diretorios usando o comportamento nativo do sistema operativo."""

    def open_folder(self, path: Path) -> None:
        """Abre uma pasta no explorador de ficheiros."""
        folder = Path(path)
        folder.mkdir(parents=True, exist_ok=True)

        if platform.system() == "Windows":
            os.startfile(str(folder))  # type: ignore[attr-defined]
            return

        command = ["open", str(folder)] if platform.system() == "Darwin" else ["xdg-open", str(folder)]
        subprocess.Popen(
            command,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
