"""Interface de repositório: Jogos instalados localmente (ROMs)."""
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional, Set

from src.domain.entities.game import Game
from src.domain.entities.emulator import Emulator


class GameRepository(ABC):
    """
    Contrato para acesso ao filesystem de ROMs.
    Responsável por: scan, validar checksums, detectar novos arquivos.
    """
    
    @abstractmethod
    def scan_directory(self, directory: Path, extensions: List[str]) -> List[Game]:
        """
        Escaneia diretório e retorna jogos encontrados.
        Deve criar objetos Game com Rom preenchido mas sem metadados de catálogo.
        """
        pass
    
    @abstractmethod
    def find_by_path(self, rom_path: Path) -> Optional[Game]:
        """Busca jogo pelo path exato da ROM."""
        pass
    
    @abstractmethod
    def find_by_filename(self, filename: str) -> Optional[Game]:
        """Busca por nome de arquivo (fuzzy matching)."""
        pass
    
    @abstractmethod
    def get_installed_games(self, emulator: Optional[Emulator] = None) -> List[Game]:
        """
        Retorna todos os jogos instalados.
        Se emulator especificado, filtra por extensões suportadas.
        """
        pass
    
    @abstractmethod
    def delete_game(self, game: Game) -> bool:
        """Remove ROM do disco. Retorna True se sucesso."""
        pass
    
    @abstractmethod
    def validate_rom(self, game: Game) -> bool:
        """Verifica se arquivo ainda existe e checksum bate (se disponível)."""
        pass
    
    @abstractmethod
    def get_disk_usage(self) -> int:
        """Retorna bytes totais usados por ROMs."""
        pass

class DuplicateRomError(Exception):
    """Raised quando tenta adicionar ROM duplicada."""
    pass


class RomNotFoundError(Exception):
    """Raised quando arquivo ROM não existe."""
    pass