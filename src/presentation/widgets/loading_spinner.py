"""Widget de loading spinner animado para tkinter."""
import tkinter as tk
from typing import Optional

from src.presentation.theme import DARK_THEME, font


class LoadingSpinner(tk.Canvas):
    """
    Spinner de loading animado (estilo Material Design).
    
    Uso:
        spinner = LoadingSpinner(parent, size=40, color='#0078d4')
        spinner.pack()
        spinner.start()
        # ... trabalho ...
        spinner.stop()
    """

    def __init__(
        self,
        parent: tk.Widget,
        size: int = 40,
        color: str = None,
        bg_color: str = None,
        width: int = 4,
        speed: int = 80,  # ms entre frames
    ):
        t = DARK_THEME
        self._size = size
        self._color = color or t.accent
        self._bg_color = bg_color or t.bg_primary
        self._line_width = width
        self._speed = speed
        self._running = False
        self._angle = 0
        self._job_id: Optional[str] = None

        super().__init__(
            parent,
            width=size,
            height=size,
            bg=self._bg_color,
            highlightthickness=0,
        )

        self._center = size // 2
        self._radius = (size // 2) - width

    def start(self):
        """Inicia a animação do spinner."""
        if self._running:
            return
        self._running = True
        self._animate()

    def stop(self):
        """Para a animação e limpa o canvas."""
        self._running = False
        if self._job_id:
            self.after_cancel(self._job_id)
            self._job_id = None
        self.delete('all')

    def _animate(self):
        """Frame da animação — arco rotativo."""
        if not self._running:
            return

        self.delete('all')

        # Arco principal (270 graus)
        start = self._angle
        extent = 270

        self.create_arc(
            self._center - self._radius,
            self._center - self._radius,
            self._center + self._radius,
            self._center + self._radius,
            start=start,
            extent=extent,
            style='arc',
            outline=self._color,
            width=self._line_width,
        )

        # Arco secundário mais pequeno e transparente (efeito de rasto)
        self.create_arc(
            self._center - self._radius,
            self._center - self._radius,
            self._center + self._radius,
            self._center + self._radius,
            start=(start + 180) % 360,
            extent=90,
            style='arc',
            outline=self._color,
            width=max(1, self._line_width - 1),
            stipple='gray50',
        )

        self._angle = (self._angle + 10) % 360
        self._job_id = self.after(self._speed, self._animate)


class LoadingOverlay(tk.Frame):
    """
    Overlay de loading com spinner + mensagem.
    Cobre o widget pai completamente.
    """

    def __init__(
        self,
        parent: tk.Widget,
        message: str = "A carregar…",
        spinner_size: int = 50,
    ):
        t = DARK_THEME
        super().__init__(parent, bg=t.bg_primary)

        self.spinner = LoadingSpinner(self, size=spinner_size)
        self.spinner.pack(pady=(0, 15))

        tk.Label(
            self,
            text=message,
            bg=t.bg_primary,
            fg=t.text_secondary,
            font=font(t, "font_size_md"),
        ).pack()

    def show(self):
        """Mostra o overlay e inicia spinner."""
        self.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.lift()
        self.spinner.start()

    def hide(self):
        """Esconde o overlay e para spinner."""
        self.spinner.stop()
        self.place_forget()