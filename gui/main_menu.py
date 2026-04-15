import tkinter as tk
from tkinter import ttk
from .emulator_grid import EmulatorGrid
from core.window_manager import WindowManager

class MainMenu:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("GameLauncher")
        self.root.configure(bg='#1e1e1e')
        
        # Restaurar estado anterior
        WindowManager.restore_state(self.root)
        
        # Configurar grid
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        
        # Frame principal
        self.main_frame = tk.Frame(root, bg='#1e1e1e', padx=50, pady=50)
        self.main_frame.grid(row=0, column=0, sticky="nsew")
        
        # Título
        self.lbl_title = tk.Label(
            self.main_frame,
            text="🎮 GameLauncher",
            bg='#1e1e1e',
            fg='white',
            font=('Segoe UI', 24, 'bold')
        )
        self.lbl_title.pack(pady=(0, 30))
        
        # Botões
        self.btn_emulators = tk.Button(
            self.main_frame,
            text="Emuladores",
            command=self.open_emulators,
            bg='#0078d4',
            fg='white',
            font=('Segoe UI', 12),
            width=20,
            height=2,
            relief='flat',
            cursor='hand2'
        )
        self.btn_emulators.pack(pady=10)
        
        self.btn_settings = tk.Button(
            self.main_frame,
            text="Definições",
            command=self.open_settings,
            bg='#333333',
            fg='white',
            font=('Segoe UI', 12),
            width=20,
            height=2,
            relief='flat',
            cursor='hand2'
        )
        self.btn_settings.pack(pady=10)
        
        self.btn_exit = tk.Button(
            self.main_frame,
            text="Sair",
            command=self.on_exit,
            bg='#c42b1c',
            fg='white',
            font=('Segoe UI', 12),
            width=20,
            height=2,
            relief='flat',
            cursor='hand2'
        )
        self.btn_exit.pack(pady=10)
        
        # Bind fechar janela
        self.root.protocol("WM_DELETE_WINDOW", self.on_exit)
    
    def open_emulators(self):
        """Abre grid de emuladores."""
        self.main_frame.destroy()
        EmulatorGrid(self.root, self.show_main_menu)
    
    def open_settings(self):
        """Placeholder para definições."""
        tk.messagebox.showinfo("Definições", "Funcionalidade em desenvolvimento")
    
    def show_main_menu(self):
        """Volta ao menu principal."""
        for widget in self.root.winfo_children():
            widget.destroy()
        self.__init__(self.root)
    
    def on_exit(self):
        """Guarda estado e sai."""
        WindowManager.save_state(self.root)
        self.root.quit()