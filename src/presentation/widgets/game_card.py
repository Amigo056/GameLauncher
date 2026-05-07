"""Widget reutilizável: card de um jogo no grid."""
import threading
import tkinter as tk
from pathlib import Path
from PIL import Image, ImageTk

from src.domain.entities.game import Game
from src.presentation.theme import DARK_THEME


COVER_DIMENSIONS: dict[str, tuple[int, int]] = {
    "ppsspp":      (160, 90),
    "melonds":     (128, 128),
    "mupen64plus": (140, 105),
    "mgba":        (160, 107),
}
DEFAULT_COVER_SIZE: tuple[int, int] = (140, 105)


class GameCard(tk.Frame):
    """Card visual para um jogo: capa + título + região + estatísticas."""

    def __init__(
        self,
        parent: tk.Widget,
        game: Game,
        cover_w: int,
        cover_h: int,
        on_play: callable,
        image_cache: dict,
        frame_ref: tk.Widget,
        stats_text: str = "",
    ):
        t = DARK_THEME
        super().__init__(parent, bg=t.bg_card, padx=8, pady=8, cursor='hand2')

        self.game = game
        self.cover_w = cover_w
        self.cover_h = cover_h
        self.on_play = on_play
        self._image_cache = image_cache
        self._frame_ref = frame_ref
        self.stats_text = stats_text

        self._build()
        self._load_cover_async()

    def _build(self):
        t = DARK_THEME

        self._lbl_cover = tk.Label(
            self,
            bg=t.bg_tertiary,
            width=self.cover_w // 8,
            height=self.cover_h // 16,
        )
        self._lbl_cover.pack()

        title = self.game.title
        if len(title) > 26:
            title = title[:25] + "…"
        tk.Label(
            self,
            text=title,
            bg=t.bg_card,
            fg=t.text_primary,
            font=(t.font_family, t.font_size_sm, "bold"),
            wraplength=self.cover_w + 20,
            justify='center',
        ).pack(pady=(8, 0))

        if self.game.region.name != "UNKNOWN":
            tk.Label(
                self,
                text=f"({self.game.region.name})",
                bg=t.bg_card,
                fg=t.text_secondary,
                font=(t.font_family, t.font_size_sm),
            ).pack()

        if self.stats_text:
            tk.Label(
                self,
                text=self.stats_text,
                bg=t.bg_card,
                fg=t.accent,
                font=(t.font_family, t.font_size_sm),
            ).pack(pady=(2, 0))

        for widget in [self, self._lbl_cover]:
            widget.bind('<Button-1>', lambda e, g=self.game: self.on_play(g))

        self.bind('<Enter>', self._on_enter)
        self.bind('<Leave>', self._on_leave)

    def _on_enter(self, _=None):
        t = DARK_THEME
        self.configure(bg=t.bg_hover)
        for child in self.winfo_children():
            if isinstance(child, tk.Label):
                child.configure(bg=t.bg_hover)

    def _on_leave(self, _=None):
        t = DARK_THEME
        self.configure(bg=t.bg_card)
        for child in self.winfo_children():
            if isinstance(child, tk.Label):
                child.configure(bg=t.bg_card)

    def _load_cover_async(self):
        t = DARK_THEME

        def load():
            try:
                cover_path: Path | None = None
                if self.game.cover and self.game.cover.is_local:
                    cover_path = self.game.cover.local_path

                if cover_path and cover_path.exists():
                    img = Image.open(cover_path).convert("RGBA")
                    orig_w, orig_h = img.size
                    ratio = min(self.cover_w / orig_w, self.cover_h / orig_h)
                    new_w, new_h = int(orig_w * ratio), int(orig_h * ratio)
                    img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)

                    bg_color = (51, 51, 51, 255)
                    canvas_img = Image.new("RGBA", (self.cover_w, self.cover_h), bg_color)
                    canvas_img.paste(img, ((self.cover_w - new_w) // 2, (self.cover_h - new_h) // 2), img)

                    photo = ImageTk.PhotoImage(canvas_img)
                    self._image_cache[self.game.id] = photo

                    self._frame_ref.after(0, lambda: self._lbl_cover.configure(
                        image=photo, width=self.cover_w, height=self.cover_h
                    ))
                else:
                    self._frame_ref.after(0, lambda: self._lbl_cover.configure(
                        text="?", fg=t.text_disabled,
                        font=(t.font_family, 20),
                        width=self.cover_w // 8,
                        height=self.cover_h // 16,
                    ))
            except Exception:
                pass

        threading.Thread(target=load, daemon=True).start()