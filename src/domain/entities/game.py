"""Entidades de domínio: Game, Rom, Cover."""
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
from enum import Enum, auto


class Region(Enum):
    """Regiões de lançamento de jogos."""
    USA = auto()
    EUROPE = auto()
    JAPAN = auto()
    AUSTRALIA = auto()
    UNKNOWN = auto()
    
    @classmethod
    def from_string(cls, value: str) -> "Region":
        """Parse de string para Region."""
        mapping = {
            "USA": cls.USA, "US": cls.USA,
            "EUR": cls.EUROPE, "EU": cls.EUROPE, "EUROPE": cls.EUROPE,
            "JAP": cls.JAPAN, "JP": cls.JAPAN, "JAPAN": cls.JAPAN,
            "AU": cls.AUSTRALIA, "AUS": cls.AUSTRALIA,
        }
        return mapping.get(value.upper().strip(), cls.UNKNOWN)


@dataclass(frozen=True)
class Cover:
    """Value Object: Imagem de capa do jogo."""
    url: Optional[str] = None
    local_path: Optional[Path] = None
    width: int = 0
    height: int = 0
    
    @property
    def is_local(self) -> bool:
        """Verifica se a cover está disponível localmente."""
        return self.local_path is not None and self.local_path.exists()
    
    @property
    def is_available(self) -> bool:
        """Verifica se existe URL ou arquivo local."""
        return self.url is not None or self.is_local


@dataclass(frozen=True)
class Rom:
    """Value Object: Arquivo de ROM do jogo."""
    file_path: Path
    file_size: int = 0
    checksum_md5: Optional[str] = None
    extension: str = field(init=False)
    
    def __post_init__(self):
        # frozen=True requer object.__setattr__
        object.__setattr__(self, 'extension', self.file_path.suffix.lower())
    
    @property
    def exists(self) -> bool:
        """Verifica se o arquivo físico existe."""
        return self.file_path.exists()
    
    @property
    def name(self) -> str:
        """Nome do arquivo sem extensão."""
        return self.file_path.stem


@dataclass
class Game:
    """Entidade principal: Representa um jogo no catálogo."""
    id: str  # slug único (ex: "new-super-mario-bros")
    title: str
    region: Region = Region.UNKNOWN
    cover: Cover = field(default_factory=Cover)
    rom: Optional[Rom] = None  # None = não instalado localmente
    
    def __post_init__(self):
        """Validações pós-inicialização."""
        if not self.id or not self.id.strip():
            raise ValueError("Game.id não pode ser vazio")
        if not self.title or not self.title.strip():
            raise ValueError("Game.title não pode ser vazio")
    
    @property
    def is_available_locally(self) -> bool:
        """Jogo está instalado e pronto para jogar."""
        return self.rom is not None and self.rom.exists
    
    
    def update_local_path(self, path: Path) -> "Game":
        """Retorna nova instância com path local atualizado (imutabilidade)."""
        new_rom = Rom(file_path=path) if path else None
        return Game(
            id=self.id,
            title=self.title,
            region=self.region,
            cover=self.cover,
            rom=new_rom,
        )
    
    def mark_as_downloaded(self, rom_path: Path) -> None:
        """Atualiza estado para downloaded (mutação controlada)."""
        self.rom = Rom(file_path=rom_path)
