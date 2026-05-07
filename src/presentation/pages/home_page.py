import tkinter as tk

from src.presentation.theme import DARK_THEME, font


class HomePage:
    """Página inicial com botões Emuladores e Definições."""
    
    def __init__(self, parent: tk.Widget, on_emulators: callable, on_settings: callable):
        """
        Args:
            parent: Widget pai onde a página será renderizada
            on_emulators: Callback quando clicar em "Emuladores"
            on_settings: Callback quando clicar em "Definições"
        """
        self.frame = tk.Frame(parent, bg=DARK_THEME.bg_primary)
        
        self.on_emulators = on_emulators
        self.on_settings = on_settings
        
        self._build_ui()
    
    def _build_ui(self):
        """Constrói a interface."""
        t = DARK_THEME
        
        # Container centralizado
        center = tk.Frame(self.frame, bg=t.bg_primary)
        center.place(relx=0.5, rely=0.5, anchor='center')
        
        # Título
        tk.Label(
            center,
            text="🎮 GameLauncher",
            bg=t.bg_primary,
            fg=t.text_primary,
            font=font(t, "font_size_3xl", bold=True)
        ).pack(pady=(0, 50))
        
        # Botão Emuladores
        tk.Button(
            center,
            text="📁  Emuladores",
            font=font(t, "font_size_lg"),
            bg=t.accent,
            fg=t.text_primary,
            activebackground=t.accent_hover,
            activeforeground=t.text_primary,
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
            font=font(t, "font_size_lg"),
            bg=t.bg_tertiary,
            fg=t.text_primary,
            activebackground=t.bg_hover,
            activeforeground=t.text_primary,
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
            bg=t.bg_primary,
            fg=t.text_disabled,
            font=font(t, "font_size_sm")
        ).pack(side='bottom', pady=50)