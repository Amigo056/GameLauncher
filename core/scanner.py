import os
import json
from pathlib import Path
from typing import List, Dict, Optional

class EmulatorScanner:
    def __init__(self, config_path: str = "config/emulators.json"):
        self.config_path = config_path
        self.emulators_config = self._load_config()
    
    def _load_config(self) -> List[Dict]:
        with open(self.config_path, 'r', encoding='utf-8') as f:
            return json.load(f)['emulators']
    
    def scan_all(self) -> List[Dict]:
        """Retorna lista de emuladores instalados com paths resolvidos."""
        installed = []
        for emu_config in self.emulators_config:
            exe_path = self._find_executable(emu_config)
            if exe_path:
                emu_data = emu_config.copy()
                emu_data['executable_path'] = exe_path
                emu_data['is_installed'] = True
                installed.append(emu_data)
        return installed
    
    def _find_executable(self, emu_config: Dict) -> Optional[str]:
        """Procura o executável nos caminhos padrão."""
        for path_template in emu_config['default_install_paths']:
            # Expandir variáveis de ambiente
            path = os.path.expandvars(path_template)
            for exe_name in emu_config['executable_names']:
                full_path = os.path.join(path, exe_name)
                if os.path.exists(full_path):
                    return full_path
        return None
    
    def get_emulator_by_id(self, emu_id: str) -> Optional[Dict]:
        """Retorna config de um emulador específico se instalado."""
        installed = self.scan_all()
        for emu in installed:
            if emu['id'] == emu_id:
                return emu
        return None