"""Navegação principal da aplicação."""
import tkinter as tk
from tkinter import messagebox
from pathlib import Path

from src.presentation.pages.controller_config_page import ControllerConfigPage
from src.presentation.pages.home_page import HomePage
from src.presentation.pages.emulator_selection_page import EmulatorSelectionPage
from src.presentation.pages.installed_games_page import InstalledGamesPage
from src.infrastructure.persistence.local_game_repo import LocalGameRepository
from src.domain.entities.emulator import load_emulator_from_json

class AppNavigator:
    """Controlador de navegação entre páginas usando frame stacking."""

    def __init__(self, root: tk.Tk):
        self.root = root
        
        # Frame container fixo - nunca é destruído
        self.container = tk.Frame(root, bg='#1e1e1e')
        self.container.grid(row=0, column=0, sticky="nsew")
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)
        
        # Dicionário de páginas criadas (reutilização)
        self._pages: dict[str, object] = {}
        self._current_page_key: str | None = None

    def _show_page(self, page_key: str, page_instance):
        """Mostra uma página, escondendo a anterior."""
        # Esconder página atual
        if self._current_page_key and self._current_page_key in self._pages:
            old_page = self._pages[self._current_page_key]
            if hasattr(old_page, 'frame'):
                old_page.frame.place_forget()  # Esconder com place
        
        # Guardar e mostrar nova página
        self._pages[page_key] = page_instance
        self._current_page_key = page_key
        
        if hasattr(page_instance, 'frame'):
            # Place preenche todo o container
            page_instance.frame.place(relx=0, rely=0, relwidth=1, relheight=1)
            page_instance.frame.lift()
            self.container.update_idletasks()

    def go_home(self):
        """Navega para Home."""
        if 'home' not in self._pages:
            page = HomePage(
                parent=self.container,
                on_emulators=self.go_emulators,
                on_settings=self.go_settings
            )
        else:
            page = self._pages['home']
        
        self._show_page('home', page)

    def go_emulators(self):
        """Navega para seleção de emuladores."""
        if 'emulators' not in self._pages:
            page = EmulatorSelectionPage(
                parent=self.container,
                on_back=self.go_home,
                on_select_emulator=self.go_emulator_games
            )
        else:
            page = self._pages['emulators']
        
        self._show_page('emulators', page)

    def go_settings(self):
        """Navega para definições."""
        messagebox.showinfo("Definições", "Em breve...")

    def go_emulator_games(self, emulator_id: str):
        """Vai direto para os jogos instalados do emulador."""
        try:
            emulator = load_emulator_from_json(emulator_id)
            if not emulator:
                messagebox.showerror("Erro", f"Emulador '{emulator_id}' não encontrado!")
                return

            if not emulator.is_installed:
                messagebox.showwarning(
                    "Emulador não instalado",
                    f"{emulator.name} não foi encontrado.\n"
                    "Verifica os caminhos em config/emulators.json"
                )
                return

            page_key = f'games_{emulator_id}'
            
            # Sempre recriar a página de jogos para atualizar a lista
            game_repo = LocalGameRepository(Path("roms"))
            page = InstalledGamesPage(
                parent=self.container,
                root_window=self.root,
                emulator=emulator,
                game_repo=game_repo,
                on_back=self.go_emulators,
                on_config_controller=self.go_controller_config
            )
            
            self._show_page(page_key, page)

        except Exception as e:
            messagebox.showerror("Erro", str(e))
            import traceback
            traceback.print_exc()
    
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