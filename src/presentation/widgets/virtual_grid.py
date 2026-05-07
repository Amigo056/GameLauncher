"""Widget de grid virtualizado para performance com grandes bibliotecas."""
import tkinter as tk
from typing import Callable, List, Any, Optional

from src.presentation.theme import DARK_THEME


class VirtualGrid(tk.Canvas):
    """
    Grid virtualizado — só renderiza items visíveis no viewport.

    Stub funcional (Semana 1) — delega para um Frame normal.
    Futuro: implementação real com viewport clipping e recycling.

    Uso:
        grid = VirtualGrid(parent, item_height=200)
        grid.set_items(games, render_fn)
    """

    def __init__(
        self,
        parent: tk.Widget,
        item_height: int = 200,
        columns: int = 4,
        bg: str = None,
    ):
        t = DARK_THEME
        super().__init__(parent, bg=bg or t.bg_primary, highlightthickness=0)

        self._item_height = item_height
        self._columns = columns
        self._items: List[Any] = []
        self._render_fn: Optional[Callable[[tk.Widget, Any, int], tk.Widget]] = None
        self._widgets: List[tk.Widget] = []

        # Scrollbar
        self._scrollbar = tk.Scrollbar(parent, orient='vertical', command=self.yview)
        self.configure(yscrollcommand=self._scrollbar.set)

        # Container interno
        self._frame = tk.Frame(self, bg=bg or t.bg_primary)
        self._window = self.create_window((0, 0), window=self._frame, anchor='nw')

        # Bind resize
        self.bind('<Configure>', self._on_configure)
        self._frame.bind('<Configure>', self._on_frame_configure)

    def _on_configure(self, event):
        """Ajusta largura do container interno."""
        self.itemconfig(self._window, width=event.width)

    def _on_frame_configure(self, _=None):
        """Atualiza scrollregion quando conteúdo muda."""
        self.configure(scrollregion=self.bbox('all'))

    def pack(self, **kwargs):
        """Override para empacotar scrollbar também."""
        self._scrollbar.pack(side='right', fill='y')
        super().pack(side='left', fill='both', expand=True, **kwargs)

    def grid(self, **kwargs):
        """Override para grid scrollbar também."""
        self._scrollbar.grid(row=kwargs.get('row', 0), column=kwargs.get('column', 0) + 1, sticky='ns')
        super().grid(sticky='nsew', **{k: v for k, v in kwargs.items() if k not in ('row', 'column')})

    def set_items(
        self,
        items: List[Any],
        render_fn: Callable[[tk.Widget, Any, int], tk.Widget],
    ):
        """
        Define items e função de renderização.

        Args:
            items: Lista de dados
            render_fn: (parent, item, index) -> Widget
        """
        self._items = items
        self._render_fn = render_fn
        self._refresh()

    def _refresh(self):
        """Limpa e re-renderiza todos os items visíveis."""
        # Limpar widgets antigos
        for widget in self._widgets:
            widget.destroy()
        self._widgets.clear()

        if not self._render_fn:
            return

        # Renderização simples (não virtualizada ainda)
        for idx, item in enumerate(self._items):
            row = idx // self._columns
            col = idx % self._columns

            widget = self._render_fn(self._frame, item, idx)
            widget.grid(row=row, column=col, padx=10, pady=10, sticky='n')
            self._widgets.append(widget)

        self._on_frame_configure()

    def clear(self):
        """Limpa todos os items."""
        self._items.clear()
        self._refresh()

    def bind_mousewheel(self, widget: tk.Widget):
        """Bind mousewheel para scroll."""
        def _on_mousewheel(event):
            self.yview_scroll(int(-1 * (event.delta / 120)), 'units')
        widget.bind_all('<MouseWheel>', _on_mousewheel)