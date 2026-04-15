from typing import Optional, Dict
from .melon_ds import MelonDS
from .psp import PSPPPSPP

class EmulatorFactory:
    @staticmethod
    def create(emulator_config: Dict) -> Optional[object]:
        """Cria instância do emulador apropriado baseado no ID."""
        emu_id = emulator_config.get('id')
        
        if emu_id == 'melonds':
            return MelonDS(emulator_config)
        elif emu_id == 'ppsspp':
            return PSPPPSPP(emulator_config)
        else:
            return None