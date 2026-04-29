# src/application/services/settings_service.py
import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional


@dataclass
class WindowState:
    width: int = 1200
    height: int = 800
    x: int = 100
    y: int = 100
    maximized: bool = False


@dataclass
class AppSettings:
    roms_base_path: str = "roms"
    last_selected_emulator: Optional[str] = None
    window_state: WindowState = field(default_factory=WindowState)
    cover_cache_enabled: bool = True


class SettingsService:
    """Persiste e carrega definições da aplicação em JSON."""

    DEFAULT_PATH = Path("config/settings.json")

    def __init__(self, config_path: Path = DEFAULT_PATH):
        self.config_path = Path(config_path)

    def load(self) -> AppSettings:
        """Carrega definições do JSON. Retorna defaults se não existir."""
        if not self.config_path.exists():
            return AppSettings()

        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            ws_data = data.get("window_state", {})
            window_state = WindowState(
                width=ws_data.get("width", 1200),
                height=ws_data.get("height", 800),
                x=ws_data.get("x", 100),
                y=ws_data.get("y", 100),
                maximized=ws_data.get("maximized", False),
            )

            return AppSettings(
                roms_base_path=data.get("roms_base_path", "roms"),
                last_selected_emulator=data.get("last_selected_emulator"),
                window_state=window_state,
                cover_cache_enabled=data.get("cover_cache_enabled", True),
            )

        except Exception as e:
            print(f"[Settings] Erro ao carregar: {e}")
            return AppSettings()

    def save(self, settings: AppSettings) -> None:
        """Guarda definições em JSON."""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "roms_base_path": settings.roms_base_path,
            "last_selected_emulator": settings.last_selected_emulator,
            "cover_cache_enabled": settings.cover_cache_enabled,
            "window_state": {
                "width": settings.window_state.width,
                "height": settings.window_state.height,
                "x": settings.window_state.x,
                "y": settings.window_state.y,
                "maximized": settings.window_state.maximized,
            }
        }

        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[Settings] Erro ao guardar: {e}")

    def save_window_state(self, root) -> None:
        """Atalho: guarda apenas o estado da janela tk."""
        settings = self.load()
        settings.window_state = WindowState(
            width=root.winfo_width(),
            height=root.winfo_height(),
            x=root.winfo_x(),
            y=root.winfo_y(),
            maximized=root.state() == 'zoomed',
        )
        self.save(settings)

    def apply_window_state(self, root) -> None:
        """Restaura tamanho/posição da janela."""
        settings = self.load()
        ws = settings.window_state
        if ws.maximized:
            root.state('zoomed')
        else:
            root.geometry(f"{ws.width}x{ws.height}+{ws.x}+{ws.y}")