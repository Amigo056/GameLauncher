import tkinter as tk
from tkinter import messagebox


class HomePage:
    """Página inicial com botões Emuladores e Definições."""
    
    def __init__(self, parent: tk.Widget, on_emulators: callable, on_settings: callable):
        """
        Args:
            parent: Widget pai onde a página será renderizada
            on_emulators: Callback quando clicar em "Emuladores"
            on_settings: Callback quando clicar em "Definições"
        """
        self.frame = tk.Frame(parent, bg='#1e1e1e')
        
        self.on_emulators = on_emulators
        self.on_settings = on_settings
        
        self._build_ui()
    
    def _build_ui(self):
        """Constrói a interface."""
        # Container centralizado
        center = tk.Frame(self.frame, bg='#1e1e1e')
        center.place(relx=0.5, rely=0.5, anchor='center')
        
        # Título
        tk.Label(
            center,
            text="🎮 GameLauncher",
            bg='#1e1e1e',
            fg='white',
            font=('Segoe UI', 36, 'bold')
        ).pack(pady=(0, 50))
        
        # Botão Emuladores
        tk.Button(
            center,
            text="📁  Emuladores",
            font=('Segoe UI', 16),
            bg='#0078d4',
            fg='white',
            activebackground='#106ebe',
            activeforeground='white',
            relief='flat',
            cursor='hand2',
            width=20,
            height=2,
            command=self.on_emulators
        ).pack(pady=10)
        
        # Botão Definições
        tk.Button(
            center,
            text="⚙️  Definições",
            font=('Segoe UI', 16),
            bg='#333333',
            fg='white',
            activebackground='#444444',
            activeforeground='white',
            relief='flat',
            cursor='hand2',
            width=20,
            height=2,
            command=self.on_settings
        ).pack(pady=10)
        
        # Versão
        tk.Label(
            center,
            text="v1.0",
            bg='#1e1e1e',
            fg='#666666',
            font=('Segoe UI', 9)
        ).pack(side='bottom', pady=50)
    