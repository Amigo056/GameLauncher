"""Widget de drag & drop para adicionar ROMs."""
import tkinter as tk
from pathlib import Path
from typing import Callable, List, Optional

from src.presentation.theme import DARK_THEME, font


class DropZone(tk.Frame):
    """
    Área onde o user arrasta ficheiros para adicionar ROMs.
    
    Stub funcional (Semana 1) — mostra UI mas drag & drop nativo
    requer TkDND ou implementação platform-specific.
    Futuro: integração com TkDND para drag & drop real.
    """

    def __init__(
        self,
        parent: tk.Widget,
        on_files_dropped: Optional[Callable[[List[Path]], None]] = None,
        accepted_extensions: Optional[List[str]] = None,
    ):
        t = DARK_THEME
        super().__init__(parent, bg=t.bg_card, padx=20, pady=20)
        
        self.on_files_dropped = on_files_dropped
        self.accepted_extensions = set(
            ext.lower() if ext.startswith('.') else f'.{ext.lower()}'
            for ext in (accepted_extensions or ['.nds', '.iso', '.cso', '.gba', '.gbc', '.gb', '.z64', '.n64', '.v64'])
        )
        
        self._build_ui()
        self._setup_bindings()

    def _build_ui(self):
        """Constrói interface visual da drop zone."""
        t = DARK_THEME
        
        # Borda tracejada simulada
        self.configure(
            highlightbackground=t.border,
            highlightcolor=t.accent,
            highlightthickness=2,
        )
        
        self._inner = tk.Frame(self, bg=t.bg_card)
        self._inner.pack(expand=True, fill='both', padx=40, pady=40)
        
        self._lbl_icon = tk.Label(
            self._inner,
            text="📥",
            bg=t.bg_card,
            fg=t.text_secondary,
            font=font(t, "font_size_3xl"),
        )
        self._lbl_icon.pack()
        
        self._lbl_text = tk.Label(
            self._inner,
            text="Arrasta ROMs para aqui",
            bg=t.bg_card,
            fg=t.text_secondary,
            font=font(t, "font_size_lg"),
        )
        self._lbl_text.pack(pady=(10, 5))
        
        exts_str = ', '.join(sorted(self.accepted_extensions))
        tk.Label(
            self._inner,
            text=f"Formatos suportados: {exts_str}",
            bg=t.bg_card,
            fg=t.text_disabled,
            font=font(t, "font_size_sm"),
        ).pack()
        
        # Botão alternativo (fallback)
        self._btn_browse = tk.Button(
            self._inner,
            text="📁  Ou clica para procurar",
            bg=t.bg_tertiary,
            fg=t.text_primary,
            font=font(t, "font_size_md"),
            relief='flat',
            cursor='hand2',
            command=self._on_browse,
        )
        self._btn_browse.pack(pady=(15, 0))

    def _setup_bindings(self):
        """Configura eventos de hover."""
        for widget in [self, self._inner, self._lbl_icon, self._lbl_text]:
            widget.bind('<Enter>', self._on_enter)
            widget.bind('<Leave>', self._on_leave)

    def _on_enter(self, _=None):
        """Efeito hover — ativar."""
        t = DARK_THEME
        self.configure(highlightbackground=t.accent)
        self._lbl_icon.config(fg=t.accent)
        self._lbl_text.config(fg=t.text_primary)

    def _on_leave(self, _=None):
        """Efeito hover — desativar."""
        t = DARK_THEME
        self.configure(highlightbackground=t.border)
        self._lbl_icon.config(fg=t.text_secondary)
        self._lbl_text.config(fg=t.text_secondary)

    def _on_browse(self):
        """Abre diálogo de ficheiros como fallback."""
        from tkinter import filedialog
        
        files = filedialog.askopenfilenames(
            title="Selecionar ROMs",
            filetypes=[
                ("Todos os ficheiros suportados", ' '.join(f'*{ext}' for ext in self.accepted_extensions)),
                ("ROMs Nintendo DS", "*.nds"),
                ("ROMs PSP", "*.iso *.cso"),
                ("ROMs GBA", "*.gba *.gbc *.gb"),
                ("ROMs N64", "*.z64 *.n64 *.v64"),
                ("Todos os ficheiros", "*.*"),
            ]
        )
        
        if files and self.on_files_dropped:
            paths = [Path(f) for f in files]
            self.on_files_dropped(paths)

    def set_dropped_callback(self, callback: Callable[[List[Path]], None]):
        """Atualiza callback para ficheiros recebidos."""
        self.on_files_dropped = callback