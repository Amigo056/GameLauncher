"""Tema visual da aplicação — centraliza todas as cores e estilos."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Theme:
    """Tema visual completo da aplicação.
    
    frozen=True garante imutabilidade — o tema é um value object.
    """
    # Backgrounds
    bg_primary: str = "#1e1e1e"
    bg_secondary: str = "#252525"
    bg_tertiary: str = "#333333"
    bg_card: str = "#2d2d2d"
    bg_hover: str = "#353535"
    
    # Accent
    accent: str = "#0078d4"
    accent_hover: str = "#106ebe"
    accent_light: str = "#1a8cff"
    
    # Texto
    text_primary: str = "#ffffff"
    text_secondary: str = "#888888"
    text_muted: str = "#cccccc"
    text_disabled: str = "#666666"
    
    # Estados
    error: str = "#f44336"
    error_bg: str = "#3d1f1f"
    success: str = "#4CAF50"
    success_bg: str = "#1f3d1f"
    warning: str = "#FF9800"
    warning_bg: str = "#3d2f1f"
    info: str = "#0078d4"
    info_bg: str = "#1f2f3d"
    
    # Bordas
    border: str = "#555555"
    border_light: str = "#3d3d3d"
    border_hover: str = "#666666"
    
    # Scrollbar
    scrollbar_bg: str = "#2d2d2d"
    scrollbar_fg: str = "#555555"
    
    # Fontes
    font_family: str = "Segoe UI"
    font_mono: str = "Consolas"
    
    # Tamanhos
    font_size_sm: int = 9
    font_size_md: int = 11
    font_size_lg: int = 14
    font_size_xl: int = 18
    font_size_2xl: int = 20
    font_size_3xl: int = 36


# Instância global do tema escuro
DARK_THEME = Theme()


# Helpers para estilos comuns
def font(theme: Theme, size_key: str = "font_size_md", bold: bool = False, italic: bool = False) -> tuple:
    """Retorna tuplo (family, size, *styles) para tkinter.
    
    Args:
        theme: Instância do tema
        size_key: Chave do tamanho (font_size_sm, font_size_md, etc.)
        bold: Se True, adiciona 'bold'
        italic: Se True, adiciona 'italic'
    
    Returns:
        Tuplo compatível com parâmetro font do tkinter
    """
    size = getattr(theme, size_key, theme.font_size_md)
    styles = []
    if bold:
        styles.append("bold")
    if italic:
        styles.append("italic")
    
    if styles:
        return (theme.font_family, size, " ".join(styles))
    return (theme.font_family, size)


def mono_font(theme: Theme, size_key: str = "font_size_md", bold: bool = False) -> tuple:
    """Retorna fonte monoespaçada."""
    size = getattr(theme, size_key, theme.font_size_md)
    if bold:
        return (theme.font_mono, size, "bold")
    return (theme.font_mono, size)