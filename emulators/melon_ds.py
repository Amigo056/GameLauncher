from core.emulator import Emulator
from core.game_library import GameLibrary
from typing import List, Dict
import os

class MelonDS(Emulator):
    def __init__(self, config_data: dict):
        super().__init__(config_data)
        self.library = GameLibrary(self.roms_folder, self.rom_extensions)
    
    def get_installed_games(self) -> List[Dict]:
        """Retorna jogos de NDS encontrados."""
        return self.library.scan_games()
    
    def launch_game(self, rom_path: str):
        """Lança jogo no melonDS."""
        # MelonDS aceita o ROM diretamente como argumento
        super().launch_game(rom_path)