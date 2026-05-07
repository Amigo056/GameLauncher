"""Widget de toast notifications não-modais."""
import tkinter as tk
from typing import Optional


class Toast(tk.Toplevel):
    """
    Notificação não-modal que desaparece automaticamente.
    
    Uso:
        Toast.show(parent, "Jogo lançado!", level="success", duration=3000)
    
    Levels:
        - info:    azul
        - success: verde
        - warning: laranja
        - error:   vermelho
    """

    COLORS = {
        "info":    {"bg": "#0078d4", "fg": "#ffffff"},
        "success": {"bg": "#4CAF50", "fg": "#ffffff"},
        "warning": {"bg": "#FF9800", "fg": "#ffffff"},
        "error":   {"bg": "#f44336", "fg": "#ffffff"},
    }

    _active_toasts: list["Toast"] = []
    _offset_y = 20  # Posição vertical inicial
    _toast_height = 60
    _toast_spacing = 10

    def __init__(
        self,
        parent: tk.Widget,
        message: str,
        level: str = "info",
        duration: int = 3000,
    ):
        super().__init__(parent)
        
        self._duration = duration
        self._level = level if level in self.COLORS else "info"
        colors = self.COLORS[self._level]
        
        # Configurações da janela
        self.overrideredirect(True)  # Sem borda/decorações
        self.attributes('-topmost', True)
        self.configure(bg=colors["bg"])
        
        # Conteúdo
        frame = tk.Frame(self, bg=colors["bg"], padx=20, pady=12)
        frame.pack(fill='both', expand=True)
        
        # Ícone por nível
        icons = {
            "info": "ℹ️",
            "success": "✅",
            "warning": "⚠️",
            "error": "❌",
        }
        
        tk.Label(
            frame,
            text=icons.get(self._level, "ℹ️"),
            bg=colors["bg"],
            fg=colors["fg"],
            font=('Segoe UI', 16),
        ).pack(side='left', padx=(0, 10))
        
        tk.Label(
            frame,
            text=message,
            bg=colors["bg"],
            fg=colors["fg"],
            font=('Segoe UI', 11),
            wraplength=350,
            justify='left',
        ).pack(side='left')
        
        # Botão fechar (X)
        close_btn = tk.Label(
            frame,
            text="✕",
            bg=colors["bg"],
            fg=colors["fg"],
            font=('Segoe UI', 12),
            cursor='hand2',
        )
        close_btn.pack(side='right', padx=(15, 0))
        close_btn.bind('<Button-1>', lambda e: self._close())
        
        # Posicionar
        self._position_window(parent)
        
        # Auto-close
        self._close_job = self.after(duration, self._close)
        
        # Fade in effect (simulado com alpha se suportado)
        self._fade_in()

    def _position_window(self, parent: tk.Widget):
        """Calcula posição no canto superior direito."""
        self.update_idletasks()
        
        # Obter geometria do parent
        parent_x = parent.winfo_rootx()
        parent_y = parent.winfo_rooty()
        parent_w = parent.winfo_width()
        
        toast_w = self.winfo_width()
        toast_h = self.winfo_height()
        
        # Posição: canto superior direito com margem
        x = parent_x + parent_w - toast_w - 20
        y = parent_y + Toast._offset_y
        
        self.geometry(f"+{x}+{y}")
        
        # Atualizar offset para próximo toast
        Toast._offset_y += toast_h + Toast._toast_spacing
        Toast._active_toasts.append(self)

    def _fade_in(self):
        """Tenta aplicar efeito de fade in (Windows)."""
        try:
            self.attributes('-alpha', 0.0)
            self._do_fade(0.0)
        except tk.TclError:
            pass  # Alpha não suportado

    def _do_fade(self, alpha: float):
        """Animação de fade in."""
        if alpha >= 1.0:
            return
        try:
            self.attributes('-alpha', alpha)
            self.after(20, lambda: self._do_fade(alpha + 0.1))
        except tk.TclError:
            pass

    def _close(self):
        """Fecha o toast e libera posição."""
        if self._close_job:
            self.after_cancel(self._close_job)
        
        if self in Toast._active_toasts:
            Toast._active_toasts.remove(self)
            self._reposition_toasts()
        
        try:
            self.destroy()
        except tk.TclError:
            pass

    @classmethod
    def _reposition_toasts(cls):
        """Reposiciona toasts ativos após fechar um."""
        cls._offset_y = 20
        for toast in cls._active_toasts:
            toast.update_idletasks()
            parent = toast.master
            parent_x = parent.winfo_rootx()
            parent_y = parent.winfo_rooty()
            parent_w = parent.winfo_width()
            toast_w = toast.winfo_width()
            x = parent_x + parent_w - toast_w - 20
            y = parent_y + cls._offset_y
            toast.geometry(f"+{x}+{y}")
            cls._offset_y += toast.winfo_height() + cls._toast_spacing

    @classmethod
    def show(
        cls,
        parent: tk.Widget,
        message: str,
        level: str = "info",
        duration: int = 3000,
    ) -> "Toast":
        """
        Mostra um toast notification.
        
        Args:
            parent: Widget pai (para posicionamento)
            message: Texto da notificação
            level: info | success | warning | error
            duration: Duração em ms antes de auto-fechar
            
        Returns:
            Instância do Toast (pode chamar .destroy() para fechar manualmente)
        """
        toast = cls(parent, message, level, duration)
        return toast

    @classmethod
    def close_all(cls):
        """Fecha todos os toasts ativos."""
        for toast in cls._active_toasts[:]:
            toast._close()