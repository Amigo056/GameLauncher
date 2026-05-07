"""Porta de repositorio para jogos/ROMs instalados localmente."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional

from src.domain.entities.emulator import Emulator
from src.domain.entities.game import Game


class GameRepository(ABC):
    """Contrato para acesso a ROMs locais."""

    @abstractmethod
    def scan_directory(self, directory: Path, extensions: List[str]) -> List[Game]:
        """Escaneia diretorio e retorna jogos encontrados."""
        pass

    @abstractmethod
    def get_installed_games(self, emulator: Optional[Emulator] = None) -> List[Game]:
        """Retorna jogos instalados, opcionalmente filtrados por emulador."""
        pass

    @abstractmethod
    def delete_game(self, game: Game) -> bool:
        """Remove ROM do disco."""
        pass

    @abstractmethod
    def validate_rom(self, game: Game) -> bool:
        """Valida se a ROM ainda existe e bate com checksum quando disponivel."""
        pass

    @abstractmethod
    def get_disk_usage(self) -> int:
        """Retorna bytes totais usados por ROMs."""
        pass


class DuplicateRomError(Exception):
    """Erro quando uma ROM duplicada e adicionada."""


class RomNotFoundError(Exception):
    """Erro quando a ROM nao existe no disco."""
