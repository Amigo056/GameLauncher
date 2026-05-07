"""Entry point da aplicação GameLauncher."""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.resolve()
sys.path.insert(0, str(PROJECT_ROOT))

import tkinter as tk


def ensure_directories():
    """Cria estrutura de pastas necessária."""
    dirs = [
        "assets/covers", "assets/icons",
        "roms/NDS", "roms/PSP", 
        "roms/N64", "roms/GBA",
        "logs",
    ]
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)


def main():
    ensure_directories()

    # Logging centralizado (escreve em logs/gamelauncher.log)
    from src.infrastructure.logging_config import setup_logging
    setup_logging()

    from src.presentation.app_navigator import AppNavigator
    from src.application.services.settings_service import SettingsService
    from src.presentation.theme import DARK_THEME

    settings_service = SettingsService()

    root = tk.Tk()
    root.title("GameLauncher")
    root.minsize(900, 600)
    root.configure(bg=DARK_THEME.bg_primary)

    root.grid_rowconfigure(0, weight=1)
    root.grid_columnconfigure(0, weight=1)

    # Restaurar tamanho/posição da janela da sessão anterior
    settings_service.apply_window_state(root)

    # Guardar estado ao fechar
    def on_close():
        settings_service.save_window_state(root)
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_close)

    navigator = AppNavigator(root)
    navigator.go_home()

    root.mainloop()


if __name__ == "__main__":
    from src.domain.entities.emulator import load_emulator_from_json
    emu = load_emulator_from_json("mgba")
    print(f"mGBA path: {emu.executable_path if emu else 'NÃO ENCONTRADO'}")
    print(f"mGBA installed: {emu.is_installed if emu else False}")
    main()