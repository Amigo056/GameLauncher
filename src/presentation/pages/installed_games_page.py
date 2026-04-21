"""View: Página de jogos instalados localmente."""
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
import threading
from PIL import Image, ImageTk
from typing import Optional

from src.domain.entities.game import Game
from src.domain.entities.emulator import Emulator
from src.domain.repositories.game_repository import GameRepository
from src.application.launch_emulator import LaunchEmulatorUseCase
from src.infrastructure.system.process_manager import SubprocessProcessManager


class InstalledGamesPage:
    """Mostra jogos locais com grid de capas e lançamento."""

    def __init__(
        self,
        parent: tk.Widget,
        root_window: tk.Tk,  # Necessário para minimizar/restaurar
        emulator: Emulator,
        game_repo: GameRepository,
        on_back: callable,
        on_config_controller: callable = None

    ):
        self.frame = tk.Frame(parent, bg='#1e1e1e')

        self.root = root_window
        self.emulator = emulator
        self.game_repo = game_repo
        self.on_back = on_back
        self.on_config_controller = on_config_controller

        self.games: list[Game] = []
        self._image_cache: dict[str, ImageTk.PhotoImage] = {}
        self.covers_dir = Path("assets/covers")

        self._build_ui()
        self._load_games()

    def _build_ui(self):
        """Constrói interface com grid de jogos."""
        # Header
        header = tk.Frame(self.frame, bg='#1e1e1e', padx=20, pady=15)
        header.pack(fill='x')

        tk.Button(
            header, text="← Voltar",
            font=('Segoe UI', 11), bg='#333333', fg='white',
            relief='flat', cursor='hand2',
            command=self.on_back
        ).pack(side='left')

        tk.Label(
            header,
            text=f"Meus Jogos - {self.emulator.name}",
            bg='#1e1e1e', fg='white',
            font=('Segoe UI', 18, 'bold')
        ).pack(side='left', padx=20)

        self.lbl_count = tk.Label(
            header, text="",
            bg='#1e1e1e', fg='#888888',
            font=('Segoe UI', 11)
        )
        self.lbl_count.pack(side='right')

        # Botão config controlos (só para N64)
        if self.emulator.id == "mupen64plus":
            tk.Button(
                header,
                text="🎮 Controlos",
                font=('Segoe UI', 11),
                bg='#2d2d2d',
                fg='white',
                relief='flat',
                cursor='hand2',
                command=self._on_config_controller
            ).pack(side='right', padx=10)
        
        # Área de scroll para os jogos
        container = tk.Frame(self.frame, bg='#1e1e1e')
        container.pack(fill='both', expand=True, padx=20, pady=10)

        # Canvas com scrollbar
        self.canvas = tk.Canvas(container, bg='#1e1e1e', highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=self.canvas.yview)

        self.grid_frame = tk.Frame(self.canvas, bg='#1e1e1e')
        self.grid_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.grid_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Mouse scroll
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    def _on_config_controller(self):
        """Abre página de configuração de controlos."""
        if self.on_config_controller:
            self.on_config_controller(self.emulator.id)

    def _load_games(self):
        """Carrega jogos do repositório local."""
        # Scan da pasta de ROMs
        self.games = self.game_repo.get_installed_games(self.emulator)
        self.lbl_count.config(text=f"{len(self.games)} jogos")

        if not self.games:
            tk.Label(
                self.grid_frame,
                text="Nenhum jogo encontrado\nColoca as ROMs na pasta:",
                bg='#1e1e1e', fg='#888888',
                font=('Segoe UI', 12),
                justify='center'
            ).grid(row=0, column=0, pady=50)

            path_label = tk.Label(
                self.grid_frame,
                text=str(self.emulator.roms_directory),
                bg='#1e1e1e', fg='#0078d4',
                font=('Segoe UI', 10, 'bold')
            )
            path_label.grid(row=1, column=0)
            return

        self._render_grid()

    def _render_grid(self):
        """Renderiza grid de jogos."""
        # Limpar grid anterior
        for widget in self.grid_frame.winfo_children():
            widget.destroy()

        cols = 4
        for idx, game in enumerate(self.games):
            row = idx // cols
            col = idx % cols

            card = self._create_game_card(game)
            card.grid(row=row, column=col, padx=15, pady=15)

    def _create_game_card(self, game: Game) -> tk.Frame:
        """Cria card de um jogo."""
        frame = tk.Frame(self.grid_frame, bg='#252525', padx=10, pady=10, cursor='hand2')

        # Cover (placeholder inicial)
        lbl_cover = tk.Label(frame, bg='#333333', width=15, height=8)
        lbl_cover.pack()

        # Carregar imagem assincronamente
        self._load_cover_async(game, lbl_cover)

        # Título
        title = game.title[:28] + "..." if len(game.title) > 28 else game.title
        tk.Label(
            frame, text=title,
            bg='#252525', fg='white',
            font=('Segoe UI', 9, 'bold'),
            wraplength=130, justify='center'
        ).pack(pady=(10, 0))

        # Região
        region_text = f"({game.region.name})" if game.region.name != "UNKNOWN" else ""
        if region_text:
            tk.Label(
                frame, text=region_text,
                bg='#252525', fg='#888888',
                font=('Segoe UI', 8)
            ).pack()

        # Clique para jogar
        for widget in [frame, lbl_cover]:
            widget.bind('<Button-1>', lambda e, g=game: self._on_play(g))

        # Hover
        def on_enter(e):
            frame.configure(bg='#353535')
            for child in frame.winfo_children():
                if isinstance(child, tk.Label):
                    child.configure(bg='#353535')

        def on_leave(e):
            frame.configure(bg='#252525')
            for child in frame.winfo_children():
                if isinstance(child, tk.Label):
                    child.configure(bg='#252525')

        frame.bind('<Enter>', on_enter)
        frame.bind('<Leave>', on_leave)

        return frame

    def _load_cover_async(self, game: Game, label: tk.Label):
        """Carrega capa em thread separada."""
        def load():
            try:
                # Procurar capa
                cover_path = self._find_cover(game)

                if cover_path and cover_path.exists():
                    img = Image.open(cover_path)
                    img = img.resize((140, 210), Image.Resampling.LANCZOS)
                    photo = ImageTk.PhotoImage(img)
                    self._image_cache[game.id] = photo

                    # Atualizar UI na main thread
                    self.frame.after(0, lambda: label.configure(image=photo, width=0, height=0))
                else:
                    # Placeholder com texto
                    self.frame.after(0, lambda: label.configure(
                        text="No Image", fg='white', font=('Segoe UI', 10)
                    ))
            except Exception:
                pass

        threading.Thread(target=load, daemon=True).start()

    def _find_cover(self, game: Game) -> Optional[Path]:
        """Procura capa do jogo em vários locais."""
        # Possíveis nomes
        if not game.rom:
            return None
        
        rom_stem = game.rom.file_path.stem
        # Sanitizar: remover (USA), (Rev 2), etc. para bater com os nomes das covers
        clean_name = self._sanitize_for_cover(rom_stem)  # "Cars 2" → "cars_2"
        
        candidates = [
            f"{self.emulator.id}_{clean_name}.png",
            f"{self.emulator.id}_{clean_name}.jpg",
            f"{clean_name}.png",
            rom_stem + ".png",
        ]

        # Locais
        locations = [
            self.covers_dir / self.emulator.id.lower(),
            self.covers_dir,
            game.rom.file_path.parent if game.rom else None
        ]

        for loc in locations:
            if not loc:
                continue
            for candidate in candidates:
                path = loc / candidate
                if path.exists():
                    return path
        return None
    
    def _sanitize_for_cover(self, name: str) -> str:
        """Converte nome da ROM para formato das covers."""
        import re
        # Remover parênteses e conteúdo: (USA), (Rev 2), etc.
        clean = re.sub(r'\s*\([^)]*\)', '', name)
        # Remover pontuação exceto underscore
        clean = re.sub(r'[^\w\s]', '', clean)
        # Trim e lowercase com underscores
        clean = '_'.join(clean.strip().lower().split())
        return clean

    def _on_play(self, game: Game):
        """Lança o jogo: minimiza, abre emulador, espera, restaura."""
        if not game.rom or not game.rom.exists:
            messagebox.showerror("Erro", "ROM não encontrada!")
            return

        confirm = messagebox.askyesno(
            "Lançar Jogo",
            f"Desejas jogar {game.title}?"
        )
        if not confirm:
            return

        # Minimizar janela
        self.root.iconify()

        # Lançar em background
        def launch_and_wait():
            try:
                process_manager = SubprocessProcessManager()
                use_case = LaunchEmulatorUseCase(process_manager)

                result = use_case.execute(game, self.emulator, wait_for_close=True)

                if not result.success:
                    self.frame.after(0, lambda: messagebox.showerror(
                        "Erro", f"Falha ao lançar: {result.error_message}"
                    ))

                # Restaurar janela quando emulador fechar
                self.frame.after(0, self.root.deiconify)

            except Exception as e:
                self.frame.after(0, lambda: messagebox.showerror("Erro", str(e)))
                self.frame.after(0, self.root.deiconify)

        threading.Thread(target=launch_and_wait, daemon=True).start()

    def destroy(self):
        """Esconde em vez de destruir."""
        self.canvas.unbind_all("<MouseWheel>")
        self.frame.grid_remove()