"""Entidade Emulator: Configuração pura de emuladores."""
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Dict
from enum import Enum
import platform

class Platform(Enum):
    """Plataformas suportadas."""
    NINTENDO_DS = "nintendo-ds"
    PLAYSTATION_PORTABLE = "playstation-portable"
    NINTENDO_64 = "nintendo-64"
    GAME_BOY_ADVANCE      = "game-boy-advance"
    UNKNOWN = "unknown"

@dataclass(frozen=True)
class EmulatorConfig:
    """Value Object: Configurações de execução seguras."""
    safe_settings: Dict[str, str] = field(default_factory=dict)
    config_file_path: Optional[Path] = None 
    
    def get_setting(self, key: str, default: str = "") -> str:
        """Obtém setting seguro."""
        return self.safe_settings.get(key, default)

@dataclass
class Emulator:
    """Entidade: Representa um emulador instalado."""
    id: str  # "melonds", "ppsspp"
    name: str  # "Nintendo DS"
    platform: Platform
    icon_path: Optional[Path]               = None
    executable_path: Optional[Path]         = None  # Path real do .exe
    executable_names: List[str]             = field(default_factory=list)  # Nomes possíveis
    default_install_paths: List[Path]       = field(default_factory=list)  # Caminhos padrão
    supported_extensions: List[str]         = field(default_factory=list)  # [".nds", ".zip"]
    roms_folder: Path                       = field(default=Path("roms"))
    launch_args_template: str               = '"{rom_path}"'  # Template: {rom_path}
    config: EmulatorConfig                  = field(default_factory=EmulatorConfig)
    save_dir: Optional[Path]                = None

    def __post_init__(self):
        if not self.id:
            raise ValueError("Emulator.id não pode ser vazio")
        # Normalizar extensões para lowercase
        self.supported_extensions = [
            ext.lower() if ext.startswith('.') else f'.{ext.lower()}'
            for ext in self.supported_extensions
        ]
    
    @property
    def is_installed(self) -> bool:
        """Verifica se o executável foi localizado."""
        return self.executable_path is not None and self.executable_path.exists()
    
    @property
    def roms_directory(self) -> Path:
        """Retorna pasta de ROMs específica do emulador."""
        return self.roms_folder
    
    def _get_screen_resolution(self) -> tuple[int, int]:
        """Deteta resolução nativa do monitor primário."""
        if platform.system() == "Windows":
            try:
                import ctypes
                user32 = ctypes.windll.user32
                return user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
            except Exception:
                pass
        return 1920, 1080

    def build_launch_command(self, rom_path: Path) -> str:
        """Constrói comando de lançamento completo."""
        if not self.is_installed:
            raise RuntimeError(f"Emulador {self.name} não está instalado")
        
        if not rom_path.exists():
            raise FileNotFoundError(f"ROM não encontrada: {rom_path}")
        
        rom_abs = rom_path.resolve()
        rom_str = str(rom_abs).replace('"', '\\"')
        
        exe_abs = self.executable_path.resolve()
        emulator_dir = str(exe_abs.parent).replace('"', '\\"')
        
        args = self.launch_args_template.format(
            rom_path=rom_str,
            emulator_dir=emulator_dir
        )
        if self.id == "mupen64plus":
            screen_w, screen_h = self._get_screen_resolution()
            resolution_arg = f"--resolution {screen_w}x{screen_h}"
            return f'"{exe_abs}" {resolution_arg} {args}'

        return f'"{exe_abs}" {args}'
    
    def supports_extension(self, ext: str) -> bool:
        """Verifica se extensão é suportada."""
        ext = ext.lower()
        if not ext.startswith('.'):
            ext = f'.{ext}'
        return ext in self.supported_extensions
    
def load_emulator_from_json(
        emu_id: str, 
        config_path: Path = Path("config/emulators.json")
) -> Optional[Emulator]:
    """
    Carrega configuração de emulador do ficheiro JSON.
    Tenta detectar automaticamente o executável nos caminhos padrão.
    """
    import json
    import os
    
    if not config_path.exists():
        return None
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Encontrar config do emulador específico
        emu_config = next(
            (e for e in data.get('emulators', []) if e['id'] == emu_id),
            None
        )
        
        if not emu_config:
            return None
        
        # Mapear plataforma
        platform_map = {
            'melonds':      Platform.NINTENDO_DS,
            'ppsspp':       Platform.PLAYSTATION_PORTABLE,
            'mupen64plus':  Platform.NINTENDO_64,
            'mgba':         Platform.GAME_BOY_ADVANCE,

        }

        emu_platform = platform_map.get(emu_id.lower(), Platform.UNKNOWN)
        
        # Converter paths string para Path objects
        project_root = Path(__file__).parent.parent.parent.parent  # até à raiz
        
        project_paths = [
            project_root / "emulators" / emu_id,
            project_root / "emulators" / emu_id.lower(),
        ]

        default_paths = project_paths + [
            Path(p) for p in emu_config.get('default_install_paths', [])
        ]
        
        # Tentar encontrar executável
        exe_path = None
        for path in default_paths:
            # Expandir variáveis de ambiente (ex: %PROGRAMFILES%)
            expanded_path = Path(os.path.expandvars(str(path)))
            for exe_name in emu_config.get('executable_names', []):
                full_path = expanded_path / exe_name
                if full_path.exists():
                    exe_path = full_path
                    break
            if exe_path:
                break
        
        # Criar config de segurança
        safe_settings = emu_config.get('safe_settings', {})
        emulator_config = EmulatorConfig(
            safe_settings=safe_settings,
            config_file_path=Path(os.path.expandvars(emu_config.get('config_file', ''))) 
            if emu_config.get('config_file') else None
        )

        roms_folder = Path(emu_config.get('roms_folder', 'roms'))
        
        return Emulator(
            id=emu_config['id'],
            name=emu_config['name'],
            platform=emu_platform,
            icon_path=Path(emu_config['icon']) if emu_config.get('icon') else None,
            executable_path=exe_path,
            executable_names=emu_config.get('executable_names', []),
            default_install_paths=default_paths,
            supported_extensions=emu_config.get('rom_extensions', []),
            roms_folder=roms_folder,
            launch_args_template=emu_config.get('launch_args', '"{rom_path}"'),
            config=emulator_config,
            save_dir=roms_folder if emu_id == 'mgba' else None
        )
        
    except Exception as e:
        print(f"Erro ao carregar configuração do emulador: {e}")
        return None