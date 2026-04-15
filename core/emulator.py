import os
import subprocess
from abc import ABC, abstractmethod
from typing import List, Dict, Optional

class Emulator(ABC):
    def __init__(self, config_data: dict):
        self.id = config_data['id']
        self.name = config_data['name']
        self.icon_path = config_data['icon']
        self.exe_names = config_data['executable_names']
        self.default_paths = config_data['default_install_paths']
        self.rom_extensions = config_data['rom_extensions']
        self.roms_folder = config_data['roms_folder']
        self.launch_args = config_data['launch_args']
        self.executable_path = config_data.get('executable_path')
        self.is_installed = config_data.get('is_installed', False)
        
    def scan_installation(self) -> bool:
        """Procura o executável nos caminhos padrão."""
        for path_template in self.default_paths:
            path = os.path.expandvars(path_template)
            for exe_name in self.exe_names:
                full_path = os.path.join(path, exe_name)
                if os.path.exists(full_path):
                    self.executable_path = full_path
                    self.is_installed = True
                    return True
        return False
    
    @abstractmethod
    def get_installed_games(self) -> List[Dict]:
        """Retorna lista de jogos {nome, path, cover}."""
        pass
    
    def launch_game(self, rom_path: str):
        """Executa o emulador com o jogo."""
        if not self.executable_path or not os.path.exists(self.executable_path):
            raise FileNotFoundError(f"Emulador não encontrado: {self.executable_path}")
        
        args = self.launch_args.format(rom_path=rom_path)
        cmd = f'"{self.executable_path}" {args}'
        
        # Usar Popen para não bloquear a GUI
        subprocess.Popen(cmd, shell=True)
    
    def apply_safe_settings(self):
        """Aplica configs otimizadas para HP x360 (opcional)."""
        pass