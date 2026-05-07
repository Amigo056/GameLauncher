# src/application/services/settings_service.py
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from src.domain.value_objects.graphics_profile import GraphicsProfileLevel


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
    graphics_profiles: dict[str, str] = field(default_factory=dict)
    favorite_games: dict[str, list[str]] = field(default_factory=dict)


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
                graphics_profiles=data.get("graphics_profiles", {}),
                favorite_games=self._normalize_favorites(
                    data.get("favorite_games", {})
                ),
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
            "graphics_profiles": settings.graphics_profiles,
            "favorite_games": settings.favorite_games,
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

    def get_graphics_profile(
        self,
        emulator_id: str,
        default: GraphicsProfileLevel = GraphicsProfileLevel.BALANCED,
    ) -> GraphicsProfileLevel:
        """Retorna o perfil grafico escolhido para um emulador."""
        settings = self.load()
        raw = settings.graphics_profiles.get(emulator_id, default.value)
        try:
            return GraphicsProfileLevel(raw)
        except ValueError:
            return default

    def save_graphics_profile(
        self,
        emulator_id: str,
        level: GraphicsProfileLevel,
    ) -> None:
        """Guarda o perfil grafico escolhido para um emulador."""
        settings = self.load()
        settings.graphics_profiles[emulator_id] = level.value
        self.save(settings)

    def get_favorite_games(self, emulator_id: str) -> set[str]:
        """Retorna os IDs favoritos para um emulador."""
        settings = self.load()
        return set(settings.favorite_games.get(emulator_id, []))

    def is_favorite_game(self, emulator_id: str, game_id: str) -> bool:
        """Verifica se um jogo esta marcado como favorito."""
        return game_id in self.get_favorite_games(emulator_id)

    def set_favorite_game(
        self,
        emulator_id: str,
        game_id: str,
        favorite: bool,
    ) -> bool:
        """Marca ou desmarca um jogo como favorito e retorna o novo estado."""
        settings = self.load()
        favorites = list(dict.fromkeys(settings.favorite_games.get(emulator_id, [])))

        if favorite and game_id not in favorites:
            favorites.append(game_id)
        elif not favorite:
            favorites = [current for current in favorites if current != game_id]

        settings.favorite_games[emulator_id] = favorites
        self.save(settings)
        return favorite

    def toggle_favorite_game(self, emulator_id: str, game_id: str) -> bool:
        """Alterna o favorito de um jogo e retorna o novo estado."""
        current = self.is_favorite_game(emulator_id, game_id)
        return self.set_favorite_game(emulator_id, game_id, not current)

    def _normalize_favorites(self, raw: object) -> dict[str, list[str]]:
        """Normaliza favoritos vindos do JSON antigo ou editado manualmente."""
        if not isinstance(raw, dict):
            return {}

        normalized: dict[str, list[str]] = {}
        for emulator_id, game_ids in raw.items():
            if not isinstance(emulator_id, str) or not isinstance(game_ids, list):
                continue
            normalized[emulator_id] = list(
                dict.fromkeys(str(game_id) for game_id in game_ids if game_id)
            )
        return normalized
