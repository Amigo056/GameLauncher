import tkinter as tk
from tkinter import messagebox
from core.window_manager import WindowManager
from .widgets import GameCard

class GameList:
    def __init__(self, root: tk.Tk, emulator, back_callback):
        self.root = root
        self.emulator = emulator
        self.back_callback = back_callback
        
        self.root.configure(bg='#1e1e1e')
        
        # Frame principal
        self.frame = tk.Frame(root, bg='#1e1e1e')
        self.frame.grid(row=0, column=0, sticky="nsew")
        self.frame.grid_columnconfigure(0, weight=1)
        
        # Header
        self.create_header()
        
        # Lista de jogos
        self.create_game_grid()
    
    def create_header(self):
        """Cria cabeçalho com título e botão voltar."""
        self.header = tk.Frame(self.frame, bg='#1e1e1e', padx=10, pady=10)
        self.header.grid(row=0, column=0, sticky='ew')
        
        self.btn_back = tk.Button(
            self.header,
            text="← Voltar",
            command=self.go_back,
            bg='#333333',
            fg='white',
            relief='flat',
            font=('Segoe UI', 10)
        )
        self.btn_back.pack(side='left')
        
        self.lbl_title = tk.Label(
            self.header,
            text=f"{self.emulator.name} - Jogos",
            bg='#1e1e1e',
            fg='white',
            font=('Segoe UI', 16, 'bold')
        )
        self.lbl_title.pack(side='left', padx=20)
        
        self.lbl_count = tk.Label(
            self.header,
            text="",
            bg='#1e1e1e',
            fg='#888888',
            font=('Segoe UI', 10)
        )
        self.lbl_count.pack(side='right')
    
    def create_game_grid(self):
        """Cria scrollable grid de jogos."""
        # Canvas para scrolling
        self.canvas = tk.Canvas(self.frame, bg='#1e1e1e', highlightthickness=0)
        self.scrollbar = tk.Scrollbar(self.frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg='#1e1e1e')
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        self.canvas.grid(row=1, column=0, sticky="nsew")
        self.scrollbar.grid(row=1, column=1, sticky="ns")
        self.frame.grid_rowconfigure(1, weight=1)
        
        # Carregar jogos
        self.load_games()
    
    def load_games(self):
        """Carrega e mostra jogos."""
        games = self.emulator.get_installed_games()
        
        if not games:
            self.lbl_empty = tk.Label(
                self.scrollable_frame,
                text=f"Nenhum jogo encontrado em:\n{self.emulator.roms_folder}\n\nColoca os ficheiros {self.emulator.rom_extensions} nessa pasta.",
                bg='#1e1e1e',
                fg='#888888',
                font=('Segoe UI', 11),
                justify='center'
            )
            self.lbl_empty.pack(pady=50)
            return
        
        # Atualizar contador
        self.lbl_count.configure(text=f"{len(games)} jogos")
        
        # Grid de cards
        row, col = 0, 0
        for game in games:
            card = GameCard(
                self.scrollable_frame,
                game,
                self.launch_game
            )
            card.grid(row=row, column=col, padx=10, pady=10)
            
            col += 1
            if col > 4:  # 5 colunas
                col = 0
                row += 1
    
    def launch_game(self, game_data: dict):
        """Lança o jogo selecionado."""
        try:
            # Guardar estado
            WindowManager.save_state(self.root)
            
            # Minimizar
            self.root.withdraw()
            
            # Lançar
            self.emulator.launch_game(game_data['path'])
            
            # Aguardar fecho (polling simples)
            self.check_process_closed()
            
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível lançar o jogo:\n{str(e)}")
            self.root.deiconify()
    
    def check_process_closed(self):
        """Verifica se o emulador fechou para restaurar janela."""
        # Simplificação: após 2 segundos, restaura
        # Em produção, verificar se processo ainda corre
        self.root.after(2000, self.restore_window)
    
    def restore_window(self):
        """Restaura janela principal."""
        self.root.deiconify()
        WindowManager.restore_state(self.root)
        self.root.lift()
    
    def go_back(self):
        """Volta à seleção de emuladores."""
        self.frame.destroy()
        self.back_callback()