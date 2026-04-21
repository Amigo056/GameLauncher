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
        "roms/NDS", "roms/PSP", "roms/N64",
    ]
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)


def main():
    ensure_directories()

    from src.presentation.app_navigator import AppNavigator

    root = tk.Tk()
    root.title("GameLauncher")
    root.geometry("1200x800")
    root.minsize(900, 600)
    root.configure(bg='#1e1e1e')

    root.grid_rowconfigure(0, weight=1)
    root.grid_columnconfigure(0, weight=1)

    navigator = AppNavigator(root)
    navigator.go_home()

    root.mainloop()


if __name__ == "__main__":
    main()