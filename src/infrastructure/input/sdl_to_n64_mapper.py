"""Converte comandos SDL2 para configuração Mupen64Plus."""

from dataclasses import dataclass
from typing import Dict, Optional
from pathlib import Path
import json

from src.infrastructure.input.controller_detector import ControllerInfo


@dataclass
class SDLMapping:
    """Mapeamento de um botão/axis SDL para ação N64."""
    sdl_type: str   # "button", "axis", "hat"
    sdl_index: int
    sdl_direction: Optional[str] = None  # "+" ou "-" para axes, "Up" etc para hats


@dataclass
class N64ControllerProfile:
    """Perfil completo de mapeamento N64."""
    name: str
    controller_name: str  # Nome do comando real
    guid: Optional[str] = None
    
    # Mapeamentos N64 → SDL
    dpad_up: Optional[SDLMapping] = None
    dpad_down: Optional[SDLMapping] = None
    dpad_left: Optional[SDLMapping] = None
    dpad_right: Optional[SDLMapping] = None
    
    start: Optional[SDLMapping] = None
    a_button: Optional[SDLMapping] = None
    b_button: Optional[SDLMapping] = None
    
    z_trig: Optional[SDLMapping] = None
    r_trig: Optional[SDLMapping] = None
    l_trig: Optional[SDLMapping] = None
    
    c_up: Optional[SDLMapping] = None
    c_down: Optional[SDLMapping] = None
    c_left: Optional[SDLMapping] = None
    c_right: Optional[SDLMapping] = None
    
    analog_x: Optional[SDLMapping] = None
    analog_y: Optional[SDLMapping] = None
    
    mempak_switch: Optional[SDLMapping] = None
    rumblepak_switch: Optional[SDLMapping] = None


