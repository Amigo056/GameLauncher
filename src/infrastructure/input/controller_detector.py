import subprocess
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, List


@dataclass
class ControllerInfo:
    """Informação de um comando detetado pelo sistema."""
    guid: str           # SDL GUID único (ex: "030000004c050000cc09000011810000")
    name: str           # Nome do fabricante (ex: "PS4 Controller", "Xbox 360 Controller")
    vendor_id: str      # Para identificação
    product_id: str
    is_gamecontroller: bool  # Se tem mapeamento SDL2 nativo


class ControllerDetector:
    """Deteta comandos ligados ao PC via SDL2."""
    
    def __init__(self):
        self._sdl_path = self._find_sdl2_test()
    
    def _find_sdl2_test(self) -> Optional[Path]:
        """Procura por ferramenta SDL2 para listar comandos."""
        # Pode ser um pequeno exe SDL2 que distribuis com o launcher
        # ou usar pygame como fallback
        sdl_test = Path("tools/sdl2-controllers.exe")
        return sdl_test if sdl_test.exists() else None
    
    def list_controllers(self) -> List[ControllerInfo]:
        """Lista todos os comandos ligados."""
        controllers = []
        
        # Opção A: Usar SDL2 diretamente (mais fiável)
        if self._sdl_path:
            result = subprocess.run(
                [str(self._sdl_path), "--list"],
                capture_output=True, text=True
            )
            controllers = self._parse_sdl_output(result.stdout)
        
        # Opção B: Fallback com pygame (mais simples, menos fiável)
        else:
            controllers = self._list_via_pygame()
        
        return controllers
    
    def _parse_sdl_output(self, output: str) -> List[ControllerInfo]:
        """Parse do output do SDL2."""
        controllers = []
        for line in output.splitlines():
            # Formato: "030000004c050000cc09000011810000,PS4 Controller,..."
            if "," in line:
                parts = line.split(",")
                if len(parts) >= 2:
                    controllers.append(ControllerInfo(
                        guid=parts[0],
                        name=parts[1],
                        vendor_id="",
                        product_id="",
                        is_gamecontroller=True
                    ))
        return controllers
    
    def _list_via_pygame(self) -> List[ControllerInfo]:
        """Fallback usando pygame (requer instalação)."""
        try:
            import pygame
            pygame.init()
            pygame.joystick.init()
            
            controllers = []
            for i in range(pygame.joystick.get_count()):
                joy = pygame.joystick.Joystick(i)
                joy.init()
                controllers.append(ControllerInfo(
                    guid="unknown",
                    name=joy.get_name(),
                    vendor_id="",
                    product_id="",
                    is_gamecontroller=False
                ))
            return controllers
        except ImportError:
            return []
        finally:
            pygame.quit()