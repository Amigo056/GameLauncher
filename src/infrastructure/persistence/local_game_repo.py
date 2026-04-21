"""Implementação concreta: Repositório de jogos locais (filesystem)."""
import os
import hashlib
import fnmatch
from pathlib import Path
from typing import List, Optional, Set, Dict
from datetime import datetime

from src.domain.entities.game import Game, Rom, Region
from src.domain.entities.emulator import Emulator
from src.domain.repositories.game_repository import GameRepository, RomNotFoundError


class LocalGameRepository(GameRepository):
    """
    Implementação do GameRepository usando filesystem local.
    Responsável por: scan, validação de arquivos, fuzzy matching de nomes.
    """
    
    def __init__(self, base_path: Path, calculate_checksums: bool = False):
        """
        Args:
            base_path: Pasta raiz de ROMs (ex: ./roms)
            calculate_checksums: Se True, calcula MD5 dos arquivos (lento para arquivos grandes)
        """
        self.base_path = Path(base_path)
        self.calculate_checksums = calculate_checksums
        self._cache: Dict[Path, Rom] = {}  # Cache de ROMs escaneadas
        self._last_scan: Optional[datetime] = None
    
    def scan_directory(self, directory: Path, extensions: List[str]) -> List[Game]:
        """
        Escaneia diretório por arquivos de ROM.
        Retorna objetos Game com apenas os dados do filesystem (sem metadados de catálogo).
        """
        if not directory.exists():
            return []
        
        games = []
        extensions_lower = [ext.lower() if ext.startswith('.') else f'.{ext.lower()}' 
                          for ext in extensions]
        
        # Escanear recursivamente
        for ext in extensions_lower:
            pattern = f"*{ext}"
            for file_path in directory.rglob(pattern):
                if file_path.is_file():
                    try:
                        stat = file_path.stat()
                        rom = Rom(
                            file_path=file_path,
                            file_size=stat.st_size,
                            checksum_md5=self._calculate_md5(file_path) if self.calculate_checksums else None
                        )
                        
                        # Criar Game básico (ID temporário baseado no nome do arquivo)
                        game_id = self._filename_to_id(file_path.stem)
                        
                        game = Game(
                            id=game_id,
                            title=file_path.stem,  # Nome do arquivo como título temporário
                            rom=rom,
                            region=self._detect_region_from_filename(file_path.name)
                        )
                        
                        games.append(game)
                        self._cache[file_path] = rom
                        
                    except (OSError, PermissionError) as e:
                        print(f"Erro lendo {file_path}: {e}")
                        continue
        
        self._last_scan = datetime.now()
        return games
    
    def find_by_path(self, rom_path: Path) -> Optional[Game]:
        """Busca jogo pelo path exato."""
        if not rom_path.exists():
            return None
        
        for game in self.get_installed_games():
            if game.rom and game.rom.file_path == rom_path:
                return game
        return None
    
    def find_by_filename(self, filename: str) -> Optional[Game]:
        """Busca por nome de arquivo com fuzzy matching."""
        candidates = self.get_installed_games()
        filename_clean = self._normalize_filename(filename)
        
        best_match = None
        best_score = 0.0
        
        for game in candidates:
            if not game.rom:
                continue
            
            file_stem = game.rom.file_path.stem
            score = self._similarity(filename_clean, self._normalize_filename(file_stem))
            
            if score > 0.85 and score > best_score:  # Threshold alto para filenames
                best_score = score
                best_match = game
        
        return best_match
    
    def get_installed_games(self, emulator: Optional[Emulator] = None) -> List[Game]:
        """
        Retorna todos os jogos instalados.
        Se emulator especificado, filtra por extensões e pasta específica.
        """
        if emulator:
            directory = emulator.roms_directory
            extensions = emulator.supported_extensions
        else:
            directory = self.base_path
            extensions = ['.nds', '.zip', '.iso', '.cso', '.pbp', '.gb', '.gbc', '.gba']
        
        # Usar cache se scan recente (< 5 min) e mesmo diretório
        if self._last_scan and (datetime.now() - self._last_scan).seconds < 300:
            # Filtrar cache pelo diretório solicitado
            cached = []
            for path, rom in self._cache.items():
                if path.is_relative_to(directory):
                    game = Game(
                        id=self._filename_to_id(path.stem),
                        title=path.stem,
                        rom=rom,
                    )
                    cached.append(game)
            
            if cached:
                return cached
        
        return self.scan_directory(directory, extensions)
    
    def delete_game(self, game: Game) -> bool:
        """Remove ROM do disco."""
        if not game.rom or not game.rom.exists:
            raise RomNotFoundError(f"ROM não encontrada: {game.rom}")
        
        try:
            game.rom.file_path.unlink()
            # Remover da cache
            if game.rom.file_path in self._cache:
                del self._cache[game.rom.file_path]
            return True
        except Exception as e:
            print(f"Erro deletando {game.rom.file_path}: {e}")
            return False
    
    def validate_rom(self, game: Game) -> bool:
        """Verifica se arquivo existe e checksum bate (se disponível)."""
        if not game.rom:
            return False
        
        if not game.rom.file_path.exists():
            return False
        
        # Se temos checksum esperado, validar
        if self.calculate_checksums and game.rom.checksum_md5:
            current_md5 = self._calculate_md5(game.rom.file_path)
            return current_md5 == game.rom.checksum_md5
        
        return True
    
    def get_disk_usage(self) -> int:
        """Retorna bytes totais usados por ROMs."""
        total = 0
        for game in self.get_installed_games():
            if game.rom and game.rom.exists:
                total += game.rom.file_size
        return total
    
    # === Métodos auxiliares privados ===
    
    def _calculate_md5(self, file_path: Path, chunk_size: int = 8192) -> str:
        """Calcula MD5 de arquivo grande sem carregar tudo em memória."""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(chunk_size), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def _filename_to_id(self, filename: str) -> str:
        """Converte nome de arquivo para ID (slug)."""
        # Remover extensão e normalizar
        clean = self._sanitize_filename(filename)
        return clean.lower().replace(' ', '-').replace('_', '-')[:50]
    
    def _sanitize_filename(self, name: str) -> str:
        """Remove caracteres inválidos de nome de arquivo."""
        invalid = '<>:"/\\|?*'
        for char in invalid:
            name = name.replace(char, '')
        return name.strip()
    
    def _normalize_filename(self, filename: str) -> str:
        """Normaliza para comparação fuzzy."""
        # Remover parênteses e conteúdo: (USA), (Rev 1), etc.
        import re
        normalized = re.sub(r'\s*\([^)]*\)', '', filename)
        # Remover pontuação
        normalized = re.sub(r'[^\w\s]', '', normalized)
        # Normalizar espaços
        normalized = ' '.join(normalized.split())
        return normalized.lower()
    
    def _similarity(self, a: str, b: str) -> float:
        """Calcula similaridade entre strings (0.0 a 1.0)."""
        if a == b:
            return 1.0
        
        # Usar difflib.SequenceMatcher se disponível, senão implementação simples
        try:
            from difflib import SequenceMatcher
            return SequenceMatcher(None, a, b).ratio()
        except ImportError:
            # Fallback simples: palavras em comum
            words_a = set(a.split())
            words_b = set(b.split())
            if not words_a or not words_b:
                return 0.0
            intersection = words_a & words_b
            return len(intersection) / max(len(words_a), len(words_b))
    
    def _detect_region_from_filename(self, filename: str) -> Region:
        """Detecta região baseado em padrões no nome do arquivo."""
        upper = filename.upper()
        if '(USA)' in upper or '(U)' in upper or ' USA ' in upper:
            return Region.USA
        elif '(EUR)' in upper or '(E)' in upper or ' EUROPE ' in upper:
            return Region.EUROPE
        elif '(JAP)' in upper or '(J)' in upper or ' JAPAN ' in upper:
            return Region.JAPAN
        return Region.UNKNOWN
    
    def clear_cache(self):
        """Limpa cache de ROMs escaneadas."""
        self._cache.clear()
        self._last_scan = None