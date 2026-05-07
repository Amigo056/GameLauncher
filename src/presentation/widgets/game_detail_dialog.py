"""Popup de detalhes de um jogo instalado."""
import tkinter as tk
from datetime import datetime
from tkinter import messagebox, ttk
from typing import Callable

from PIL import Image, ImageTk

from src.application.services.save_manager import SaveManager, SaveSlot
from src.application.services.session_tracker import SessionTracker
from src.application.services.settings_service import SettingsService
from src.domain.entities.emulator import Emulator
from src.domain.entities.game import Game
from src.domain.entities.play_session import PlaySession
from src.presentation.theme import DARK_THEME, font, mono_font
from src.presentation.widgets.toast import Toast


class GameDetailDialog:
    """Modal com capa, informacao, estatisticas, historico e saves."""

    COVER_SIZE = (280, 190)

    def __init__(
        self,
        root_window: tk.Tk,
        game: Game,
        emulator: Emulator,
        session_tracker: SessionTracker,
        save_manager: SaveManager,
        settings_service: SettingsService,
        on_play: Callable[[Game], None],
        on_favorite_changed: Callable[[Game, bool], None] | None = None,
    ):
        self.root = root_window
        self.game = game
        self.emulator = emulator
        self.session_tracker = session_tracker
        self.save_manager = save_manager
        self.settings_service = settings_service
        self.on_play = on_play
        self.on_favorite_changed = on_favorite_changed

        self.window = tk.Toplevel(root_window)
        self.window.title(game.title)
        self.window.configure(bg=DARK_THEME.bg_primary)
        self.window.transient(root_window)
        self.window.grab_set()
        self.window.protocol("WM_DELETE_WINDOW", self.destroy)
        self.window.minsize(760, 520)

        self._cover_photo: ImageTk.PhotoImage | None = None
        self._favorite_button: tk.Button | None = None
        self._saves_body: tk.Frame | None = None
        self._history_body: tk.Frame | None = None

        self._build_ui()
        self._center_window()

    def _build_ui(self):
        t = DARK_THEME

        shell = tk.Frame(self.window, bg=t.bg_primary)
        shell.pack(fill='both', expand=True)

        header = tk.Frame(shell, bg=t.bg_primary, padx=18, pady=14)
        header.pack(fill='x')

        tk.Label(
            header,
            text=self.game.title,
            bg=t.bg_primary,
            fg=t.text_primary,
            font=font(t, "font_size_2xl", bold=True),
        ).pack(side='left', fill='x', expand=True)

        tk.Button(
            header,
            text="Fechar",
            bg=t.bg_tertiary,
            fg=t.text_primary,
            activebackground=t.bg_hover,
            activeforeground=t.text_primary,
            relief='flat',
            cursor='hand2',
            command=self.destroy,
        ).pack(side='right')

        outer = tk.Frame(shell, bg=t.bg_primary)
        outer.pack(fill='both', expand=True, padx=18, pady=(0, 18))

        canvas = tk.Canvas(outer, bg=t.bg_primary, highlightthickness=0)
        scrollbar = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        self.content = tk.Frame(canvas, bg=t.bg_primary)
        self.content.bind(
            "<Configure>",
            lambda _event: canvas.configure(scrollregion=canvas.bbox("all")),
        )
        canvas.create_window((0, 0), window=self.content, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        main = tk.Frame(self.content, bg=t.bg_primary)
        main.pack(fill='both', expand=True)
        main.grid_columnconfigure(1, weight=1)

        left = tk.Frame(main, bg=t.bg_primary)
        left.grid(row=0, column=0, sticky='nw', padx=(0, 18))

        right = tk.Frame(main, bg=t.bg_primary)
        right.grid(row=0, column=1, sticky='nsew')

        self._build_cover_panel(left)
        self._build_stats_section(right)
        self._build_history_section(right)
        self._build_info_section(right)
        self._build_saves_section(right)

    def _build_cover_panel(self, parent: tk.Widget):
        t = DARK_THEME
        panel = tk.Frame(parent, bg=t.bg_secondary, padx=16, pady=16)
        panel.pack(fill='x')

        cover = tk.Label(
            panel,
            bg=t.bg_tertiary,
            fg=t.text_disabled,
            text="Sem capa",
            width=self.COVER_SIZE[0] // 9,
            height=self.COVER_SIZE[1] // 18,
            font=font(t, "font_size_lg", bold=True),
        )
        cover.pack()
        self._load_cover(cover)

        tk.Button(
            panel,
            text="Jogar",
            font=font(t, "font_size_lg", bold=True),
            bg=t.accent,
            fg=t.text_primary,
            activebackground=t.accent_hover,
            activeforeground=t.text_primary,
            relief='flat',
            cursor='hand2',
            width=22,
            pady=8,
            command=self._play,
        ).pack(fill='x', pady=(16, 8))

        self._favorite_button = tk.Button(
            panel,
            text=self._favorite_button_text(),
            bg=t.bg_tertiary,
            fg=t.text_primary,
            activebackground=t.bg_hover,
            activeforeground=t.text_primary,
            relief='flat',
            cursor='hand2',
            width=22,
            pady=6,
            command=self._toggle_favorite,
        )
        self._favorite_button.pack(fill='x')

    def _build_stats_section(self, parent: tk.Widget):
        section = self._section(parent, "Estatisticas")
        stats = self.session_tracker.get_game_stats(self.game.id)
        if not stats:
            self._muted_label(section, "Ainda sem sessoes registadas.")
            return

        rows = [
            ("Tempo total", self._format_duration(int(stats.total_playtime_seconds))),
            ("Sessoes", str(stats.total_sessions)),
            ("Ultima vez", self._format_datetime(stats.last_played)),
            ("Media", self._format_duration(int(stats.average_session_seconds))),
        ]
        self._detail_rows(section, rows)

    def _build_history_section(self, parent: tk.Widget):
        section = self._section(parent, "Historico")
        self._history_body = tk.Frame(section, bg=DARK_THEME.bg_secondary)
        self._history_body.pack(fill='x')
        sessions = self._sessions_for_game(limit=6)
        if not sessions:
            self._muted_label(self._history_body, "Ainda nao ha historico para este jogo.")
            return

        for session in sessions:
            started = self._format_datetime(session.started_at)
            duration = self._format_duration(int(session.duration_seconds or 0))
            self._muted_label(self._history_body, f"{started} - {duration}")

    def _build_info_section(self, parent: tk.Widget):
        section = self._section(parent, "Informacao")
        platform_value = getattr(self.emulator.platform, "value", str(self.emulator.platform))
        rows = [
            ("ID", self.game.id),
            ("Titulo", self.game.title),
            ("Regiao", self.game.region.name),
            ("Emulador", self.emulator.name),
            ("Plataforma", platform_value),
        ]

        if self.game.rom:
            rows.extend(
                [
                    ("Ficheiro", self.game.rom.file_path.name),
                    ("Pasta", str(self.game.rom.file_path.parent)),
                    ("Tamanho", self._format_size(self.game.rom.file_size)),
                    ("Extensao", self.game.rom.extension),
                ]
            )

        self._detail_rows(section, rows, mono_labels={"ID", "Pasta"})

    def _build_saves_section(self, parent: tk.Widget):
        section = self._section(parent, "Saves")
        toolbar = tk.Frame(section, bg=DARK_THEME.bg_secondary)
        toolbar.pack(fill='x', pady=(0, 8))

        tk.Button(
            toolbar,
            text="Criar backup",
            bg=DARK_THEME.bg_tertiary,
            fg=DARK_THEME.text_primary,
            activebackground=DARK_THEME.bg_hover,
            activeforeground=DARK_THEME.text_primary,
            relief='flat',
            cursor='hand2',
            command=self._create_manual_backup,
        ).pack(side='left')

        self._saves_body = tk.Frame(section, bg=DARK_THEME.bg_secondary)
        self._saves_body.pack(fill='x')
        self._render_saves_body()

    def _render_saves_body(self):
        if not self._saves_body:
            return
        for child in self._saves_body.winfo_children():
            child.destroy()

        current_saves = self.save_manager.list_current_saves(self.game)
        slots = self.save_manager.list_save_slots(self.game) if self.game.rom else []

        self._muted_label(
            self._saves_body,
            f"{len(current_saves)} ficheiro(s) de save atual encontrado(s).",
        )

        if not slots:
            self._muted_label(self._saves_body, "Ainda nao existem backups guardados.")
            return

        for slot in slots[:8]:
            self._save_slot_row(self._saves_body, slot)

    def _save_slot_row(self, parent: tk.Widget, slot: SaveSlot):
        t = DARK_THEME
        row = tk.Frame(parent, bg=t.bg_secondary)
        row.pack(fill='x', pady=3)

        label = (
            f"{slot.name} - {self._format_datetime(slot.created_at)} - "
            f"{self._format_size(slot.file_size)}"
        )
        tk.Label(
            row,
            text=label,
            bg=t.bg_secondary,
            fg=t.text_primary,
            font=font(t, "font_size_sm"),
            anchor='w',
        ).pack(side='left', fill='x', expand=True)

        tk.Button(
            row,
            text="Restaurar",
            bg=t.bg_tertiary,
            fg=t.text_primary,
            activebackground=t.bg_hover,
            activeforeground=t.text_primary,
            relief='flat',
            cursor='hand2',
            command=lambda current=slot: self._restore_slot(current),
        ).pack(side='right', padx=(6, 0))

        tk.Button(
            row,
            text="Eliminar",
            bg=t.error_bg,
            fg=t.text_primary,
            activebackground=t.error,
            activeforeground=t.text_primary,
            relief='flat',
            cursor='hand2',
            command=lambda current=slot: self._delete_slot(current),
        ).pack(side='right', padx=(6, 0))

    def _section(self, parent: tk.Widget, title: str) -> tk.Frame:
        t = DARK_THEME
        frame = tk.Frame(parent, bg=t.bg_secondary, padx=16, pady=12)
        frame.pack(fill='x', pady=(0, 12))
        tk.Label(
            frame,
            text=title,
            bg=t.bg_secondary,
            fg=t.text_primary,
            font=font(t, "font_size_lg", bold=True),
        ).pack(anchor='w', pady=(0, 8))
        return frame

    def _detail_rows(
        self,
        parent: tk.Widget,
        rows: list[tuple[str, str]],
        mono_labels: set[str] | None = None,
    ):
        t = DARK_THEME
        mono_labels = mono_labels or set()
        for label, value in rows:
            row = tk.Frame(parent, bg=t.bg_secondary)
            row.pack(fill='x', pady=3)
            tk.Label(
                row,
                text=f"{label}:",
                bg=t.bg_secondary,
                fg=t.text_secondary,
                font=font(t, "font_size_md"),
                width=12,
                anchor='w',
            ).pack(side='left')
            tk.Label(
                row,
                text=str(value),
                bg=t.bg_secondary,
                fg=t.text_primary,
                font=mono_font(t, "font_size_sm") if label in mono_labels else font(t),
                anchor='w',
                justify='left',
                wraplength=560,
            ).pack(side='left', padx=(8, 0), fill='x', expand=True)

    def _muted_label(self, parent: tk.Widget, text: str):
        t = DARK_THEME
        tk.Label(
            parent,
            text=text,
            bg=t.bg_secondary,
            fg=t.text_secondary,
            font=font(t, "font_size_md"),
            anchor='w',
            justify='left',
            wraplength=640,
        ).pack(fill='x', pady=2)

    def _load_cover(self, label: tk.Label):
        cover_path = (
            self.game.cover.local_path
            if self.game.cover and self.game.cover.is_local
            else None
        )
        if not cover_path or not cover_path.exists():
            return

        try:
            img = Image.open(cover_path).convert("RGBA")
            orig_w, orig_h = img.size
            ratio = min(self.COVER_SIZE[0] / orig_w, self.COVER_SIZE[1] / orig_h)
            new_w = max(1, int(orig_w * ratio))
            new_h = max(1, int(orig_h * ratio))
            img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)

            bg = Image.new("RGBA", self.COVER_SIZE, (51, 51, 51, 255))
            bg.paste(
                img,
                ((self.COVER_SIZE[0] - new_w) // 2, (self.COVER_SIZE[1] - new_h) // 2),
                img,
            )
            self._cover_photo = ImageTk.PhotoImage(bg)
            label.configure(
                image=self._cover_photo,
                text="",
                width=self.COVER_SIZE[0],
                height=self.COVER_SIZE[1],
            )
        except Exception:
            return

    def _play(self):
        self.destroy()
        self.on_play(self.game)

    def _toggle_favorite(self):
        is_favorite = self.settings_service.toggle_favorite_game(
            self.emulator.id,
            self.game.id,
        )
        if self._favorite_button:
            self._favorite_button.configure(text=self._favorite_button_text())

        if self.on_favorite_changed:
            self.on_favorite_changed(self.game, is_favorite)

        Toast.show(
            self.root,
            f"{self.game.title}: {'favorito' if is_favorite else 'removido dos favoritos'}",
            level="success" if is_favorite else "info",
            duration=1800,
        )

    def _create_manual_backup(self):
        if not self.save_manager.list_current_saves(self.game):
            Toast.show(
                self.root,
                "Nao encontrei saves atuais para criar backup.",
                level="warning",
                duration=3000,
            )
            return

        slot = self.save_manager.create_save_slot(self.game, "manual")
        self._render_saves_body()
        Toast.show(
            self.root,
            f"Backup criado: {self._format_size(slot.file_size)}",
            level="success",
            duration=2500,
        )

    def _restore_slot(self, slot: SaveSlot):
        confirmed = messagebox.askyesno(
            "Restaurar backup",
            f"Restaurar o backup '{slot.name}' para este jogo?",
            parent=self.window,
        )
        if not confirmed:
            return

        if self.save_manager.restore_save_slot(self.game, slot):
            self._render_saves_body()
            Toast.show(self.root, "Backup restaurado.", level="success", duration=2500)
        else:
            Toast.show(self.root, "Nao foi possivel restaurar o backup.", level="error")

    def _delete_slot(self, slot: SaveSlot):
        confirmed = messagebox.askyesno(
            "Eliminar backup",
            f"Eliminar permanentemente o backup '{slot.name}'?",
            parent=self.window,
        )
        if not confirmed:
            return

        if self.save_manager.delete_save_slot(slot):
            self._render_saves_body()
            Toast.show(self.root, "Backup eliminado.", level="success", duration=2200)
        else:
            Toast.show(self.root, "Nao foi possivel eliminar o backup.", level="error")

    def _sessions_for_game(self, limit: int) -> list[PlaySession]:
        if hasattr(self.session_tracker, "get_sessions_for_game"):
            return self.session_tracker.get_sessions_for_game(self.game.id, limit=limit)
        return []

    def _favorite_button_text(self) -> str:
        if self.settings_service.is_favorite_game(self.emulator.id, self.game.id):
            return "Remover favorito"
        return "Adicionar favorito"

    def _format_duration(self, seconds: int) -> str:
        return self.session_tracker._format_duration(seconds)

    def _format_size(self, size_bytes: int | float) -> str:
        size = float(size_bytes or 0)
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"

    def _format_datetime(self, value: datetime | None) -> str:
        if value is None:
            return "Nunca"
        return value.strftime("%d/%m/%Y %H:%M")

    def _center_window(self):
        self.window.update_idletasks()
        width = min(940, max(780, self.root.winfo_width() - 160))
        height = min(680, max(540, self.root.winfo_height() - 120))
        x = self.root.winfo_rootx() + max(20, (self.root.winfo_width() - width) // 2)
        y = self.root.winfo_rooty() + max(20, (self.root.winfo_height() - height) // 2)
        self.window.geometry(f"{width}x{height}+{x}+{y}")

    def destroy(self):
        try:
            if self.window.winfo_exists():
                self.window.grab_release()
                self.window.destroy()
        except tk.TclError:
            pass
