import os
import glob
from pathlib import Path
from typing import List, Dict
from PIL import Image

class GameLibrary:
    def __init__(self, roms_folder: str, extensions: List[str]):
        self.roms_folder = Path(roms_folder)
        self.extensions = extensions
        self.covers_cache = {}
    
    def scan_games(self) -> List[Dict]:
        """Escaneia pasta de ROMs e retorna lista de jogos."""
        games = []
        
        if not self.roms_folder.exists():
            return games
        
        for ext in self.extensions:
            pattern = str(self.roms_folder / f"*{ext}")
            for file_path in glob.glob(pattern):
                file_path = Path(file_path)
                game_info = {
                    'name': file_path.stem,  # Nome sem extensão
                    'path': str(file_path),
                    'extension': ext,
                    'cover': self._find_cover(file_path)
                }
                games.append(game_info)
        
        # Ordenar por nome
        games.sort(key=lambda x: x['name'].lower())
        return games
    
    def _find_cover(self, rom_path: Path) -> str:
        """Procura cover art na pasta do jogo ou usa default."""
        # Procurar ficheiros com mesmo nome mas extensão de imagem
        for ext in ['.png', '.jpg', '.jpeg']:
            cover_path = rom_path.with_suffix(ext)
            if cover_path.exists():
                return str(cover_path)
        
        # Procurar em assets/covers/
        covers_dir = Path("assets/covers")
        if covers_dir.exists():
            for ext in ['.png', '.jpg']:
                cover_file = covers_dir / f"{rom_path.stem}{ext}"
                if cover_file.exists():
                    return str(cover_file)
        
        # Retornar default
        return "assets/default_cover.png"
    
    def get_thumbnail(self, cover_path: str, size: tuple = (150, 150)) -> Image.Image:
        """Retorna thumbnail da cover (para Tkinter)."""
        try:
            if cover_path in self.covers_cache:
                return self.covers_cache[cover_path]
            
            img = Image.open(cover_path)
            img.thumbnail(size, Image.Resampling.LANCZOS)
            self.covers_cache[cover_path] = img
            return img
        except:
            # Retornar imagem vazia ou default
            return Image.new('RGB', size, color='gray')