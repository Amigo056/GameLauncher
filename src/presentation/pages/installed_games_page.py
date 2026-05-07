"""View: Página de jogos instalados localmente."""
import tkinter as tk
from tkinter import ttk
import threading

from src.application.use_cases.scan_library import ScanLibraryUseCase, ScanProgress
from src.domain.entities.game import Game
from src.domain.entities.emulator import Emulator
from src.domain.value_objects.graphics_profile import GraphicsProfile, GraphicsProfileLevel
from src.infrastructure.container import container
from src.presentation.widgets.game_card import GameCard, COVER_DIMENSIONS, DEFAULT_COVER_SIZE
from src.presentation.widgets.toast import Toast
from src.presentation.theme import DARK_THEME, font


class InstalledGamesPage:
    """Mostra jogos locais com grid de capas, lançamento e estatísticas."""

    def __init__(
        self,
        parent: tk.Widget,
        root_window: tk.Tk,
        emulator: Emulator,
        scan_use_case: ScanLibraryUseCase,
        on_back: callable,
        on_config_controller: callable = None,
    ):
        t = DARK_THEME
        self.frame = tk.Frame(parent, bg=t.bg_primary)

        self.root          = root_window
        self.emulator      = emulator
        self.scan_use_case = scan_use_case
        self.on_back       = on_back
        self.on_config_controller = on_config_controller

        self.games: list[Game] = []
        self._image_cache: dict = {}
        self._session_tracker = container.session_tracker
        self._settings_service = container.settings_service
        self._graphics_registry = container.graphics_profile_registry
        self._graphics_profiles: dict[str, GraphicsProfile] = {}

        self._build_ui()
        self._load_games()

    def _build_ui(self):
        t = DARK_THEME

        header = tk.Frame(self.frame, bg=t.bg_primary, padx=20, pady=15)
        header.pack(fill='x')

        tk.Button(
            header, text="← Voltar",
            font=font(t, "font_size_md"), bg=t.bg_tertiary, fg=t.text_primary,
            relief='flat', cursor='hand2',
            command=self.on_back,
        ).pack(side='left')

        tk.Label(
            header,
            text=f"Meus Jogos — {self.emulator.name}",
            bg=t.bg_primary, fg=t.text_primary,
            font=font(t, "font_size_2xl", bold=True),
        ).pack(side='left', padx=20)

        self._progress_frame = tk.Frame(header, bg=t.bg_primary)
        self._progress_frame.pack(side='right', padx=10)

        self._progress_bar = ttk.Progressbar(
            self._progress_frame,
            orient='horizontal',
            mode='determinate',
            length=150,
            maximum=100,
        )
        self._progress_bar.pack(side='left')

        self._progress_label = tk.Label(
            self._progress_frame,
            text="",
            bg=t.bg_primary,
            fg=t.text_secondary,
            font=font(t, "font_size_sm"),
        )
        self._progress_label.pack(side='left', padx=(8, 0))

        self._hide_progress()

        self.lbl_count = tk.Label(
            header, text="",
            bg=t.bg_primary, fg=t.text_secondary,
            font=font(t, "font_size_md"),
        )
        self.lbl_count.pack(side='right', padx=6)

        tk.Button(
            header, text="🔄 Atualizar",
            font=font(t, "font_size_md"), bg=t.bg_card, fg=t.text_primary,
            relief='flat', cursor='hand2',
            command=self._refresh,
        ).pack(side='right', padx=6)

        if self.emulator.id == "mupen64plus":
            tk.Button(
                header, text="🎮 Controlos",
                font=font(t, "font_size_md"), bg=t.bg_card, fg=t.text_primary,
                relief='flat', cursor='hand2',
                command=self._on_config_controller,
            ).pack(side='right', padx=10)

        search_bar = tk.Frame(self.frame, bg=t.bg_primary, padx=20, pady=5)
        search_bar.pack(fill='x')

        self._search_var = tk.StringVar()
        self._search_var.trace_add('write', self._on_search)

        tk.Label(
            search_bar, text="🔍", bg=t.bg_primary, fg=t.text_secondary,
            font=font(t, "font_size_lg"),
        ).pack(side='left')

        tk.Entry(
            search_bar, textvariable=self._search_var,
            bg=t.bg_card, fg=t.text_primary, insertbackground=t.text_primary,
            relief='flat', font=font(t, "font_size_md"), width=30,
        ).pack(side='left', padx=8, ipady=4)

        self._build_graphics_selector(search_bar)

        outer = tk.Frame(self.frame, bg=t.bg_primary)
        outer.pack(fill='both', expand=True, pady=(5, 0))

        self.canvas = tk.Canvas(outer, bg=t.bg_primary, highlightthickness=0)
        scrollbar   = ttk.Scrollbar(outer, orient="vertical", command=self.canvas.yview)

        self.grid_frame = tk.Frame(self.canvas, bg=t.bg_primary)
        self.grid_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.grid_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True, padx=(20, 0))

        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _build_graphics_selector(self, parent: tk.Widget):
        """Cria seletor de perfil grafico por emulador."""
        t = DARK_THEME
        profiles = self._graphics_registry.get_profiles(self.emulator.id)
        self._graphics_profiles = {profile.level.label: profile for profile in profiles}

        selected_level = self._settings_service.get_graphics_profile(self.emulator.id)
        selected_label = selected_level.label
        if selected_label not in self._graphics_profiles:
            selected_label = GraphicsProfileLevel.BALANCED.label

        graphics_frame = tk.Frame(parent, bg=t.bg_primary)
        graphics_frame.pack(side='right')

        tk.Label(
            graphics_frame,
            text="Gráficos",
            bg=t.bg_primary,
            fg=t.text_secondary,
            font=font(t, "font_size_sm"),
        ).pack(side='left', padx=(0, 6))

        self._graphics_profile_var = tk.StringVar(value=selected_label)
        menu = tk.OptionMenu(
            graphics_frame,
            self._graphics_profile_var,
            *self._graphics_profiles.keys(),
            command=self._on_graphics_profile_changed,
        )
        menu.configure(
            bg=t.bg_card,
            fg=t.text_primary,
            activebackground=t.bg_hover,
            activeforeground=t.text_primary,
            relief='flat',
            highlightthickness=0,
            cursor='hand2',
            font=font(t, "font_size_sm"),
        )
        menu["menu"].configure(
            bg=t.bg_card,
            fg=t.text_primary,
            activebackground=t.bg_hover,
            activeforeground=t.text_primary,
            font=font(t, "font_size_sm"),
        )
        menu.pack(side='left')

    def _on_graphics_profile_changed(self, label: str):
        """Persiste selecao de perfil grafico."""
        profile = self._graphics_profiles.get(label)
        if not profile:
            return

        self._settings_service.save_graphics_profile(
            self.emulator.id,
            profile.level,
        )
        Toast.show(
            self.root,
            f"Perfil gráfico: {profile.level.label}",
            level="success",
            duration=1800,
        )

    def _selected_graphics_profile(self) -> GraphicsProfile:
        """Retorna o perfil grafico selecionado na UI."""
        label = self._graphics_profile_var.get()
        profile = self._graphics_profiles.get(label)
        if profile:
            return profile

        level = self._settings_service.get_graphics_profile(self.emulator.id)
        return self._graphics_registry.get_profile(self.emulator.id, level)

    def _show_progress(self):
        self._progress_frame.pack(side='right', padx=10, before=self.lbl_count)
        self._progress_bar['value'] = 0
        self._progress_label.config(text="0%")

    def _hide_progress(self):
        self._progress_frame.pack_forget()

    def _update_progress(self, progress: ScanProgress):
        def _update():
            self._progress_bar['value'] = progress.percent
            self._progress_label.config(
                text=f"{progress.percent:.0f}% ({progress.completed}/{progress.total})"
            )
        self.frame.after(0, _update)

    def _get_game_stats(self, game: Game) -> str:
        """Retorna estatísticas formatadas para mostrar no card."""
        try:
            playtime = self._session_tracker.get_total_playtime(game.id)
            sessions = self._session_tracker.get_session_count(game.id)
            if sessions > 0:
                return f"⏱ {playtime} • {sessions}x"
        except Exception:
            pass
        return ""

    def _clear_grid(self):
        for widget in self.grid_frame.winfo_children():
            widget.destroy()

    def _show_loading(self):
        t = DARK_THEME
        self._clear_grid()
        tk.Label(
            self.grid_frame,
            text="⏳  A carregar jogos…",
            bg=t.bg_primary, fg=t.text_secondary,
            font=font(t, "font_size_lg"),
        ).grid(row=0, column=0, pady=60, padx=40)
        self.lbl_count.config(text="A carregar…")

    def _show_empty_state(self):
        t = DARK_THEME
        self._clear_grid()
        tk.Label(
            self.grid_frame,
            text="📂  Nenhum jogo encontrado",
            bg=t.bg_primary, fg=t.text_secondary,
            font=font(t, "font_size_lg", bold=True), justify='center',
        ).grid(row=0, column=0, pady=(60, 10), padx=40)
        tk.Label(
            self.grid_frame, text="Coloca as ROMs na pasta:",
            bg=t.bg_primary, fg=t.text_disabled, font=font(t, "font_size_md"),
        ).grid(row=1, column=0)
        tk.Label(
            self.grid_frame, text=str(self.emulator.roms_directory),
            bg=t.bg_primary, fg=t.accent, font=font(t, "font_size_sm", bold=True),
        ).grid(row=2, column=0, pady=(4, 0))

    def _scan_worker(self, force: bool):
        try:
            games = (
                self.scan_use_case.force_refresh(
                    self.emulator,
                    progress_callback=self._update_progress
                )
                if force
                else self.scan_use_case.execute(
                    self.emulator,
                    progress_callback=self._update_progress
                )
            )
            self.frame.after(0, lambda: self._on_games_loaded(games))
        except Exception as e:
            self.frame.after(0, lambda: self._on_scan_error(str(e)))

    def _load_games(self):
        self._show_progress()
        self._show_loading()
        threading.Thread(target=self._scan_worker, args=(False,), daemon=True).start()

    def _refresh(self):
        self._image_cache.clear()
        self._show_progress()
        self._show_loading()
        threading.Thread(target=self._scan_worker, args=(True,), daemon=True).start()

    def _on_games_loaded(self, games: list[Game]):
        t = DARK_THEME
        self.games = games
        count = len(games)
        self.lbl_count.config(text=f"{count} jogo{'s' if count != 1 else ''}")
        self._hide_progress()

        if not games:
            self._show_empty_state()
            return

        self.frame.after(100, lambda: self._render_grid(games))

    def _on_scan_error(self, error_msg: str):
        self._hide_progress()
        self._clear_grid()
        t = DARK_THEME
        tk.Label(
            self.grid_frame,
            text=f"❌ Erro ao carregar jogos:\n{error_msg}",
            bg=t.bg_primary, fg=t.error,
            font=font(t, "font_size_md"), justify='center',
        ).grid(row=0, column=0, pady=60, padx=40)
        self.lbl_count.config(text="Erro")

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

    def _render_grid(self, games: list[Game]):
        self._clear_grid()

        if not games:
            t = DARK_THEME
            tk.Label(
                self.grid_frame,
                text="Nenhum resultado para essa pesquisa.",
                bg=t.bg_primary, fg=t.text_disabled, font=font(t, "font_size_md"),
            ).grid(row=0, column=0, pady=40, padx=40)
            return

        self.canvas.update_idletasks()
        available_width = self.canvas.winfo_width()
        if available_width < 10:
            available_width = 900

        cover_w, cover_h = COVER_DIMENSIONS.get(self.emulator.id, DEFAULT_COVER_SIZE)

        card_slot = cover_w + 40
        cols      = max(2, available_width // card_slot)

        for idx, game in enumerate(games):
            stats_text = self._get_game_stats(game)

            card = GameCard(
                parent=self.grid_frame,
                game=game,
                cover_w=cover_w,
                cover_h=cover_h,
                on_play=self._on_play,
                image_cache=self._image_cache,
                frame_ref=self.frame,
                stats_text=stats_text,
            )
            card.grid(
                row=idx // cols, column=idx % cols,
                padx=12, pady=12, sticky='n',
            )

    def _on_play(self, game: Game):
        if not game.rom or not game.rom.exists:
            Toast.show(
                self.root,
                "ROM não encontrada!",
                level="error",
                duration=4000
            )
            return

        Toast.show(
            self.root,
            f"A lançar {game.title}…",
            level="info",
            duration=2000
        )

        graphics_profile = self._selected_graphics_profile()
        self.root.iconify()

        def launch_and_wait():
            error_msg = None
            result = None
            
            try:
                container.create_apply_graphics_profile_use_case().execute(
                    self.emulator,
                    graphics_profile,
                )

                result = container.create_launch_use_case().execute(
                    game, self.emulator, wait_for_close=True
                )

                if not result.success:
                    error_msg = f"Falha ao lançar:\n{result.error_message}"
            except Exception as exc:
                error_msg = f"Erro: {str(exc)}"
                import traceback
                traceback.print_exc()
            finally:
                # ✅ Closure segura - captura valores, não referências
                self.frame.after(0, lambda msg=error_msg, res=result: 
                    self._show_launch_result(msg, res, game.title))
                self.frame.after(0, self.root.deiconify)

        threading.Thread(target=launch_and_wait, daemon=True).start()

    def _show_launch_result(self, error_msg: str | None, result, game_title: str):
        """Callback seguro na UI thread."""
        if error_msg:
            Toast.show(
                self.root,
                error_msg,
                level="error",
                duration=5000
            )
        elif result and result.success:
            self._refresh_stats()
            Toast.show(
                self.root,
                f"✅ {game_title} — Sessão: {result.session_duration:.0f}s",
                level="success",
                duration=3000
            )


    def _refresh_stats(self):
        if self.games:
            self._render_grid(self.games)

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _on_config_controller(self):
        if self.on_config_controller:
            self.on_config_controller(self.emulator.id)

    def destroy(self):
        self.canvas.unbind_all("<MouseWheel>")
        self.frame.place_forget()
