import time
import tkinter as tk
from tkinter import messagebox
from typing import Callable

from src.infrastructure.input.controller_detector import ControllerDetector
from src.infrastructure.input.sdl_to_n64_mapper import SDLToN64Mapper, N64ControllerProfile
from src.infrastructure.input.profile_manager import ProfileManager


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
        self.frame = tk.Frame(parent, bg='#1e1e1e')
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
        # Header
        header = tk.Frame(self.frame, bg='#1e1e1e', padx=20, pady=15)
        header.pack(fill='x')
        
        tk.Button(
            header,
            text="← Voltar",
            font=('Segoe UI', 11),
            bg='#333333',
            fg='white',
            relief='flat',
            cursor='hand2',
            command=self.on_back
        ).pack(side='left')
        
        tk.Label(
            header,
            text=f"⚙️ Controlos - {self.emulator_id.upper()}",
            bg='#1e1e1e',
            fg='white',
            font=('Segoe UI', 18, 'bold')
        ).pack(side='left', padx=20)

        # Container principal
        main = tk.Frame(self.frame, bg='#1e1e1e')
        main.pack(fill='both', expand=True, padx=20, pady=10)

        # Painel esquerdo: Status + Perfis
        left = tk.Frame(main, bg='#1e1e1e')
        left.pack(side='left', fill='y')

        # Status do comando
        self.lbl_status = tk.Label(
            left,
            text="🔍 A procurar comando...",
            bg='#1e1e1e',
            fg='#888888',
            font=('Segoe UI', 11)
        )
        self.lbl_status.pack(pady=(0, 20))

        # Secção: Perfil Automático
        tk.Label(
            left,
            text="Perfil Automático",
            bg='#1e1e1e',
            fg='white',
            font=('Segoe UI', 12, 'bold')
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
                font=('Segoe UI', 10),
                bg='#2d2d2d',
                fg='white',
                activebackground='#3d3d3d',
                activeforeground='white',
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
            bg='#1e1e1e',
            fg='white',
            font=('Segoe UI', 12, 'bold')
        ).pack(anchor='w', pady=(30, 5))

        tk.Button(
            left,
            text="🎮 Testar Comando",
            font=('Segoe UI', 10),
            bg='#2d2d2d', fg='white',
            relief='flat', cursor='hand2',
            width=25, command=self._test_controller
        ).pack(pady=5)

        tk.Button(
            left,
            text="💾 Guardar e Aplicar",
            font=('Segoe UI', 11, 'bold'),
            bg='#0078d4',
            fg='white',
            activebackground='#106ebe',
            relief='flat',
            cursor='hand2',
            width=25,
            height=2,
            command=self._save
        ).pack(pady=5)

        # Painel direito: Preview do mapeamento
        right = tk.Frame(main, bg='#252525', padx=20, pady=20)
        right.pack(side='left', fill='both', expand=True, padx=(20, 0))

        tk.Label(
            right,
            text="Preview do Mapeamento",
            bg='#252525',
            fg='white',
            font=('Segoe UI', 14, 'bold')
        ).pack(anchor='w', pady=(0, 10))

        self.txt_preview = tk.Text(
            right,
            bg='#1e1e1e',
            fg='#cccccc',
            font=('Consolas', 10),
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
        controllers = self.detector.list_controllers()
        if controllers:
            self.lbl_status.config(
                text=f"✅ Comando: {controllers[0].name}",
                fg='#4CAF50'
            )
        else:
            self.lbl_status.config(
                text="❌ Nenhum comando ligado\nLiga um comando USB/Bluetooth",
                fg='#f44336'
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
        messagebox.showinfo("Perfil", "✅ Perfil PS4 carregado!")

    def _apply_xbox(self):
        """Aplica perfil Xbox."""
        from src.infrastructure.input.controller_detector import ControllerInfo
        info = ControllerInfo(
            guid="", name="Xbox Controller",
            vendor_id="", product_id="", is_gamecontroller=True
        )
        self.current_profile = self.mapper.create_default_profile(info)
        self._update_preview()
        messagebox.showinfo("Perfil", "✅ Perfil Xbox carregado!")

    def _apply_switch(self):
        """Aplica perfil Switch."""
        from src.infrastructure.input.controller_detector import ControllerInfo
        info = ControllerInfo(
            guid="", name="Switch Pro Controller",
            vendor_id="", product_id="", is_gamecontroller=True
        )
        self.current_profile = self.mapper.create_default_profile(info)
        self._update_preview()
        messagebox.showinfo("Perfil", "✅ Perfil Switch carregado!")

    def _apply_generic(self):
        """Aplica perfil genérico."""
        from src.infrastructure.input.controller_detector import ControllerInfo
        info = ControllerInfo(
            guid="", name="Generic Controller",
            vendor_id="", product_id="", is_gamecontroller=True
        )
        self.current_profile = self.mapper.create_default_profile(info)
        self._update_preview()
        messagebox.showinfo("Perfil", "✅ Perfil Genérico carregado!")

    def _auto_detect(self):
        """Tenta detetar automaticamente."""
        controllers = self.detector.list_controllers()
        if not controllers:
            messagebox.showerror(
                "Erro",
                "Nenhum comando detetado!\n\n"
                "Liga um comando e tenta novamente."
            )
            return
        
        self.current_profile = self.mapper.create_default_profile(controllers[0])
        self._update_preview()
        messagebox.showinfo(
            "Auto-Deteção",
            f"Perfil aplicado para:\n{controllers[0].name}"
        )

    def _save(self):
        """Guarda e aplica configuração."""
        if not self.current_profile:
            messagebox.showerror("Erro", "Nenhum perfil configurado!\nSeleciona um perfil primeiro.")
            return
        
        try:
            # 1. Guardar perfil JSON
            self.profile_manager.save_profile(self.emulator_id, self.current_profile)
            
            # 2. Aplicar no mupen64plus.cfg
            success = self.profile_manager.apply_to_mupen64plus(self.current_profile)
            
            if success:
                messagebox.showinfo(
                    "Sucesso",
                    "✅ Configuração guardada e aplicada!\n\n"
                    "A configuração foi escrita em:\n"
                    f"{self.profile_manager.mupen_cfg_path}\n\n"
                    "Podes lançar um jogo N64 agora."
                )
            else:
                messagebox.showwarning(
                    "Aviso",
                    "Perfil guardado mas houve erro ao aplicar no mupen64plus.cfg"
                )
                
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao guardar: {e}")

    def _test_controller(self):
        """Abre janela de teste para ver os índices reais dos botões."""
        import threading
        import pygame
        
        test_window = tk.Toplevel(self.frame)
        test_window.title("Testar Comando")
        test_window.geometry("400x500")
        test_window.configure(bg='#1e1e1e')
        
        tk.Label(
            test_window,
            text="Pressiona botões no comando para ver os índices",
            bg='#1e1e1e', fg='white',
            font=('Segoe UI', 11, 'bold')
        ).pack(pady=10)
        
        # Labels para mostrar estado
        lbl_info = tk.Label(
            test_window, text="Aguardando input...",
            bg='#1e1e1e', fg='#4CAF50',
            font=('Consolas', 10)
        )
        lbl_info.pack(pady=10)
        
        txt_log = tk.Text(
            test_window, bg='#252525', fg='#cccccc',
            font=('Consolas', 9), height=20, width=45
        )
        txt_log.pack(padx=10, pady=10)
        
        self._test_running = True
        
        def listen():
            try:
                pygame.init()
                pygame.joystick.init()
                
                if pygame.joystick.get_count() == 0:
                    test_window.after(0, lambda: lbl_info.config(
                        text="❌ Nenhum comando detetado", fg='#f44336'
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
                    fg='#4CAF50'
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
                    text=f"Erro: {e}", fg='#f44336'
                ))
            finally:
                pygame.quit()
        
        # Botão fechar
        def on_close():
            self._test_running = False
            test_window.destroy()
        
        tk.Button(
            test_window, text="Fechar", command=on_close,
            bg='#333333', fg='white'
        ).pack(pady=10)
        
        test_window.protocol("WM_DELETE_WINDOW", on_close)
        
        # Iniciar thread de escuta
        threading.Thread(target=listen, daemon=True).start()

    def destroy(self):
        """Esconde em vez de destruir."""
        self.frame.place_forget()