"""Testes unitários para build_launch_command."""
from pathlib import Path
from unittest.mock import patch

import pytest

from src.domain.entities.emulator import Emulator, Platform


class TestLaunchCommand:
    """Testes para construção de comandos de lançamento."""

    @pytest.fixture
    def base_emulator(self):
        return Emulator(
            id="test",
            name="Test Emulator",
            platform=Platform.UNKNOWN,
            executable_path=Path("C:/emu/test.exe"),
            supported_extensions=[".rom"],
        )

    def test_basic_command(self, base_emulator, tmp_path):
        """Comando básico deve incluir exe e ROM."""
        rom = tmp_path / "game.rom"
        rom.write_text("mock")
        
        cmd = base_emulator.build_launch_command(rom)
        assert "test.exe" in cmd
        assert "game.rom" in cmd

    def test_mupen64plus_resolution(self, tmp_path):
        """mupen64plus deve incluir argumento de resolução."""
        emu = Emulator(
            id="mupen64plus",
            name="Mupen64Plus",
            platform=Platform.NINTENDO_64,
            executable_path=Path("C:/emu/mupen.exe"),
            supported_extensions=[".z64"],
        )
        rom = tmp_path / "game.z64"
        rom.write_text("mock")
        
        with patch.object(emu, '_get_screen_resolution', return_value=(1920, 1080)):
            cmd = emu.build_launch_command(rom)
            assert "--resolution 1920x1080" in cmd

    def test_mgba_savedir(self, tmp_path):
        """mGBA deve incluir --savedir."""
        emu = Emulator(
            id="mgba",
            name="mGBA",
            platform=Platform.GAME_BOY_ADVANCE,
            executable_path=Path("C:/emu/mgba.exe"),
            supported_extensions=[".gba"],
            save_dir=tmp_path,
        )
        rom = tmp_path / "game.gba"
        rom.write_text("mock")
        
        cmd = emu.build_launch_command(rom)
        assert "--savedir" in cmd

    def test_not_installed_raises(self, tmp_path):
        """Deve lançar erro se emulador não instalado."""
        emu = Emulator(
            id="test",
            name="Test",
            platform=Platform.UNKNOWN,
            executable_path=None,
            supported_extensions=[".rom"],
        )
        rom = tmp_path / "game.rom"
        rom.write_text("mock")
        
        with pytest.raises(RuntimeError):
            emu.build_launch_command(rom)

    def test_rom_not_found_raises(self, base_emulator, tmp_path):
        """Deve lançar erro se ROM não existe."""
        rom = tmp_path / "nonexistent.rom"
        
        with pytest.raises(FileNotFoundError):
            base_emulator.build_launch_command(rom)