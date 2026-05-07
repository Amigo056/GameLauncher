"""Widget reutilizável: card de um jogo no grid."""
from collections.abc import Callable
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
        on_play: Callable[[Game], None],
        image_cache: dict,
        frame_ref: tk.Widget,
        stats_text: str = "",
        on_details: Callable[[Game], None] | None = None,
        on_toggle_favorite: Callable[[Game], bool] | None = None,
        is_favorite: bool = False,
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
        self.on_details = on_details
        self.on_toggle_favorite = on_toggle_favorite
        self.is_favorite = is_favorite
        self._btn_favorite: tk.Button | None = None

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
        title_label = tk.Label(
            self,
            text=title,
            bg=t.bg_card,
            fg=t.text_primary,
            font=(t.font_family, t.font_size_sm, "bold"),
            wraplength=self.cover_w + 20,
            justify='center',
        )
        title_label.pack(pady=(8, 0))
        clickable_widgets = [self, self._lbl_cover, title_label]

        if self.game.region.name != "UNKNOWN":
            region_label = tk.Label(
                self,
                text=f"({self.game.region.name})",
                bg=t.bg_card,
                fg=t.text_secondary,
                font=(t.font_family, t.font_size_sm),
            )
            region_label.pack()
            clickable_widgets.append(region_label)

        if self.stats_text:
            stats_label = tk.Label(
                self,
                text=self.stats_text,
                bg=t.bg_card,
                fg=t.accent,
                font=(t.font_family, t.font_size_sm),
            )
            stats_label.pack(pady=(2, 0))
            clickable_widgets.append(stats_label)

        actions = tk.Frame(self, bg=t.bg_card)
        actions.pack(pady=(8, 0), fill='x')

        if self.on_toggle_favorite:
            self._btn_favorite = tk.Button(
                actions,
                text="*" if self.is_favorite else "+",
                width=3,
                bg=t.bg_tertiary,
                fg=t.warning if self.is_favorite else t.text_secondary,
                activebackground=t.bg_hover,
                activeforeground=t.warning,
                relief='flat',
                cursor='hand2',
                command=self._toggle_favorite,
            )
            self._btn_favorite.pack(side='left', padx=(0, 4))

        if self.on_details:
            tk.Button(
                actions,
                text="Info",
                bg=t.bg_tertiary,
                fg=t.text_primary,
                activebackground=t.bg_hover,
                activeforeground=t.text_primary,
                relief='flat',
                cursor='hand2',
                command=lambda g=self.game: self.on_details(g),
            ).pack(side='left', expand=True, fill='x', padx=(0, 4))

        tk.Button(
            actions,
            text="Jogar",
            bg=t.accent,
            fg=t.text_primary,
            activebackground=t.accent_hover,
            activeforeground=t.text_primary,
            relief='flat',
            cursor='hand2',
            command=lambda g=self.game: self.on_play(g),
        ).pack(side='left', expand=True, fill='x')

        for widget in clickable_widgets:
            widget.bind('<Button-1>', lambda _event: self._open_details())

        self.bind('<Enter>', self._on_enter)
        self.bind('<Leave>', self._on_leave)

    def _toggle_favorite(self):
        if not self.on_toggle_favorite:
            return

        self.is_favorite = bool(self.on_toggle_favorite(self.game))
        if self._btn_favorite:
            t = DARK_THEME
            self._btn_favorite.configure(
                text="*" if self.is_favorite else "+",
                fg=t.warning if self.is_favorite else t.text_secondary,
            )

    def _open_details(self):
        if self.on_details:
            self.on_details(self.game)
            return
        self.on_play(self.game)

    def _on_enter(self, _=None):
        t = DARK_THEME
        self.configure(bg=t.bg_hover)
        for child in self.winfo_children():
            if isinstance(child, (tk.Label, tk.Frame)):
                child.configure(bg=t.bg_hover)

    def _on_leave(self, _=None):
        t = DARK_THEME
        self.configure(bg=t.bg_card)
        for child in self.winfo_children():
            if isinstance(child, (tk.Label, tk.Frame)):
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
