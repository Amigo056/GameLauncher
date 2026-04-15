import tkinter as tk
from tkinter import messagebox
from core.scanner import EmulatorScanner
from emulators import EmulatorFactory
from .game_list import GameList
from .widgets import ConsoleButton

class EmulatorGrid:
    def __init__(self, root: tk.Tk, back_callback):
        self.root = root
        self.back_callback = back_callback
        
        self.root.configure(bg='#1e1e1e')
        
        # Scanner
        self.scanner = EmulatorScanner()
        self.emulators = self.scanner.scan_all()
        
        # Frame principal
        self.frame = tk.Frame(root, bg='#1e1e1e', padx=20, pady=20)
        self.frame.grid(row=0, column=0, sticky="nsew")
        
        # Header
        self.header = tk.Frame(self.frame, bg='#1e1e1e')
        self.header.pack(fill='x', pady=(0, 20))
        
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
            text="Seleciona a Consola",
            bg='#1e1e1e',
            fg='white',
            font=('Segoe UI', 16, 'bold')
        )
        self.lbl_title.pack(side='left', padx=20)
        
        # Grid de emuladores
        self.grid_frame = tk.Frame(self.frame, bg='#1e1e1e')
        self.grid_frame.pack(expand=True, fill='both')
        
        if not self.emulators:
            self.lbl_empty = tk.Label(
                self.grid_frame,
                text="Nenhum emulador encontrado.\nInstala o melonDS ou PPSSPP.",
                bg='#1e1e1e',
                fg='#888888',
                font=('Segoe UI', 12)
            )
            self.lbl_empty.pack(expand=True)
        else:
            self.create_grid()
    
    def create_grid(self):
        """Cria grid de botões de consolas."""
        row, col = 0, 0
        for emu_data in self.emulators:
            btn = ConsoleButton(
                self.grid_frame,
                name=emu_data['name'],
                icon_path=emu_data['icon'],
                command=lambda e=emu_data: self.select_emulator(e)
            )
            btn.grid(row=row, column=col, padx=10, pady=10)
            
            col += 1
            if col > 2:  # 3 colunas
                col = 0
                row += 1
    
    def select_emulator(self, emu_data: dict):
        """Seleciona emulador e mostra jogos."""
        emulator = EmulatorFactory.create(emu_data)
        if emulator:
            self.frame.destroy()
            GameList(self.root, emulator, self.go_back)
        else:
            messagebox.showerror("Erro", f"Emulador {emu_data['id']} não implementado.")
    
    def go_back(self):
        """Volta ao menu anterior."""
        self.frame.destroy()
        self.back_callback()