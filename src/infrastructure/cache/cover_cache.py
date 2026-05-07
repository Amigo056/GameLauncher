"""Cache persistente de covers com TTL."""
import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from threading import RLock
from typing import Optional, Dict, Any

from src.domain.entities.game import Cover


@dataclass
class CacheEntry:
    """Entrada individual no cache."""
    game_id: str
    emulator_id: str
    cover_path: str
    rom_checksum: str
    created_at: str
    ttl_seconds: int


class CoverCache:
    """
    Cache persistente de covers em JSON.
    
    Invalida entradas quando:
    - ROM muda (checksum diferente)
    - TTL expira
    - Cover file é eliminado
    """

    CACHE_FILE = Path("data/cover_cache.json")
    DEFAULT_TTL_DAYS = 30

    def __init__(self, cache_file: Optional[Path] = None):
        self.cache_file = Path(cache_file) if cache_file else self.CACHE_FILE
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)
        self._data: Dict[str, Any] = {}
        self._lock = RLock()
        self._load()

    def _load(self):
        """Carrega cache do disco."""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    self._data = json.load(f)
            except (json.JSONDecodeError, OSError):
                self._data = {}
        else:
            self._data = {}

    def _save(self):
        """Persiste cache no disco."""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self._data, f, indent=2)
        except OSError:
            pass

    def _make_key(self, game_id: str, emulator_id: str) -> str:
        """Gera chave única para cache."""
        return f"{emulator_id}:{game_id}"

    def get(self, game_id: str, emulator_id: str, rom_checksum: str) -> Optional[Cover]:
        """
        Retorna cover do cache se válida.
        
        Args:
            game_id: ID do jogo
            emulator_id: ID do emulador
            rom_checksum: Checksum atual da ROM (para invalidação)
            
        Returns:
            Cover se válida, None caso contrário
        """
        with self._lock:
            key = self._make_key(game_id, emulator_id)
            entry = self._data.get(key)

            if not entry:
                return None

            # Verificar TTL
            created = datetime.fromisoformat(entry['created_at'])
            ttl = timedelta(seconds=entry.get('ttl_seconds', self.DEFAULT_TTL_DAYS * 86400))
            if datetime.now() - created > ttl:
                del self._data[key]
                self._save()
                return None

            # Verificar se ROM mudou
            if entry.get('rom_checksum') != rom_checksum:
                del self._data[key]
                self._save()
                return None

            # Verificar se ficheiro existe
            cover_path = Path(entry['cover_path'])
            if not cover_path.exists():
                del self._data[key]
                self._save()
                return None

            return Cover(local_path=cover_path)

    def put(
        self,
        game_id: str,
        emulator_id: str,
        cover: Cover,
        rom_checksum: str,
        ttl_days: Optional[int] = None,
    ):
        """
        Armazena cover no cache.
        
        Args:
            game_id: ID do jogo
            emulator_id: ID do emulador
            cover: Cover a cachear
            rom_checksum: Checksum da ROM para invalidação futura
            ttl_days: Dias até expirar (default: 30)
        """
        if not cover.local_path:
            return
        
        with self._lock:
            key = self._make_key(game_id, emulator_id)
            self._data[key] = {
                'game_id': game_id,
                'emulator_id': emulator_id,
                'cover_path': str(cover.local_path),
                'rom_checksum': rom_checksum,
                'created_at': datetime.now().isoformat(),
                'ttl_seconds': (ttl_days or self.DEFAULT_TTL_DAYS) * 86400,
            }
            self._save()

    def invalidate(self, game_id: str, emulator_id: str):
        """Remove entrada específica do cache."""
        with self._lock:
            key = self._make_key(game_id, emulator_id)
            if key in self._data:
                del self._data[key]
                self._save()

    def invalidate_all(self, emulator_id: Optional[str] = None):
        """
        Invalida todo o cache ou só de um emulador.
        
        Args:
            emulator_id: Se especificado, só invalida desse emulador
        """
        with self._lock:
            if emulator_id:
                keys_to_remove = [
                    k for k in self._data.keys()
                    if k.startswith(f"{emulator_id}:")
                ]
                for key in keys_to_remove:
                    del self._data[key]
            else:
                self._data.clear()
            self._save()

    def cleanup(self) -> int:
        """
        Remove entradas expiradas e órfãs.
        
        Returns:
            Número de entradas removidas
        """
        with self._lock:
            removed = 0
            now = datetime.now()

            keys = list(self._data.keys())
            for key in keys:
                entry = self._data[key]

                # TTL expirado
                created = datetime.fromisoformat(entry['created_at'])
                ttl = timedelta(seconds=entry.get('ttl_seconds', self.DEFAULT_TTL_DAYS * 86400))
                if now - created > ttl:
                    del self._data[key]
                    removed += 1
                    continue

                # Ficheiro não existe
                if not Path(entry['cover_path']).exists():
                    del self._data[key]
                    removed += 1

            if removed > 0:
                self._save()

            return removed
