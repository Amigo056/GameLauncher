import json
import tkinter as tk
from pathlib import Path
from PIL import Image, ImageTk

from src.presentation.theme import DARK_THEME, font


class EmulatorSelectionPage:
    """Página para selecionar qual emulador/plataforma usar."""

    # Tamanho normalizado dos ícones (todos ficam iguais)
    ICON_SIZE = (120, 120)
    # Tamanho fixo de cada card (largura x altura)
    CARD_WIDTH = 240
    CARD_HEIGHT = 280

    def __init__(
        self,
        parent: tk.Widget,
        on_back: callable,
        on_select_emulator: callable,
        emulators_config: list[dict] = None
    ):
        t = DARK_THEME
        self.frame = tk.Frame(parent, bg=t.bg_primary)

        self.on_back = on_back
        self.on_select_emulator = on_select_emulator
        self._icon_cache: dict[str, ImageTk.PhotoImage] = {}

        # Config default se não fornecido
        with open("config/emulators.json") as f:
            self.emulators = json.load(f)["emulators"]

        self._build_ui()

    def _build_ui(self):
        """Constrói a interface."""
        t = DARK_THEME
        
        # Header
        header = tk.Frame(self.frame, bg=t.bg_primary, padx=20, pady=20)
        header.pack(fill='x')

        tk.Button(
            header,
            text="← Voltar",
            font=font(t, "font_size_md"),
            bg=t.bg_tertiary,
            fg=t.text_primary,
            relief='flat',
            cursor='hand2',
            command=lambda: self.frame.after(10, self.on_back)
        ).pack(side='left')

        tk.Label(
            header,
            text="Seleciona uma plataforma",
            bg=t.bg_primary,
            fg=t.text_primary,
            font=font(t, "font_size_2xl", bold=True)
        ).pack(side='left', padx=20)

        # Container dos cards
        container = tk.Frame(self.frame, bg=t.bg_primary)
        container.pack(expand=True)

        # Criar card para cada emulador
        for emu in self.emulators:
            self._create_emulator_card(container, emu).pack(
                side='left', padx=20, pady=20
            )

    def _load_emulator_icon(self, emu: dict) -> ImageTk.PhotoImage | None:
        """Carrega e redimensiona ícone do emulador. Retorna None se falhar."""
        icon_path = emu.get("icon_path") or emu.get("icon")

        if icon_path:
            path = Path(icon_path)
            if path.exists():
                try:
                    img = Image.open(path).convert("RGBA")
                    img = img.resize(self.ICON_SIZE, Image.Resampling.LANCZOS)
                    photo = ImageTk.PhotoImage(img)
                    self._icon_cache[emu["id"]] = photo
                    return photo
                except Exception as e:
                    print(f"Erro ao carregar ícone {icon_path}: {e}")

        # Fallback: gerar imagem com emoji se não houver ficheiro
        try:
            from PIL import ImageDraw, ImageFont
            img = Image.new('RGBA', self.ICON_SIZE, (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)

            # Tentar fonte do sistema
            try:
                font_obj = ImageFont.truetype("segoeui.ttf", 72)
            except Exception:
                font_obj = ImageFont.load_default()

            emoji = emu.get("emoji", "🎮")
            bbox = draw.textbbox((0, 0), emoji, font=font_obj)
            w = bbox[2] - bbox[0]
            h = bbox[3] - bbox[1]
            x = (self.ICON_SIZE[0] - w) // 2
            y = (self.ICON_SIZE[1] - h) // 2
            draw.text((x, y), emoji, font=font_obj, embedded_color=True)

            photo = ImageTk.PhotoImage(img)
            self._icon_cache[emu["id"]] = photo
            return photo
        except Exception:
            return None

    def _create_emulator_card(self, parent: tk.Widget, emu: dict) -> tk.Frame:
        """Cria card de tamanho FIXO para o emulador."""
        t = DARK_THEME
        
        card = tk.Frame(
            parent,
            bg=t.bg_card,
            width=self.CARD_WIDTH,
            height=self.CARD_HEIGHT,
            cursor='hand2',
            highlightbackground=t.border_light,
            highlightthickness=1
        )
        # Fundamental: impede o frame de ajustar ao conteúdo
        card.pack_propagate(False)
        card.grid_propagate(False)

        # Container interno centrado (para o conteúdo não colar nas bordas)
        inner = tk.Frame(card, bg=t.bg_card)
        inner.place(relx=0.5, rely=0.45, anchor='center')

        # Ícone (todos do mesmo tamanho)
        icon_photo = self._load_emulator_icon(emu)
        if icon_photo:
            lbl_icon = tk.Label(inner, image=icon_photo, bg=t.bg_card)
            lbl_icon.image = icon_photo  # Guardar ref.
        else:
            lbl_icon = tk.Label(
                inner,
                text=emu.get("emoji", "🎮"),
                bg=t.bg_card,
                fg=emu.get("color", t.text_primary),
                font=font(t, "font_size_3xl")
            )
        lbl_icon.pack()

        # Nome com largura fixa para não quebrar layout
        # trunca com '...' se for muito grande
        display_name = emu["name"]
        if len(display_name) > 22:
            display_name = display_name[:20] + "..."

        lbl_name = tk.Label(
            inner,
            text=display_name,
            bg=t.bg_card,
            fg=t.text_primary,
            font=font(t, "font_size_md", bold=True),
            wraplength=200,
            justify='center',
            width=20  # Força largura de caracteres
        )
        lbl_name.pack(pady=(15, 0))

        # Hover effects (apenas bg, sem mexer no conteúdo visual)
        def on_enter(e):
            card.configure(bg=t.bg_hover, highlightbackground=t.border_hover)
            inner.configure(bg=t.bg_hover)
            for child in inner.winfo_children():
                child.configure(bg=t.bg_hover)

        def on_leave(e):
            card.configure(bg=t.bg_card, highlightbackground=t.border_light)
            inner.configure(bg=t.bg_card)
            for child in inner.winfo_children():
                child.configure(bg=t.bg_card)

        # Bind em todos os widgets interativos
        for widget in [card, inner, lbl_icon, lbl_name]:
            widget.bind('<Enter>', on_enter)
            widget.bind('<Leave>', on_leave)
            widget.bind('<Button-1>', lambda e, eid=emu["id"]: self.on_select_emulator(eid))

        return card