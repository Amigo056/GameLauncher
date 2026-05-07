"""Exceções de domínio — hierarquia enterprise para tratamento estruturado de erros."""


class GameLauncherError(Exception):
    """Base para todas as exceções da aplicação."""
    pass


# ─── Emulador ─────────────────────────────────

class EmulatorError(GameLauncherError):
    """Erro relacionado com emuladores."""
    pass


class EmulatorNotInstalledError(EmulatorError):
    """Emulador não encontrado no sistema."""
    pass


class EmulatorNotFoundError(EmulatorError):
    """Configuração de emulador não existe no JSON."""
    pass


class InvalidLaunchCommandError(EmulatorError):
    """Comando de lançamento malformado."""
    pass


# ─── ROM / Jogo ───────────────────────────────

class RomError(GameLauncherError):
    """Erro relacionado com ROMs."""
    pass


class RomNotFoundError(RomError):
    """Arquivo ROM não existe no disco."""
    pass


class DuplicateRomError(RomError):
    """Tentativa de adicionar ROM duplicada."""
    pass


class InvalidRomFormatError(RomError):
    """Formato de ROM inválido ou corrompido."""
    pass


class RomReadError(RomError):
    """Erro de leitura do arquivo ROM."""
    pass


# ─── Cover ────────────────────────────────────

class CoverError(GameLauncherError):
    """Erro relacionado com extração de covers."""
    pass


class CoverExtractionError(CoverError):
    """Falha ao extrair cover de uma ROM."""
    pass


class CoverNotFoundError(CoverError):
    """Cover não encontrada para o jogo."""
    pass


# ─── Configuração ─────────────────────────────

class ConfigError(GameLauncherError):
    """Erro relacionado com configurações."""
    pass


class ConfigNotFoundError(ConfigError):
    """Ficheiro de configuração não encontrado."""
    pass


class ConfigValidationError(ConfigError):
    """Configuração inválida ou incompleta."""
    pass


# ─── Sistema / Processo ───────────────────────

class SystemError(GameLauncherError):
    """Erro de sistema operativo."""
    pass


class ProcessLaunchError(SystemError):
    """Falha ao lançar processo do emulador."""
    pass


class ProcessNotFoundError(SystemError):
    """Processo não encontrado (PID inválido)."""
    pass


# ─── Input / Controlos ────────────────────────

class InputError(GameLauncherError):
    """Erro relacionado com controlos."""
    pass


class ControllerNotFoundError(InputError):
    """Nenhum comando detetado."""
    pass


class ProfileError(InputError):
    """Erro no perfil de controlos."""
    pass