"""Caso de uso: Lançar emulador com jogo."""
import time
from dataclasses import dataclass
from typing import Optional, Protocol

from src.domain.entities.game import Game
from src.domain.entities.emulator import Emulator
from src.application.events import event_bus, GameLaunched, GameClosed


class ProcessManager(Protocol):
    """
    Protocolo para gerenciamento de processos.
    Implementação: infrastructure/system/process_manager.py
    """
    def launch(self, command: str) -> int:
        """Lança processo e retorna PID."""
        ...
    
    def is_running(self, pid: int) -> bool:
        """Verifica se processo ainda executa."""
        ...
    
    def wait_for_close(self, pid: int, timeout: Optional[float] = None) -> bool:
        """Aguarda fechamento do processo."""
        ...


@dataclass
class LaunchResult:
    """Resultado do lançamento."""
    success: bool
    pid: Optional[int] = None
    error_message: Optional[str] = None
    session_duration: float = 0.0


class LaunchEmulatorUseCase:
    """
    Orquestra o lançamento de um jogo:
    1. Valida que jogo existe localmente
    2. Valida que emulador está instalado
    3. Constrói comando
    4. Lança processo
    5. (Opcional) Monitora fechamento
    """
    
    def __init__(self, process_manager: ProcessManager):
        self.process_manager = process_manager
    
    def execute(
        self,
        game: Game,
        emulator: Emulator,
        wait_for_close: bool = True
    ) -> LaunchResult:
        """
        Lança emulador com o jogo especificado.
        
        Args:
            game: Jogo a ser lançado (deve ter rom local)
            emulator: Configuração do emulador
            wait_for_close: Se True, bloqueia até fechar (para tracking)
        """
        # Validações
        if not game.is_available_locally:
            return LaunchResult(
                success=False,
                error_message="Jogo não está instalado localmente"
            )
        
        if not emulator.is_installed:
            return LaunchResult(
                success=False,
                error_message=f"Emulador {emulator.name} não encontrado"
            )
        
        if not game.rom:
            return LaunchResult(
                success=False,
                error_message="Path da ROM não disponível"
            )
        
        # Construir comando
        try:
            command = emulator.build_launch_command(game.rom.file_path)
        except Exception as e:
            return LaunchResult(
                success=False,
                error_message=f"Erro construindo comando: {e}"
            )
        
        # Lançar
        try:
            pid = self.process_manager.launch(command)
            start_time = time.time()
            
            event_bus.emit(GameLaunched(
                game_id=game.id,
                emulator_id=emulator.id,
                rom_path=game.rom.file_path,
                process_id=pid
            ))
            
            # Se não precisa esperar, retorna imediatamente
            if not wait_for_close:
                return LaunchResult(success=True, pid=pid)
            
            # Monitorar fechamento (bloqueante)
            self.process_manager.wait_for_close(pid)
            duration = time.time() - start_time
            
            event_bus.emit(GameClosed(
                game_id=game.id,
                emulator_id=emulator.id,
                session_duration=duration
            ))
            
            return LaunchResult(
                success=True,
                pid=pid,
                session_duration=duration
            )
            
        except Exception as e:
            return LaunchResult(
                success=False,
                error_message=f"Falha ao lançar: {e}"
            )
    
    def launch_async(
        self,
        game: Game,
        emulator: Emulator,
        on_close: Optional[callable] = None
    ) -> LaunchResult:
        """
        Lança sem bloquear. Chama callback quando fechar (se fornecido).
        Útil para UI que não pode travar.
        """
        result = self.execute(game, emulator, wait_for_close=False)
        
        if result.success and on_close:
            # Inicia thread de monitoramento não-bloqueante
            import threading
            def monitor():
                self.process_manager.wait_for_close(result.pid)
                event_bus.emit(GameClosed(
                    game_id=game.id,
                    emulator_id=emulator.id,
                    session_duration=0  # Calcular corretamente
                ))
                on_close(game.id)
            
            threading.Thread(target=monitor, daemon=True).start()
        
        return result