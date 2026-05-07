"""Probe local de hardware usando biblioteca standard e psutil quando disponivel."""

import platform
import subprocess

from src.application.ports.hardware_probe import HardwareProbe
from src.domain.value_objects.hardware_profile import HardwareProfile


class LocalHardwareProbe(HardwareProbe):
    """Analisa informacao basica do PC atual."""

    def inspect(self) -> HardwareProfile:
        """Retorna perfil de hardware local."""
        return HardwareProfile(
            os_name=platform.system() or "Unknown",
            os_version=platform.version() or "Unknown",
            cpu_name=self._cpu_name(),
            cpu_cores=self._cpu_cores(),
            ram_gb=self._ram_gb(),
            gpu_name=self._gpu_name(),
        )

    def _cpu_name(self) -> str:
        cpu = platform.processor().strip()
        return cpu or platform.machine() or "Unknown"

    def _cpu_cores(self) -> int:
        try:
            import os

            return os.cpu_count() or 1
        except Exception:
            return 1

    def _ram_gb(self) -> float:
        try:
            import psutil

            return round(psutil.virtual_memory().total / (1024**3), 2)
        except Exception:
            return 0.0

    def _gpu_name(self) -> str:
        if platform.system() != "Windows":
            return "Unknown"

        try:
            result = subprocess.run(
                [
                    "powershell",
                    "-NoProfile",
                    "-Command",
                    "Get-CimInstance Win32_VideoController | "
                    "Select-Object -First 1 -ExpandProperty Name",
                ],
                capture_output=True,
                text=True,
                timeout=3,
                check=False,
            )
            gpu = result.stdout.strip()
            return gpu or "Unknown"
        except Exception:
            return "Unknown"
