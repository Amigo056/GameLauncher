import tkinter as tk

from src.infrastructure.container import container
from src.application.use_cases.scan_library import ScanLibraryUseCase
from src.presentation.pages.controller_config_page import ControllerConfigPage
from src.presentation.pages.home_page import HomePage
from src.presentation.pages.emulator_selection_page import EmulatorSelectionPage
from src.presentation.pages.installed_games_page import InstalledGamesPage
from src.presentation.widgets.game_detail_dialog import GameDetailDialog
from src.domain.entities.emulator import load_emulator_from_json
from src.presentation.widgets.toast import Toast
from src.presentation.theme import DARK_THEME


class AppNavigator:
    """Controlador de navegação entre páginas usando frame stacking."""

    def __init__(self, root: tk.Tk):
        self.root = root

        self.container = tk.Frame(root, bg=DARK_THEME.bg_primary)
        self.container.grid(row=0, column=0, sticky="nsew")
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        self._pages: dict[str, object] = {}
        self._current_page_key: str | None = None
        self._active_detail_dialog: GameDetailDialog | None = None

    # ─────────────────────────────────────────────
    # NAVEGAÇÃO BASE
    # ─────────────────────────────────────────────

    def _show_page(self, page_key: str, page_instance):
        """Mostra uma página, escondendo a anterior."""
        if self._current_page_key and self._current_page_key in self._pages:
            old_page = self._pages[self._current_page_key]
            if hasattr(old_page, 'frame'):
                old_page.frame.place_forget()

        self._pages[page_key] = page_instance
        self._current_page_key = page_key

        if hasattr(page_instance, 'frame'):
            page_instance.frame.place(relx=0, rely=0, relwidth=1, relheight=1)
            page_instance.frame.lift()
            self.container.update_idletasks()

    # ─────────────────────────────────────────────
    # ROTAS
    # ─────────────────────────────────────────────

    def go_home(self):
        if 'home' not in self._pages:
            self._pages['home'] = HomePage(
                parent=self.container,
                on_emulators=self.go_emulators,
                on_settings=self.go_settings
            )
        self._show_page('home', self._pages['home'])

    def go_emulators(self):
        if 'emulators' not in self._pages:
            self._pages['emulators'] = EmulatorSelectionPage(
                parent=self.container,
                on_back=self.go_home,
                on_select_emulator=self.go_emulator_games
            )
        self._show_page('emulators', self._pages['emulators'])

    def go_settings(self):
        Toast.show(
            self.root,
            "Definições em breve…",
            level="info",
            duration=3000
        )

    def go_emulator_games(self, emulator_id: str):
        """Navega para os jogos do emulador. Cria a página uma só vez."""
        try:
            emulator = load_emulator_from_json(emulator_id)
            if not emulator:
                Toast.show(
                    self.root,
                    f"Emulador '{emulator_id}' não encontrado!",
                    level="error",
                    duration=5000
                )
                return

            if not emulator.is_installed:
                Toast.show(
                    self.root,
                    f"{emulator.name} não foi encontrado.\\n"
                    "Verifica os caminhos em config/emulators.json",
                    level="warning",
                    duration=5000
                )
                return

            page_key = f'games_{emulator_id}'

            # Criar apenas se ainda não existe — o botão "Atualizar" dentro
            # da própria página trata de forçar novo scan quando necessário.
            if page_key not in self._pages:
                game_repo = container.game_repo
                cover_service = container.cover_service
                scan_use_case = ScanLibraryUseCase(game_repo, cover_service)

                self._pages[page_key] = InstalledGamesPage(
                    parent=self.container,
                    root_window=self.root,
                    emulator=emulator,
                    scan_use_case=scan_use_case,
                    on_back=self.go_emulators,
                    on_config_controller=self.go_controller_config,
                    on_show_details=lambda game, emu=emulator: self.go_game_detail(emu, game),
                )

            self._show_page(page_key, self._pages[page_key])

        except Exception as e:
            Toast.show(
                self.root,
                f"Erro: {str(e)}",
                level="error",
                duration=5000
            )
            import traceback
            traceback.print_exc()

    def go_game_detail(self, emulator, game):
        """Abre o popup de detalhe do jogo."""
        games_page_key = f'games_{emulator.id}'
        games_page = self._pages.get(games_page_key)

        if self._active_detail_dialog:
            self._active_detail_dialog.destroy()

        def refresh_games_page(_game, _is_favorite):
            if games_page and hasattr(games_page, '_render_current_view'):
                games_page._render_current_view()

        self._active_detail_dialog = GameDetailDialog(
            root_window=self.root,
            game=game,
            emulator=emulator,
            session_tracker=container.session_tracker,
            save_manager=container.save_manager,
            settings_service=container.settings_service,
            on_play=games_page._on_play if games_page else lambda _game: None,
            on_favorite_changed=refresh_games_page,
        )

    def go_controller_config(self, emulator_id: str):
        """Navega para configuração de controlos."""
        page_key = f'config_controller_{emulator_id}'

        if page_key not in self._pages:
            self._pages[page_key] = ControllerConfigPage(
                parent=self.container,
                emulator_id=emulator_id,
                on_back=lambda: self.go_emulator_games(emulator_id)
            )

        self._show_page(page_key, self._pages[page_key])

    def invalidate_games_page(self, emulator_id: str):
        """
        Remove a página de jogos do cache para forçar recriação na próxima visita.
        Útil se o user adicionar/remover ROMs externamente.
        """
        page_key = f'games_{emulator_id}'
        if page_key in self._pages:
            del self._pages[page_key]
