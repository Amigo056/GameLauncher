"""View: Página de jogos instalados localmente."""
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
import threading

from src.application.use_cases.scan_library import ScanLibraryUseCase
from src.domain.entities.game import Game
from src.domain.entities.emulator import Emulator
from src.application.use_cases.launch_game import LaunchGameUseCase
from src.infrastructure.system.process_manager import SubprocessProcessManager
from src.presentation.widgets.game_card import GameCard, COVER_DIMENSIONS, DEFAULT_COVER_SIZE


class InstalledGamesPage:
    """Mostra jogos locais com grid de capas e lançamento."""

    def __init__(
        self,
        parent: tk.Widget,
        root_window: tk.Tk,
        emulator: Emulator,
        scan_use_case: ScanLibraryUseCase,
        on_back: callable,
        on_config_controller: callable = None,
    ):
        self.frame = tk.Frame(parent, bg='#1e1e1e')

        self.root          = root_window
        self.emulator      = emulator
        self.scan_use_case = scan_use_case
        self.on_back       = on_back
        self.on_config_controller = on_config_controller

        self.games: list[Game] = []
        self._image_cache: dict = {}   # partilhado com todos os GameCards

        self._build_ui()
        self._load_games()

    # ─────────────────────────────────────────────
    # UI BUILD
    # ─────────────────────────────────────────────

    def _build_ui(self):
        # ── Header ───────────────────────────────
        header = tk.Frame(self.frame, bg='#1e1e1e', padx=20, pady=15)
        header.pack(fill='x')

        tk.Button(
            header, text="← Voltar",
            font=('Segoe UI', 11), bg='#333333', fg='white',
            relief='flat', cursor='hand2',
            command=self.on_back,
        ).pack(side='left')

        tk.Label(
            header,
            text=f"Meus Jogos — {self.emulator.name}",
            bg='#1e1e1e', fg='white',
            font=('Segoe UI', 18, 'bold'),
        ).pack(side='left', padx=20)

        self.lbl_count = tk.Label(
            header, text="",
            bg='#1e1e1e', fg='#888888',
            font=('Segoe UI', 11),
        )
        self.lbl_count.pack(side='right')

        tk.Button(
            header, text="🔄 Atualizar",
            font=('Segoe UI', 10), bg='#2d2d2d', fg='white',
            relief='flat', cursor='hand2',
            command=self._refresh,
        ).pack(side='right', padx=6)

        if self.emulator.id == "mupen64plus":
            tk.Button(
                header, text="🎮 Controlos",
                font=('Segoe UI', 11), bg='#2d2d2d', fg='white',
                relief='flat', cursor='hand2',
                command=self._on_config_controller,
            ).pack(side='right', padx=10)

        # ── Barra de pesquisa ─────────────────────
        search_bar = tk.Frame(self.frame, bg='#1e1e1e', padx=20, pady=5)
        search_bar.pack(fill='x')

        self._search_var = tk.StringVar()
        self._search_var.trace_add('write', self._on_search)

        tk.Label(
            search_bar, text="🔍", bg='#1e1e1e', fg='#888888',
            font=('Segoe UI', 13),
        ).pack(side='left')

        tk.Entry(
            search_bar, textvariable=self._search_var,
            bg='#2d2d2d', fg='white', insertbackground='white',
            relief='flat', font=('Segoe UI', 11), width=30,
        ).pack(side='left', padx=8, ipady=4)

        # ── Área de scroll ────────────────────────
        # O outer frame NÃO tem padx — assim o scrollbar fica colado à borda.
        # O padding esquerdo é aplicado só ao canvas.
        outer = tk.Frame(self.frame, bg='#1e1e1e')
        outer.pack(fill='both', expand=True, pady=(5, 0))

        self.canvas = tk.Canvas(outer, bg='#1e1e1e', highlightthickness=0)
        scrollbar   = ttk.Scrollbar(outer, orient="vertical", command=self.canvas.yview)

        self.grid_frame = tk.Frame(self.canvas, bg='#1e1e1e')
        self.grid_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.grid_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)

        # IMPORTANTE: scrollbar PRIMEIRO → fica colada à direita absoluta da janela
        scrollbar.pack(side="right", fill="y")
        # Canvas preenche o resto, com padding só à esquerda
        self.canvas.pack(side="left", fill="both", expand=True, padx=(20, 0))

        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    # ─────────────────────────────────────────────
    # ESTADOS VISUAIS
    # ─────────────────────────────────────────────

    def _clear_grid(self):
        for widget in self.grid_frame.winfo_children():
            widget.destroy()

    def _show_loading(self):
        self._clear_grid()
        tk.Label(
            self.grid_frame,
            text="⏳  A carregar jogos…",
            bg='#1e1e1e', fg='#888888',
            font=('Segoe UI', 14),
        ).grid(row=0, column=0, pady=60, padx=40)
        self.lbl_count.config(text="A carregar…")

    def _show_empty_state(self):
        self._clear_grid()
        tk.Label(
            self.grid_frame,
            text="📂  Nenhum jogo encontrado",
            bg='#1e1e1e', fg='#888888',
            font=('Segoe UI', 14, 'bold'), justify='center',
        ).grid(row=0, column=0, pady=(60, 10), padx=40)
        tk.Label(
            self.grid_frame, text="Coloca as ROMs na pasta:",
            bg='#1e1e1e', fg='#666666', font=('Segoe UI', 11),
        ).grid(row=1, column=0)
        tk.Label(
            self.grid_frame, text=str(self.emulator.roms_directory),
            bg='#1e1e1e', fg='#0078d4', font=('Segoe UI', 10, 'bold'),
        ).grid(row=2, column=0, pady=(4, 0))

    # ─────────────────────────────────────────────
    # SCAN ASSÍNCRONO
    # ─────────────────────────────────────────────

    def _scan_worker(self, force: bool):
        """Corre em thread separada — nunca toca na UI."""
        games = (
            self.scan_use_case.force_refresh(self.emulator)
            if force
            else self.scan_use_case.execute(self.emulator)
        )
        self.frame.after(0, lambda: self._on_games_loaded(games))

    def _load_games(self):
        self._show_loading()
        threading.Thread(target=self._scan_worker, args=(False,), daemon=True).start()

    def _refresh(self):
        """Botão Atualizar — invalida cache antes de re-escanear."""
        self._image_cache.clear()
        self._show_loading()
        threading.Thread(target=self._scan_worker, args=(True,), daemon=True).start()

    def _on_games_loaded(self, games: list[Game]):
        self.games = games
        count = len(games)
        self.lbl_count.config(text=f"{count} jogo{'s' if count != 1 else ''}")

        if not games:
            self._show_empty_state()
            return

        # after(100) garante que o canvas já tem largura real ao calcular colunas
        self.frame.after(100, lambda: self._render_grid(games))

    # ─────────────────────────────────────────────
    # PESQUISA
    # ─────────────────────────────────────────────

    def _on_search(self, *_):
        query = self._search_var.get().lower().strip()
        if not self.games:
            return

        filtered = (
            [g for g in self.games if query in g.title.lower()]
            if query else self.games
        )
        total = len(self.games)
        shown = len(filtered)

        self.lbl_count.config(
            text=(
                f"{shown} de {total} jogo{'s' if total != 1 else ''}"
                if query
                else f"{total} jogo{'s' if total != 1 else ''}"
            )
        )
        self.frame.after(0, lambda: self._render_grid(filtered))

    # ─────────────────────────────────────────────
    # GRID
    # ─────────────────────────────────────────────

    def _render_grid(self, games: list[Game]):
        self._clear_grid()

        if not games:
            tk.Label(
                self.grid_frame,
                text="Nenhum resultado para essa pesquisa.",
                bg='#1e1e1e', fg='#666666', font=('Segoe UI', 12),
            ).grid(row=0, column=0, pady=40, padx=40)
            return

        # Colunas dinâmicas — winfo_width() tem valor real graças ao after(100)
        self.canvas.update_idletasks()
        available_width = self.canvas.winfo_width()
        if available_width < 10:
            available_width = 900

        cover_w, cover_h = COVER_DIMENSIONS.get(self.emulator.id, DEFAULT_COVER_SIZE)

        # Largura do card = cover + padding interno (8px cada lado) + gap
        card_slot = cover_w + 40
        cols      = max(2, available_width // card_slot)

        for idx, game in enumerate(games):
            card = GameCard(
                parent=self.grid_frame,
                game=game,
                cover_w=cover_w,
                cover_h=cover_h,
                on_play=self._on_play,
                image_cache=self._image_cache,
                frame_ref=self.frame,
            )
            card.grid(
                row=idx // cols, column=idx % cols,
                padx=12, pady=12, sticky='n',
            )

    # ─────────────────────────────────────────────
    # PLAY
    # ─────────────────────────────────────────────

    def _on_play(self, game: Game):
        if not game.rom or not game.rom.exists:
            messagebox.showerror("Erro", "ROM não encontrada!")
            return

        if not messagebox.askyesno("Lançar Jogo", f"Jogar  {game.title}?"):
            return

        self.root.iconify()

        def launch_and_wait():
            try:
                result = LaunchGameUseCase(SubprocessProcessManager()).execute(
                    game, self.emulator, wait_for_close=True
                )
                if not result.success:
                    self.frame.after(0, lambda: messagebox.showerror(
                        "Erro", f"Falha ao lançar:\n{result.error_message}"
                    ))
            except Exception as e:
                self.frame.after(0, lambda: messagebox.showerror("Erro", str(e)))
            finally:
                self.frame.after(0, self.root.deiconify)

        threading.Thread(target=launch_and_wait, daemon=True).start()

    # ─────────────────────────────────────────────
    # HELPERS
    # ─────────────────────────────────────────────

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _on_config_controller(self):
        if self.on_config_controller:
            self.on_config_controller(self.emulator.id)

    def destroy(self):
        self.canvas.unbind_all("<MouseWheel>")
        self.frame.place_forget()