#!/usr/bin/env python3
import tkinter as tk
from gui.main_menu import MainMenu
import os

def ensure_directories():
    """Cria pastas necessárias se não existirem."""
    dirs = [
        "config",
        "assets/icons",
        "assets/covers",
        "roms/NDS",
        "roms/PSP"
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)

def main():
    # Criar estrutura de pastas
    ensure_directories()
    
    # Iniciar Tkinter
    root = tk.Tk()
    root.geometry("800x600")
    root.minsize(600, 400)
    
    # Tema escuro (Windows)
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except:
        pass
    
    # Iniciar app
    app = MainMenu(root)
    
    # Loop principal
    root.mainloop()

if __name__ == "__main__":
    main()