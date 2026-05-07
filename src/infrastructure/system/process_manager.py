"""Implementação concreta: Gerenciamento de processos do sistema."""
import subprocess
import time
import platform
from pathlib import Path
from typing import Optional

import psutil

from src.application.protocols.process_manager import ProcessManager


class SubprocessProcessManager(ProcessManager):
    """Implementação do ProcessManager usando subprocess e psutil."""

    def __init__(self, shell: bool = False):
        self.shell = shell
        self.system = platform.system()
        self._creationflags = 0
        
        if self.system == "Windows":
            self._creationflags = subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS

    def launch(self, command: str) -> int:
        """
        Lança processo e retorna PID.
        Corre o processo na pasta do executável para encontrar DLLs/plugins.
        """
        try:
            print(f"[DEBUG] Launching: {command}")  # ⬅️ ADICIONAR

            # Extrair diretório do executável SEM shlex.split
            # O comando começa com "path\do\exe" ou path\do\exe (sem aspas)
            command_stripped = command.strip()
            if command_stripped.startswith('"'):
                # Path com aspas: "C:\Program Files\...\exe" ...
                end_quote = command_stripped.find('"', 1)
                exe_path = Path(command_stripped[1:end_quote])
            else:
                # Path sem aspas: C:\Users\...\exe ...
                first_space = command_stripped.find(' ')
                if first_space == -1:
                    exe_path = Path(command_stripped)
                else:
                    exe_path = Path(command_stripped[:first_space])
            
            
            exe_path = exe_path.resolve()
            working_dir = exe_path.parent
            print(f"[DEBUG] Working dir: {working_dir}")
            if self.system == "Windows":
                process = subprocess.Popen(
                    command,
                    shell=self.shell,
                    creationflags=self._creationflags,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    cwd=str(working_dir)
                )
            else:
                process = subprocess.Popen(
                    command,
                    shell=self.shell,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True,
                    cwd=str(working_dir)
                )
            
            return process.pid
            
        except Exception as e:
            raise RuntimeError(f"Falha ao lançar processo: {e}")
        
    def is_running(self, pid: int) -> bool:
        """Verifica se processo ainda existe."""
        try:
            process = psutil.Process(pid)
            return process.is_running()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return False

    def wait_for_close(self, pid: int, timeout: Optional[float] = None) -> bool:
        """Aguarda processo encerrar."""
        start_time = time.time()
        check_interval = 0.5
        
        try:
            process = psutil.Process(pid)
            process.wait(timeout=timeout)
            return True
        except psutil.TimeoutExpired:
            return False
        except psutil.NoSuchProcess:
            return True

    def terminate(self, pid: int, force: bool = False) -> bool:
        """Encerra processo."""
        try:
            process = psutil.Process(pid)
            if force:
                process.kill()
            else:
                process.terminate()
            
            gone, alive = psutil.wait_procs([process], timeout=3)
            return len(gone) > 0
            
        except Exception as e:
            print(f"Erro terminando processo {pid}: {e}")
            return False


def get_process_manager() -> ProcessManager:
    """Retorna instância adequada ao sistema."""
    return SubprocessProcessManager()