from core.emulator import Emulator
from core.game_library import GameLibrary
from typing import List, Dict

class PSPPPSPP(Emulator):
    def __init__(self, config_data: dict):
        super().__init__(config_data)
        self.library = GameLibrary(self.roms_folder, self.rom_extensions)
    
    def get_installed_games(self) -> List[Dict]:
        """Retorna jogos de PSP encontrados."""
        return self.library.scan_games()
    
    def launch_game(self, rom_path: str):
        """Lança jogo no PPSSPP."""
        # PPSSPP aceita o ROM diretamente
        super().launch_game(rom_path)