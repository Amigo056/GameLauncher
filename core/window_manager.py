import json
import os
from typing import Dict, Any

class WindowManager:
    STATE_FILE = "config/settings.json"
    
    @staticmethod
    def save_state(window: Any):
        """Guarda estado atual da janela."""
        try:
            with open(WindowManager.STATE_FILE, 'r', encoding='utf-8') as f:
                settings = json.load(f)
            
            settings['window_state'] = {
                'width': window.winfo_width(),
                'height': window.winfo_height(),
                'x': window.winfo_x(),
                'y': window.winfo_y(),
                'maximized': window.state() == 'zoomed'
            }
            
            with open(WindowManager.STATE_FILE, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2)
        except Exception as e:
            print(f"Erro ao guardar estado: {e}")
    
    @staticmethod
    def restore_state(window: Any):
        """Restaura estado da janela."""
        try:
            with open(WindowManager.STATE_FILE, 'r', encoding='utf-8') as f:
                settings = json.load(f)
            
            state = settings.get('window_state', {})
            
            if state.get('maximized'):
                window.state('zoomed')
            else:
                window.geometry(f"{state.get('width', 800)}x{state.get('height', 600)}")
                window.geometry(f"+{state.get('x', 100)}+{state.get('y', 100)}")
                
        except Exception as e:
            print(f"Erro ao restaurar estado: {e}")
            window.geometry("800x600+100+100")