import time
import tkinter as tk
from typing import Callable

from src.infrastructure.input.controller_detector import ControllerDetector
from src.infrastructure.input.sdl_to_n64_mapper import SDLToN64Mapper, N64ControllerProfile
from src.infrastructure.input.profile_manager import ProfileManager
from src.presentation.widgets.toast import Toast
from src.presentation.theme import DARK_THEME, font, mono_font


class ControllerConfigPage:
    """
    Página de configuração de controlos por emulador.
    """

    def __init__(
        self,
        parent: tk.Widget,
        emulator_id: str,
        on_back: Callable,
    ):
        t = DARK_THEME
        self.frame = tk.Frame(parent, bg=t.bg_primary)
        self.emulator_id = emulator_id
        self.on_back = on_back
        
        self.detector = ControllerDetector()
        self.mapper = SDLToN64Mapper()
        self.profile_manager = ProfileManager()
        
        self.current_profile: N64ControllerProfile | None = None
        
        self._build_ui()
        self._detect_controllers()

    def _build_ui(self):
        """Constrói interface de configuração."""
        t = DARK_THEME
        
        # Header
        header = tk.Frame(self.frame, bg=t.bg_primary, padx=20, pady=15)
        header.pack(fill='x')
        
        tk.Button(
            header,
            text="← Voltar",
            font=font(t, "font_size_md"),
            bg=t.bg_tertiary,
            fg=t.text_primary,
            relief='flat',
            cursor='hand2',
            command=self.on_back
        ).pack(side='left')
        
        tk.Label(
            header,
            text=f"⚙️ Controlos - {self.emulator_id.upper()}",
            bg=t.bg_primary,
            fg=t.text_primary,
            font=font(t, "font_size_2xl", bold=True)
        ).pack(side='left', padx=20)

        # Container principal
        main = tk.Frame(self.frame, bg=t.bg_primary)
        main.pack(fill='both', expand=True, padx=20, pady=10)

        # Painel esquerdo: Status + Perfis
        left = tk.Frame(main, bg=t.bg_primary)
        left.pack(side='left', fill='y')

        # Status do comando
        self.lbl_status = tk.Label(
            left,
            text="🔍 A procurar comando…",
            bg=t.bg_primary,
            fg=t.text_secondary,
            font=font(t, "font_size_md")
        )
        self.lbl_status.pack(pady=(0, 20))

        # Secção: Perfil Automático
        tk.Label(
            left,
            text="Perfil Automático",
            bg=t.bg_primary,
            fg=t.text_primary,
            font=font(t, "font_size_lg", bold=True)
        ).pack(anchor='w', pady=(20, 5))

        profiles = [
            ("🎮 PS4 / DualShock 4", self._apply_ps4),
            ("🎮 Xbox 360/One/Series", self._apply_xbox),
            ("🎮 Nintendo Switch Pro", self._apply_switch),
            ("🎮 Genérico / Outro", self._apply_generic),
            ("🔍 Auto-Detetar", self._auto_detect),
        ]

        for name, cmd in profiles:
            btn = tk.Button(
                left,
                text=name,
                font=font(t, "font_size_md"),
                bg=t.bg_card,
                fg=t.text_primary,
                activebackground=t.bg_hover,
                activeforeground=t.text_primary,
                relief='flat',
                cursor='hand2',
                width=25,
                command=cmd
            )
            btn.pack(pady=3)

        # Secção: Ação
        tk.Label(
            left,
            text="Ação",
            bg=t.bg_primary,
            fg=t.text_primary,
            font=font(t, "font_size_lg", bold=True)
        ).pack(anchor='w', pady=(30, 5))

        tk.Button(
            left,
            text="🎮 Testar Comando",
            font=font(t, "font_size_md"),
            bg=t.bg_card, fg=t.text_primary,
            relief='flat', cursor='hand2',
            width=25, command=self._test_controller
        ).pack(pady=5)

        tk.Button(
            left,
            text="💾 Guardar e Aplicar",
            font=font(t, "font_size_lg", bold=True),
            bg=t.accent,
            fg=t.text_primary,
            activebackground=t.accent_hover,
            relief='flat',
            cursor='hand2',
            width=25,
            height=2,
            command=self._save
        ).pack(pady=5)

        # Painel direito: Preview do mapeamento
        right = tk.Frame(main, bg=t.bg_secondary, padx=20, pady=20)
        right.pack(side='left', fill='both', expand=True, padx=(20, 0))

        tk.Label(
            right,
            text="Preview do Mapeamento",
            bg=t.bg_secondary,
            fg=t.text_primary,
            font=font(t, "font_size_xl", bold=True)
        ).pack(anchor='w', pady=(0, 10))

        self.txt_preview = tk.Text(
            right,
            bg=t.bg_primary,
            fg=t.text_muted,
            font=mono_font(t, "font_size_sm"),
            height=25,
            width=50,
            relief='flat',
            state='disabled'
        )
        self.txt_preview.pack(fill='both', expand=True)

    def _update_preview(self):
        """Atualiza o preview do mapeamento."""
        if not self.current_profile:
            return
        
        config = self.mapper.generate_mupen64_config(self.current_profile)
        
        self.txt_preview.config(state='normal')
        self.txt_preview.delete('1.0', 'end')
        self.txt_preview.insert('1.0', config)
        self.txt_preview.config(state='disabled')

    def _detect_controllers(self):
        """Deteta comandos ligados."""
        t = DARK_THEME
        controllers = self.detector.list_controllers()
        if controllers:
            self.lbl_status.config(
                text=f"✅ Comando: {controllers[0].name}",
                fg=t.success
            )
        else:
            self.lbl_status.config(
                text="❌ Nenhum comando ligado\nLiga um comando USB/Bluetooth",
                fg=t.error
            )

    def _apply_ps4(self):
        """Aplica perfil PS4."""
        from src.infrastructure.input.controller_detector import ControllerInfo
        info = ControllerInfo(
            guid="", name="PS4 Controller",
            vendor_id="", product_id="", is_gamecontroller=True
        )
        self.current_profile = self.mapper.create_default_profile(info)
        self._update_preview()
        Toast.show(self.frame, "✅ Perfil PS4 carregado!", level="success", duration=3000)

    def _apply_xbox(self):
        """Aplica perfil Xbox."""
        from src.infrastructure.input.controller_detector import ControllerInfo
        info = ControllerInfo(
            guid="", name="Xbox Controller",
            vendor_id="", product_id="", is_gamecontroller=True
        )
        self.current_profile = self.mapper.create_default_profile(info)
        self._update_preview()
        Toast.show(self.frame, "✅ Perfil Xbox carregado!", level="success", duration=3000)

    def _apply_switch(self):
        """Aplica perfil Switch."""
        from src.infrastructure.input.controller_detector import ControllerInfo
        info = ControllerInfo(
            guid="", name="Switch Pro Controller",
            vendor_id="", product_id="", is_gamecontroller=True
        )
        self.current_profile = self.mapper.create_default_profile(info)
        self._update_preview()
        Toast.show(self.frame, "✅ Perfil Switch carregado!", level="success", duration=3000)

    def _apply_generic(self):
        """Aplica perfil genérico."""
        from src.infrastructure.input.controller_detector import ControllerInfo
        info = ControllerInfo(
            guid="", name="Generic Controller",
            vendor_id="", product_id="", is_gamecontroller=True
        )
        self.current_profile = self.mapper.create_default_profile(info)
        self._update_preview()
        Toast.show(self.frame, "✅ Perfil Genérico carregado!", level="success", duration=3000)

    def _auto_detect(self):
        """Tenta detetar automaticamente."""
        controllers = self.detector.list_controllers()
        if not controllers:
            Toast.show(
                self.frame,
                "Nenhum comando detetado!\n\nLiga um comando e tenta novamente.",
                level="error",
                duration=5000
            )
            return
        
        self.current_profile = self.mapper.create_default_profile(controllers[0])
        self._update_preview()
        Toast.show(
            self.frame,
            f"Perfil aplicado para:\n{controllers[0].name}",
            level="success",
            duration=3000
        )

    def _save(self):
        """Guarda e aplica configuração."""
        if not self.current_profile:
            Toast.show(
                self.frame,
                "Nenhum perfil configurado!\nSeleciona um perfil primeiro.",
                level="warning",
                duration=4000
            )
            return
        
        try:
            # 1. Guardar perfil JSON
            self.profile_manager.save_profile(self.emulator_id, self.current_profile)
            
            # 2. Aplicar no mupen64plus.cfg
            success = self.profile_manager.apply_to_mupen64plus(self.current_profile)
            
            if success:
                Toast.show(
                    self.frame,
                    f"✅ Configuração guardada e aplicada!\n\n"
                    f"A configuração foi escrita em:\n"
                    f"{self.profile_manager.mupen_cfg_path}",
                    level="success",
                    duration=5000
                )
            else:
                Toast.show(
                    self.frame,
                    "Perfil guardado mas houve erro ao aplicar no mupen64plus.cfg",
                    level="warning",
                    duration=4000
                )
                
        except Exception as e:
            Toast.show(
                self.frame,
                f"Falha ao guardar: {e}",
                level="error",
                duration=5000
            )

    def _test_controller(self):
        """Abre janela de teste para ver os índices reais dos botões."""
        import threading
        import pygame
        
        t = DARK_THEME
        test_window = tk.Toplevel(self.frame)
        test_window.title("Testar Comando")
        test_window.geometry("400x500")
        test_window.configure(bg=t.bg_primary)
        
        tk.Label(
            test_window,
            text="Pressiona botões no comando para ver os índices",
            bg=t.bg_primary, fg=t.text_primary,
            font=font(t, "font_size_md", bold=True)
        ).pack(pady=10)
        
        # Labels para mostrar estado
        lbl_info = tk.Label(
            test_window, text="Aguardando input…",
            bg=t.bg_primary, fg=t.success,
            font=mono_font(t, "font_size_sm")
        )
        lbl_info.pack(pady=10)
        
        txt_log = tk.Text(
            test_window, bg=t.bg_card, fg=t.text_muted,
            font=mono_font(t, "font_size_sm"), height=20, width=45
        )
        txt_log.pack(padx=10, pady=10)
        
        self._test_running = True
        
        def listen():
            try:
                pygame.init()
                pygame.joystick.init()
                
                if pygame.joystick.get_count() == 0:
                    test_window.after(0, lambda: lbl_info.config(
                        text="❌ Nenhum comando detetado", fg=t.error
                    ))
                    return
                
                joy = pygame.joystick.Joystick(0)
                joy.init()
                
                # Estado anterior para detectar mudanças
                prev_buttons = [False] * joy.get_numbuttons()
                prev_axes = [0.0] * joy.get_numaxes()
                prev_hats = [(0, 0)] * joy.get_numhats()
                
                test_window.after(0, lambda: lbl_info.config(
                    text=f"✅ Comando: {joy.get_name()}\n"
                         f"Botões: {joy.get_numbuttons()} | "
                         f"Axes: {joy.get_numaxes()} | "
                         f"Hats: {joy.get_numhats()}",
                    fg=t.success
                ))
                
                while self._test_running and test_window.winfo_exists():
                    pygame.event.pump()
                    
                    # Verificar botões
                    for i in range(joy.get_numbuttons()):
                        state = joy.get_button(i)
                        if state and not prev_buttons[i]:
                            msg = f"[BUTTON] Índice {i} pressionado\n"
                            test_window.after(0, lambda m=msg: txt_log.insert('end', m) or txt_log.see('end'))
                        prev_buttons[i] = state
                    
                    # Verificar axes (movimento significativo)
                    for i in range(joy.get_numaxes()):
                        val = joy.get_axis(i)
                        if abs(val) > 0.5 and abs(prev_axes[i]) <= 0.5:
                            msg = f"[AXIS] Índice {i} valor {val:+.2f}\n"
                            test_window.after(0, lambda m=msg: txt_log.insert('end', m) or txt_log.see('end'))
                        prev_axes[i] = val
                    
                    # Verificar hats (d-pad)
                    for i in range(joy.get_numhats()):
                        val = joy.get_hat(i)
                        if val != (0, 0) and prev_hats[i] == (0, 0):
                            msg = f"[HAT] Índice {i} direção {val}\n"
                            test_window.after(0, lambda m=msg: txt_log.insert('end', m) or txt_log.see('end'))
                        prev_hats[i] = val
                    
                    time.sleep(0.05)
                    
            except Exception as e:
                test_window.after(0, lambda: lbl_info.config(
                    text=f"Erro: {e}", fg=t.error
                ))
            finally:
                pygame.quit()
        
        # Botão fechar
        def on_close():
            self._test_running = False
            test_window.destroy()
        
        tk.Button(
            test_window, text="Fechar", command=on_close,
            bg=t.bg_tertiary, fg=t.text_primary,
            font=font(t, "font_size_md"), relief='flat', cursor='hand2'
        ).pack(pady=10)
        
        test_window.protocol("WM_DELETE_WINDOW", on_close)
        
        # Iniciar thread de escuta
        threading.Thread(target=listen, daemon=True).start()

    def destroy(self):
        """Esconde em vez de destruir."""
        self.frame.place_forget()