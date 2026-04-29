"""Widget reutilizável: card de um jogo no grid."""
import threading
import tkinter as tk
from pathlib import Path
from PIL import Image, ImageTk

from src.domain.entities.game import Game


# Dimensões de cover por emulador (largura px, altura px)
COVER_DIMENSIONS: dict[str, tuple[int, int]] = {
    "ppsspp":      (160, 90),    # PIC1 480×272 → 16:9 landscape
    "melonds":     (128, 128),   # Ícone NDS 32×32 escalado → quadrado
    "mupen64plus": (140, 105),   # N64 → 4:3
}
DEFAULT_COVER_SIZE: tuple[int, int] = (140, 105)


class GameCard(tk.Frame):
    """
    Card visual para um jogo: capa + título + região.
    Reutilizável em qualquer grid — não conhece o emulador,
    recebe apenas as dimensões de cover e os callbacks.
    """

    BG_NORMAL  = '#252525'
    BG_HOVER   = '#353535'
    BG_COVER   = '#333333'

    def __init__(
        self,
        parent: tk.Widget,
        game: Game,
        cover_w: int,
        cover_h: int,
        on_play: callable,
        image_cache: dict,          # partilhado com a página pai
        frame_ref: tk.Widget,       # frame pai para .after() thread-safe
    ):
        super().__init__(parent, bg=self.BG_NORMAL, padx=8, pady=8, cursor='hand2')

        self.game = game
        self.cover_w = cover_w
        self.cover_h = cover_h
        self.on_play = on_play
        self._image_cache = image_cache
        self._frame_ref = frame_ref

        self._build()
        self._load_cover_async()

    # ─────────────────────────────────────────────
    # BUILD
    # ─────────────────────────────────────────────

    def _build(self):
        # Placeholder da capa
        self._lbl_cover = tk.Label(
            self,
            bg=self.BG_COVER,
            width=self.cover_w // 8,
            height=self.cover_h // 16,
        )
        self._lbl_cover.pack()

        # Título (truncado)
        title = self.game.title
        if len(title) > 26:
            title = title[:25] + "…"
        tk.Label(
            self,
            text=title,
            bg=self.BG_NORMAL,
            fg='white',
            font=('Segoe UI', 9, 'bold'),
            wraplength=self.cover_w + 20,
            justify='center',
        ).pack(pady=(8, 0))

        # Região
        if self.game.region.name != "UNKNOWN":
            tk.Label(
                self,
                text=f"({self.game.region.name})",
                bg=self.BG_NORMAL,
                fg='#888888',
                font=('Segoe UI', 8),
            ).pack()

        # Eventos de clique e hover
        for widget in [self, self._lbl_cover]:
            widget.bind('<Button-1>', lambda e, g=self.game: self.on_play(g))

        self.bind('<Enter>', self._on_enter)
        self.bind('<Leave>', self._on_leave)

    # ─────────────────────────────────────────────
    # HOVER
    # ─────────────────────────────────────────────

    def _on_enter(self, _=None):
        self.configure(bg=self.BG_HOVER)
        for child in self.winfo_children():
            if isinstance(child, tk.Label):
                child.configure(bg=self.BG_HOVER)

    def _on_leave(self, _=None):
        self.configure(bg=self.BG_NORMAL)
        for child in self.winfo_children():
            if isinstance(child, tk.Label):
                child.configure(bg=self.BG_NORMAL)

    # ─────────────────────────────────────────────
    # COVER ASYNC
    # ─────────────────────────────────────────────

    def _load_cover_async(self):
        """Carrega a capa em thread separada — nunca bloqueia a UI."""
        def load():
            try:
                cover_path: Path | None = None
                if self.game.cover and self.game.cover.is_local:
                    cover_path = self.game.cover.local_path

                if cover_path and cover_path.exists():
                    img = Image.open(cover_path).convert("RGBA")

                    # Fit proporcional dentro do box
                    orig_w, orig_h = img.size
                    ratio = min(self.cover_w / orig_w, self.cover_h / orig_h)
                    new_w, new_h = int(orig_w * ratio), int(orig_h * ratio)
                    img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)

                    # Centrar em fundo neutro
                    canvas_img = Image.new("RGBA", (self.cover_w, self.cover_h), (45, 45, 45, 255))
                    canvas_img.paste(img, ((self.cover_w - new_w) // 2, (self.cover_h - new_h) // 2), img)

                    photo = ImageTk.PhotoImage(canvas_img)
                    self._image_cache[self.game.id] = photo

                    self._frame_ref.after(0, lambda: self._lbl_cover.configure(
                        image=photo, width=self.cover_w, height=self.cover_h
                    ))
                else:
                    self._frame_ref.after(0, lambda: self._lbl_cover.configure(
                        text="?", fg='#555555',
                        font=('Segoe UI', 20),
                        width=self.cover_w // 8,
                        height=self.cover_h // 16,
                    ))
            except Exception:
                pass

        threading.Thread(target=load, daemon=True).start()