class SDLToN64Mapper:
    """
    Converte qualquer comando SDL2 para configuração Mupen64Plus.
    """
    
    # Botões standard SDL2 (GameController)
    SDL_BUTTON_A = 0
    SDL_BUTTON_B = 1
    SDL_BUTTON_X = 2
    SDL_BUTTON_Y = 3
    SDL_BUTTON_BACK = 4
    SDL_BUTTON_GUIDE = 5
    SDL_BUTTON_START = 6
    SDL_BUTTON_LSTICK = 7
    SDL_BUTTON_RSTICK = 8
    SDL_BUTTON_LB = 9
    SDL_BUTTON_RB = 10
    SDL_BUTTON_DPAD_UP = 11
    SDL_BUTTON_DPAD_DOWN = 12
    SDL_BUTTON_DPAD_LEFT = 13
    SDL_BUTTON_DPAD_RIGHT = 14
    
    # Axes standard
    SDL_AXIS_LX = 0
    SDL_AXIS_LY = 1
    SDL_AXIS_RX = 2
    SDL_AXIS_RY = 3
    SDL_AXIS_LT = 4
    SDL_AXIS_RT = 5

    def __init__(self):
            pass
    
    def _deserialize_profile(self, data: dict) -> N64ControllerProfile:
        """Converte dict para objeto N64ControllerProfile."""
        
        def get_mapping(field_name: str) -> Optional[SDLMapping]:
            m = data.get("mappings", {}).get(field_name)
            if m:
                return SDLMapping(
                    sdl_type=m["sdl_type"],
                    sdl_index=m["sdl_index"],
                    sdl_direction=m.get("sdl_direction")
                )
            return None
        
        return N64ControllerProfile(
            name=data.get("name", "Unknown"),
            controller_name=data.get("controller_name", "Unknown"),
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
    
    def create_default_profile(self, controller_info: ControllerInfo) -> N64ControllerProfile:
        """Cria perfil automático baseado no tipo de comando."""
        name = controller_info.name.lower()
        
        if "ps4" in name or "dualshock 4" in name:
            return self._create_ps4_profile()
        elif "xbox" in name or "x360" in name:
            return self._create_xbox_profile()
        elif "switch" in name or "pro controller" in name:
            return self._create_switch_profile()
        else:
            return self._create_generic_profile()
    
    def _create_ps4_profile(self) -> N64ControllerProfile:
        """Perfil PS4 com índices reais do teste."""
        return N64ControllerProfile(
            name="PS4 Default",
            controller_name="PS4 Controller",
            
            # D-Pad → BOTÕES (não hat!) 11-14
            dpad_up=SDLMapping("button", 11),
            dpad_down=SDLMapping("button", 12),
            dpad_left=SDLMapping("button", 13),
            dpad_right=SDLMapping("button", 14),
            
            # Start → Options (SDL standard = 6)
            start=SDLMapping("button", 6),
            
            # X (□) → A Button (índice 0 no teu teste)
            a_button=SDLMapping("button", 0),
            
            # O (○) → B Button (índice 1 no teu teste)
            b_button=SDLMapping("button", 1),
            
            # L2 (Axis 4) → Z Trigger
            z_trig=SDLMapping("axis", 4, "+"),
            
            # R1 → R Trigger (índice 10)
            r_trig=SDLMapping("button", 10),
            
            # L1 → L Trigger (índice 9)
            l_trig=SDLMapping("button", 9),
            
            # C-Buttons no Right Stick (mantém)
            c_up=SDLMapping("axis", 3, "-"),
            c_down=SDLMapping("axis", 3, "+"),
            c_left=SDLMapping("axis", 2, "-"),
            c_right=SDLMapping("axis", 2, "+"),
            
            # Analog Stick (Left Stick) → eixos 0 e 1
            analog_x=SDLMapping("axis", 0),
            analog_y=SDLMapping("axis", 1),
            
            # Extras
            mempak_switch=SDLMapping("button", 7),   # L3
            rumblepak_switch=SDLMapping("button", 5), # PS
        )
    
    def _create_xbox_profile(self) -> N64ControllerProfile:
        """Perfil otimizado para Xbox."""
        return N64ControllerProfile(
            name="Xbox Default",
            controller_name="Xbox Controller",
            dpad_up=SDLMapping("hat", 0, "Up"),
            dpad_down=SDLMapping("hat", 0, "Down"),
            dpad_left=SDLMapping("hat", 0, "Left"),
            dpad_right=SDLMapping("hat", 0, "Right"),
            start=SDLMapping("button", self.SDL_BUTTON_START),
            a_button=SDLMapping("button", self.SDL_BUTTON_A),
            b_button=SDLMapping("button", self.SDL_BUTTON_B),
            z_trig=SDLMapping("axis", self.SDL_AXIS_LT, "+"),
            r_trig=SDLMapping("button", self.SDL_BUTTON_RB),
            l_trig=SDLMapping("button", self.SDL_BUTTON_LB),
            c_up=SDLMapping("axis", self.SDL_AXIS_RY, "-"),
            c_down=SDLMapping("axis", self.SDL_AXIS_RY, "+"),
            c_left=SDLMapping("axis", self.SDL_AXIS_RX, "-"),
            c_right=SDLMapping("axis", self.SDL_AXIS_RX, "+"),
            analog_x=SDLMapping("axis", self.SDL_AXIS_LX),
            analog_y=SDLMapping("axis", self.SDL_AXIS_LY),
            mempak_switch=SDLMapping("button", self.SDL_BUTTON_BACK),
            rumblepak_switch=SDLMapping("button", self.SDL_BUTTON_GUIDE),
        )
    
    def _create_switch_profile(self) -> N64ControllerProfile:
        """Perfil para Switch Pro Controller."""
        return N64ControllerProfile(
            name="Switch Default",
            controller_name="Switch Pro Controller",
            dpad_up=SDLMapping("hat", 0, "Up"),
            dpad_down=SDLMapping("hat", 0, "Down"),
            dpad_left=SDLMapping("hat", 0, "Left"),
            dpad_right=SDLMapping("hat", 0, "Right"),
            start=SDLMapping("button", self.SDL_BUTTON_START),
            a_button=SDLMapping("button", self.SDL_BUTTON_A),
            b_button=SDLMapping("button", self.SDL_BUTTON_B),
            z_trig=SDLMapping("axis", self.SDL_AXIS_LT, "+"),
            r_trig=SDLMapping("button", self.SDL_BUTTON_RB),
            l_trig=SDLMapping("button", self.SDL_BUTTON_LB),
            c_up=SDLMapping("axis", self.SDL_AXIS_RY, "-"),
            c_down=SDLMapping("axis", self.SDL_AXIS_RY, "+"),
            c_left=SDLMapping("axis", self.SDL_AXIS_RX, "-"),
            c_right=SDLMapping("axis", self.SDL_AXIS_RX, "+"),
            analog_x=SDLMapping("axis", self.SDL_AXIS_LX),
            analog_y=SDLMapping("axis", self.SDL_AXIS_LY),
            mempak_switch=SDLMapping("button", self.SDL_BUTTON_BACK),
            rumblepak_switch=SDLMapping("button", self.SDL_BUTTON_GUIDE),
        )
    
    def _create_generic_profile(self) -> N64ControllerProfile:
        """Perfil genérico para comandos sem identificação."""
        return N64ControllerProfile(
            name="Generic Default",
            controller_name="Generic Controller",
            dpad_up=SDLMapping("hat", 0, "Up"),
            dpad_down=SDLMapping("hat", 0, "Down"),
            dpad_left=SDLMapping("hat", 0, "Left"),
            dpad_right=SDLMapping("hat", 0, "Right"),
            start=SDLMapping("button", self.SDL_BUTTON_START),
            a_button=SDLMapping("button", self.SDL_BUTTON_A),
            b_button=SDLMapping("button", self.SDL_BUTTON_B),
            z_trig=SDLMapping("axis", self.SDL_AXIS_LT, "+"),
            r_trig=SDLMapping("button", self.SDL_BUTTON_RB),
            l_trig=SDLMapping("button", self.SDL_BUTTON_LB),
            c_up=SDLMapping("axis", self.SDL_AXIS_RY, "-"),
            c_down=SDLMapping("axis", self.SDL_AXIS_RY, "+"),
            c_left=SDLMapping("axis", self.SDL_AXIS_RX, "-"),
            c_right=SDLMapping("axis", self.SDL_AXIS_RX, "+"),
            analog_x=SDLMapping("axis", self.SDL_AXIS_LX),
            analog_y=SDLMapping("axis", self.SDL_AXIS_LY),
            mempak_switch=SDLMapping("button", self.SDL_BUTTON_BACK),
            rumblepak_switch=SDLMapping("button", self.SDL_BUTTON_GUIDE),
        )
    
    def generate_mupen64_config(self, profile: N64ControllerProfile) -> str:
        """Gera a secção [Input-SDL-Control1] para o mupen64plus.cfg."""
        lines = [
            "[Input-SDL-Control1]",
            "version = 2.000000",
            "mode = 0",
            "device = 0",
            f'name = "{profile.controller_name}"',
            "plugged = True",
            "plugin = 2",
            "mouse = False",
            'MouseSensitivity = "2.00,2.00"',
            'AnalogDeadzone = "4096,4096"',
            'AnalogPeak = "32768,32768"',
        ]
        
        def fmt_mapping(m: Optional[SDLMapping]) -> str:
            if not m:
                return '""'
            if m.sdl_type == "button":
                return f'"button({m.sdl_index})"'
            elif m.sdl_type == "axis":
                direction = m.sdl_direction or ""
                if direction:
                    # Gatilho ou C-Button numa direção só (ex: axis(4+), axis(3-))
                    return f'"axis({m.sdl_index}{direction})"'
                else:
                    # Eixo analógico bidirecional — stick precisa de ambas as direções
                    return f'"axis({m.sdl_index}-,{m.sdl_index}+)"'
            elif m.sdl_type == "hat":
                return f'"hat(0 {m.sdl_direction})"'
            return '""'
        
        lines.extend([
            f'DPad R = {fmt_mapping(profile.dpad_right)}',
            f'DPad L = {fmt_mapping(profile.dpad_left)}',
            f'DPad D = {fmt_mapping(profile.dpad_down)}',
            f'DPad U = {fmt_mapping(profile.dpad_up)}',
            f'Start = {fmt_mapping(profile.start)}',
            f'Z Trig = {fmt_mapping(profile.z_trig)}',
            f'B Button = {fmt_mapping(profile.b_button)}',
            f'A Button = {fmt_mapping(profile.a_button)}',
            f'C Button R = {fmt_mapping(profile.c_right)}',
            f'C Button L = {fmt_mapping(profile.c_left)}',
            f'C Button D = {fmt_mapping(profile.c_down)}',
            f'C Button U = {fmt_mapping(profile.c_up)}',
            f'R Trig = {fmt_mapping(profile.r_trig)}',
            f'L Trig = {fmt_mapping(profile.l_trig)}',
            f'Mempak switch = {fmt_mapping(profile.mempak_switch)}',
            f'Rumblepak switch = {fmt_mapping(profile.rumblepak_switch)}',
            f'X Axis = {fmt_mapping(profile.analog_x)}',
            f'Y Axis = {fmt_mapping(profile.analog_y)}',
        ])
        
        return "\n".join(lines)
    