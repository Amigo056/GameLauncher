"""Gerenciamento de perfis de controlo: aplica configs no mupen64plus.cfg."""
import os
import platform
import shutil
from pathlib import Path
from typing import Optional

from src.infrastructure.adapters.controllers.sdl_to_n64_mapper import (
    N64ControllerProfile,
    SDLToN64Mapper,
)


class ProfileManager:
    """
    Responsável por:
    1. Guardar perfis JSON por emulador
    2. Aplicar perfil no mupen64plus.cfg real
    3. Fazer backup do cfg original
    """
    
    def __init__(self, profiles_dir: Path = Path("config/controller_profiles")):
        self.profiles_dir = Path(profiles_dir)
        self.profiles_dir.mkdir(parents=True, exist_ok=True)
        
        # Path do mupen64plus.cfg no AppData do user
        self.mupen_cfg_path = Path("emulators/M64Py/mupen64plus.cfg").resolve()
        self.mupen_cfg_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.mapper = SDLToN64Mapper()
    
    def get_profile_path(self, emulator_id: str, profile_name: str) -> Path:
        """Retorna path do perfil JSON."""
        return self.profiles_dir / f"{emulator_id}_{profile_name}.json"
    
    def save_profile(self, emulator_id: str, profile: N64ControllerProfile):
        """Guarda perfil em JSON."""
        import json
        
        path = self.get_profile_path(emulator_id, profile.name)
        
        # Serializar dataclass
        data = {
            "name": profile.name,
            "controller_name": profile.controller_name,
            "guid": profile.guid,
            "mappings": {}
        }
        
        # Mapear cada campo
        fields = [
            "dpad_up", "dpad_down", "dpad_left", "dpad_right",
            "start", "a_button", "b_button",
            "z_trig", "r_trig", "l_trig",
            "c_up", "c_down", "c_left", "c_right",
            "analog_x", "analog_y",
            "mempak_switch", "rumblepak_switch"
        ]
        
        for field_name in fields:
            mapping = getattr(profile, field_name)
            if mapping:
                data["mappings"][field_name] = {
                    "sdl_type": mapping.sdl_type,
                    "sdl_index": mapping.sdl_index,
                    "sdl_direction": mapping.sdl_direction
                }
            else:
                data["mappings"][field_name] = None
        
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        return path
    
    def load_profile(self, emulator_id: str, profile_name: str) -> Optional[N64ControllerProfile]:
        """Carrega perfil de JSON."""
        import json
        from src.infrastructure.adapters.controllers.sdl_to_n64_mapper import SDLMapping
        
        path = self.get_profile_path(emulator_id, profile_name)
        if not path.exists():
            return None
        
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Reconstruir N64ControllerProfile
        mappings = data.get("mappings", {})
        
        def get_mapping(field):
            m = mappings.get(field)
            if m:
                return SDLMapping(m["sdl_type"], m["sdl_index"], m.get("sdl_direction"))
            return None
        
        return N64ControllerProfile(
            name=data["name"],
            controller_name=data["controller_name"],
            guid=data.get("guid"),
            dpad_up=get_mapping("dpad_up"),
            dpad_down=get_mapping("dpad_down"),
            dpad_left=get_mapping("dpad_left"),
            dpad_right=get_mapping("dpad_right"),
            start=get_mapping("start"),
            a_button=get_mapping("a_button"),
            b_button=get_mapping("b_button"),
            z_trig=get_mapping("z_trig"),
            r_trig=get_mapping("r_trig"),
            l_trig=get_mapping("l_trig"),
            c_up=get_mapping("c_up"),
            c_down=get_mapping("c_down"),
            c_left=get_mapping("c_left"),
            c_right=get_mapping("c_right"),
            analog_x=get_mapping("analog_x"),
            analog_y=get_mapping("analog_y"),
            mempak_switch=get_mapping("mempak_switch"),
            rumblepak_switch=get_mapping("rumblepak_switch"),
        )
    
    def _get_screen_resolution(self) -> tuple[int, int]:
        """Deteta resolução nativa do monitor primário."""
        if platform.system() == "Windows":
            try:
                import ctypes
                user32 = ctypes.windll.user32
                return user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
            except Exception:
                pass
        # Fallback se não detetar
        return 1920, 1080

    def apply_to_mupen64plus(self, profile: N64ControllerProfile) -> bool:
        """
        Aplica perfil no mupen64plus.cfg real.
        Substitui a secção [Input-SDL-Control1] e garante vídeo fullscreen correto.
        """
        if not self.mupen_cfg_path.exists():
            self.mupen_cfg_path.parent.mkdir(parents=True, exist_ok=True)
            self.mupen_cfg_path.write_text("", encoding='utf-8')
        
        # Fazer backup
        backup = self.mupen_cfg_path.with_suffix(".cfg.backup")
        shutil.copy2(self.mupen_cfg_path, backup)
        
        # Ler cfg atual
        with open(self.mupen_cfg_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 1. Gerar nova secção de controlos
        new_section = self.mapper.generate_mupen64_config(profile)
        
        # Substituir secção existente ou adicionar no fim
        import re
        pattern = r'\[Input-SDL-Control1\].*?(?=\n\[|\Z)'
        if re.search(pattern, content, re.DOTALL):
            content = re.sub(pattern, new_section + "\n", content, flags=re.DOTALL)
        else:
            if content and not content.endswith("\n"):
                content += "\n"
            content += new_section + "\n"
        
        # 2. Garantir configuração de vídeo fullscreen com resolução nativa
        screen_w, screen_h = self._get_screen_resolution()
        
        video_section = (
            "[Video-General]\n"
            f"Fullscreen = True\n"
            f"ScreenWidth = {screen_w}\n"
            f"ScreenHeight = {screen_h}\n"
            "VerticalSync = True\n"
        )
        
        video_pattern = r'\[Video-General\].*?(?=\n\[|\Z)'
        if re.search(video_pattern, content, re.DOTALL):
            content = re.sub(video_pattern, video_section, content, flags=re.DOTALL)
        else:
            content += "\n" + video_section
        
        # 3. Guardar
        with open(self.mupen_cfg_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return True
    
    def list_saved_profiles(self, emulator_id: str) -> list[str]:
        """Lista perfis guardados para um emulador."""
        pattern = f"{emulator_id}_*.json"
        profiles = []
        for p in self.profiles_dir.glob(pattern):
            # Extrair nome do perfil do filename
            name = p.stem.replace(f"{emulator_id}_", "")
            profiles.append(name)
        return profiles
