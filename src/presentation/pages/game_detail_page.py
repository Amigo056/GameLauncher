"""Página de detalhes do jogo — stub funcional para Semana 1."""
import tkinter as tk
from typing import Callable

from src.domain.entities.game import Game
from src.domain.entities.emulator import Emulator
from src.presentation.theme import DARK_THEME, font


class GameDetailPage:
    """
    Página de detalhes do jogo.
    
    Stub funcional (Semana 1) — mostra informações básicas.
    Futuro: metadados completos, tempo de jogo, histórico de sessões.
    """

    def __init__(
        self,
        parent: tk.Widget,
        game: Game,
        emulator: Emulator,
        on_back: Callable,
        on_play: Callable[[Game], None],
    ):
        t = DARK_THEME
        self.frame = tk.Frame(parent, bg=t.bg_primary)
        self.game = game
        self.emulator = emulator
        self.on_back = on_back
        self.on_play = on_play

        self._build_ui()

    def _build_ui(self):
        """Constrói interface de detalhes básica."""
        t = DARK_THEME
        
        # Header
        header = tk.Frame(self.frame, bg=t.bg_primary, padx=20, pady=15)
        header.pack(fill='x')

        tk.Button(
            header,
            text="← Voltar",
            font=font(t, "font_size_md"),
            bg=t.bg_tertiary,
            fg=t.text_primary,
            relief='flat',
            cursor='hand2',
            command=self.on_back
        ).pack(side='left')

        tk.Label(
            header,
            text=self.game.title,
            bg=t.bg_primary,
            fg=t.text_primary,
            font=font(t, "font_size_2xl", bold=True)
        ).pack(side='left', padx=20)

        # Container principal
        main = tk.Frame(self.frame, bg=t.bg_primary)
        main.pack(fill='both', expand=True, padx=40, pady=20)

        # Info básica
        info = tk.Frame(main, bg=t.bg_secondary, padx=30, pady=30)
        info.pack(fill='x', pady=(0, 20))

        details = [
            ("ID", self.game.id),
            ("Título", self.game.title),
            ("Região", self.game.region.name),
            ("Emulador", self.emulator.name),
            ("Plataforma", self.emulator.platform.value),
        ]

        if self.game.rom:
            details.extend([
                ("Ficheiro", self.game.rom.file_path.name),
                ("Tamanho", self._format_size(self.game.rom.file_size)),
                ("Extensão", self.game.rom.extension),
            ])

        for label, value in details:
            row = tk.Frame(info, bg=t.bg_secondary)
            row.pack(fill='x', pady=4)
            tk.Label(
                row,
                text=f"{label}:",
                bg=t.bg_secondary,
                fg=t.text_secondary,
                font=font(t, "font_size_md"),
                width=12,
                anchor='w'
            ).pack(side='left')
            tk.Label(
                row,
                text=str(value),
                bg=t.bg_secondary,
                fg=t.text_primary,
                font=font(t, "font_size_md", bold=True),
                anchor='w'
            ).pack(side='left', padx=(10, 0))

        # Botão Jogar
        if self.game.is_available_locally:
            tk.Button(
                main,
                text="▶  Jogar",
                font=font(t, "font_size_xl", bold=True),
                bg=t.accent,
                fg=t.text_primary,
                activebackground=t.accent_hover,
                relief='flat',
                cursor='hand2',
                width=20,
                height=2,
                command=self._on_play
            ).pack(pady=20)
        else:
            tk.Label(
                main,
                text="ROM não disponível localmente",
                bg=t.bg_primary,
                fg=t.error,
                font=font(t, "font_size_md")
            ).pack(pady=20)

        # Placeholder para futuras features
        tk.Label(
            main,
            text="📊 Estatísticas de jogo em breve…",
            bg=t.bg_primary,
            fg=t.text_disabled,
            font=font(t, "font_size_md")
        ).pack(pady=(40, 0))

    def _format_size(self, size_bytes: int) -> str:
        """Formata bytes para human-readable."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} TB"

    def _on_play(self):
        """Callback para iniciar o jogo."""
        self.on_play(self.game)

    def destroy(self):
        """Esconde em vez de destruir."""
        self.frame.place_forget()