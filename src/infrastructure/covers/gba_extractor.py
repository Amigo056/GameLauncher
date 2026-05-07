"""
Extrator de covers GBA: captura ecrã inicial via mGBA.

Estratégia:
  1. Lança mGBA com a ROM em janela pequena (escala 2x → 480×320)
  2. Aguarda ~3.5 s para o título aparecer
  3. Captura a área do cliente (jogo sem chrome do OS) usando ctypes + PIL
  4. Fecha mGBA, guarda PNG, retorna Cover

Só funciona em Windows. Em outros sistemas retorna (None, None).
Não requer dependências além de Pillow (já instalado).
"""

import ctypes
import ctypes.wintypes
import platform
import subprocess
import time
from pathlib import Path
from typing import Optional, Tuple

from PIL import Image, ImageGrab

from src.domain.entities.game import Cover
from src.domain.services.cover_extractor import CoverExtractor


class GBAScreenshotExtractor(CoverExtractor):
    """
    Extrai cover de ROMs GBA capturando a ecrã de título do mGBA.

    Parâmetros
    ----------
    mgba_path : Path
        Caminho para o executável mGBA.exe.
    wait_seconds : float
        Tempo de espera em segundos antes de tirar screenshot.
        Default: 3.5 s (suficiente para a maioria dos jogos GBA mostrarem o título).
    window_scale : int
        Factor de escala do mGBA (1 = 240×160, 2 = 480×320, 3 = 720×480).
        Default: 2.
    """

    GBA_EXTENSIONS = {".gba", ".gbc", ".gb"}

    def __init__(
        self,
        mgba_path: Optional[Path],
        wait_seconds: float = 3.5,
        window_scale: int = 2,
    ):
        self.mgba_path    = Path(mgba_path) if mgba_path else None
        self.wait_seconds = wait_seconds
        self.window_scale = window_scale

    # ─────────────────────────────────────────────
    # CONTRATO CoverExtractor
    # ─────────────────────────────────────────────

    @property
    def supported_extensions(self) -> list[str]:
        return list(self.GBA_EXTENSIONS)

    def can_extract(self, rom_path: Path) -> bool:
        return (
            platform.system() == "Windows"
            and rom_path.suffix.lower() in self.GBA_EXTENSIONS
            and self.mgba_path is not None
            and self.mgba_path.exists()
        )

    def extract(
        self, rom_path: Path, game_id: str, output_dir: Path
    ) -> Tuple[Optional[Cover], Optional[str]]:

        if not self.can_extract(rom_path):
            return None, None

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        cover_path = output_dir / f"{game_id}_title.png"

        # Reutilizar screenshot existente se o ficheiro for mais recente que a ROM
        if cover_path.exists():
            rom_mtime   = rom_path.stat().st_mtime
            cover_mtime = cover_path.stat().st_mtime
            if cover_mtime > rom_mtime:
                return Cover(local_path=cover_path), None

        try:
            img = self._run_and_capture(rom_path)
        except Exception as e:
            print(f"[GBA] Erro a capturar screenshot de {rom_path.name}: {e}")
            return None, None

        if img is None:
            return None, None

        try:
            img.save(cover_path, "PNG")
            return Cover(local_path=cover_path), None
        except Exception as e:
            print(f"[GBA] Erro a guardar screenshot: {e}")
            return None, None

    # ─────────────────────────────────────────────
    # LÓGICA INTERNA
    # ─────────────────────────────────────────────

    def _run_and_capture(self, rom_path: Path) -> Optional[Image.Image]:
        """
        Lança mGBA, espera o título aparecer, captura a janela, fecha mGBA.
        Retorna imagem RGBA ou None em caso de falha.
        """
        process = subprocess.Popen(
            [
                str(self.mgba_path.resolve()),
                "--size", str(self.window_scale),
                str(rom_path.resolve()),
            ],
            shell=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        try:
            # Aguardar janela abrir + título aparecer
            time.sleep(self.wait_seconds)

            # Encontrar janela pelo PID (evita conflitos se mGBA já estiver aberto)
            hwnd = self._find_window_by_pid(process.pid)
            if hwnd is None:
                # Fallback: procurar por título "mGBA"
                hwnd = self._find_window_by_title("mGBA")

            if hwnd is None:
                print(f"[GBA] Janela mGBA não encontrada para {rom_path.name}")
                return None

            img = self._capture_client_area(hwnd)
            return img

        finally:
            # Garantir sempre que o processo fecha
            try:
                process.terminate()
                process.wait(timeout=3)
            except Exception:
                try:
                    process.kill()
                except Exception:
                    pass

    # ─────────────────────────────────────────────
    # WINDOWS API — encontrar janela
    # ─────────────────────────────────────────────

    def _find_window_by_pid(self, pid: int) -> Optional[int]:
        """Encontra HWND da janela principal de um processo pelo PID."""
        found: list[int] = []

        def enum_callback(hwnd, _):
            # Só janelas visíveis e com título
            if not ctypes.windll.user32.IsWindowVisible(hwnd):
                return True
            length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
            if length == 0:
                return True

            # Verificar PID do processo dono da janela
            win_pid = ctypes.c_ulong(0)
            ctypes.windll.user32.GetWindowThreadProcessId(
                hwnd, ctypes.byref(win_pid)
            )
            if win_pid.value == pid:
                found.append(hwnd)
            return True

        EnumWindowsProc = ctypes.WINFUNCTYPE(
            ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p
        )
        ctypes.windll.user32.EnumWindows(EnumWindowsProc(enum_callback), 0)

        # Preferir a janela com "mGBA" no título (ignora workers/helpers internos)
        for hwnd in found:
            title = self._get_window_title(hwnd)
            if "mgba" in title.lower():
                return hwnd

        return found[0] if found else None

    def _find_window_by_title(self, partial_title: str) -> Optional[int]:
        """Fallback: encontra HWND por substring do título."""
        found: list[int] = []

        def enum_callback(hwnd, _):
            if not ctypes.windll.user32.IsWindowVisible(hwnd):
                return True
            title = self._get_window_title(hwnd)
            if partial_title.lower() in title.lower():
                found.append(hwnd)
            return True

        EnumWindowsProc = ctypes.WINFUNCTYPE(
            ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p
        )
        ctypes.windll.user32.EnumWindows(EnumWindowsProc(enum_callback), 0)
        return found[0] if found else None

    def _get_window_title(self, hwnd: int) -> str:
        length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
        buf = ctypes.create_unicode_buffer(length + 1)
        ctypes.windll.user32.GetWindowTextW(hwnd, buf, length + 1)
        return buf.value

    # ─────────────────────────────────────────────
    # WINDOWS API — capturar área cliente
    # ─────────────────────────────────────────────

    def _capture_client_area(self, hwnd: int) -> Optional[Image.Image]:
        """
        Captura apenas a área do cliente (jogo sem barra de título nem bordas).
        Usa ClientToScreen para converter coordenadas locais em coordenadas de ecrã,
        depois PIL.ImageGrab para capturar a região.
        """
        # Dimensões da área cliente (em coordenadas locais, origem = (0,0))
        client_rect = ctypes.wintypes.RECT()
        if not ctypes.windll.user32.GetClientRect(hwnd, ctypes.byref(client_rect)):
            return None

        w = client_rect.right  - client_rect.left
        h = client_rect.bottom - client_rect.top

        if w <= 0 or h <= 0:
            return None

        # Converter o canto superior esquerdo do cliente para coordenadas de ecrã
        pt = ctypes.wintypes.POINT(0, 0)
        ctypes.windll.user32.ClientToScreen(hwnd, ctypes.byref(pt))

        bbox = (pt.x, pt.y, pt.x + w, pt.y + h)

        try:
            img = ImageGrab.grab(bbox=bbox, all_screens=True)
        except TypeError:
            # Versões mais antigas do Pillow não têm all_screens
            img = ImageGrab.grab(bbox=bbox)

        if img.size == (0, 0):
            return None

        return img.convert("RGBA")