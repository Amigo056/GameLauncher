"""Testes unitários para NDSCoverExtractor."""
import struct
from pathlib import Path
from unittest.mock import mock_open, patch

import pytest

from src.infrastructure.adapters.covers.nds_extractor import NDSCoverExtractor

class TestNDSCoverExtractor:
    """Testes para extração de covers NDS."""

    @pytest.fixture
    def extractor(self):
        return NDSCoverExtractor()

    def test_can_extract_rejects_non_nds(self, extractor):
        """Deve rejeitar ficheiros que não são .nds."""
        path = Path("game.gba")
        assert extractor.can_extract(path) is False

    def test_can_extract_rejects_too_small(self, extractor):
        """Deve rejeitar ficheiros menores que header NDS."""
        with patch('builtins.open', mock_open(read_data=b'\\x00' * 100)):
            path = Path("game.nds")
            assert extractor.can_extract(path) is False

    def test_can_extract_valid_nds(self, extractor):
        """Deve aceitar ROM NDS válida com banner pointer."""
        # Header mínimo: banner_offset em 0x068 = 0x200
        data = bytearray(0x1000)
        data[0x068:0x06C] = struct.pack('<I', 0x200)  # banner_offset
        
        with patch('builtins.open', mock_open(read_data=bytes(data))) as mock_file:
            mock_file.return_value.seek = lambda pos, whence=0: len(data) if whence == 2 else pos
            path = Path("game.nds")
            assert extractor.can_extract(path) is True

    def test_can_extract_zero_banner_offset(self, extractor):
        """Deve rejeitar ROM com banner_offset = 0."""
        data = bytearray(0x1000)
        data[0x068:0x06C] = struct.pack('<I', 0)  # banner_offset = 0
        
        with patch('builtins.open', mock_open(read_data=bytes(data))) as mock_file:
            mock_file.return_value.seek = lambda pos, whence=0: len(data) if whence == 2 else pos
            path = Path("game.nds")
            assert extractor.can_extract(path) is False

    def test_decode_palette_index_zero_transparent(self, extractor):
        """Índice 0 da paleta deve ser sempre transparente."""
        # Paleta com cor não-zero no índice 0
        palette_data = struct.pack('<H', 0x7FFF) + b'\x00' * 30  # índice 0 = branco puro
        palette = extractor._decode_palette(palette_data)
        
        assert palette[0] == (0, 0, 0, 0)  # transparente
        assert len(palette) == 16  # 16 cores

    def test_decode_palette_bgr555(self, extractor):
        """Deve decodificar cor BGR555 corretamente."""
        # Índice 1: vermelho puro = 0x001F (BGR555: R=31, G=0, B=0)
        palette_data = b'\x00\x00' + struct.pack('<H', 0x001F) + b'\x00' * 28
        palette = extractor._decode_palette(palette_data)
        
        assert palette[1] == (248, 0, 0, 255)  # R=31<<3=248

    def test_supported_extensions(self, extractor):
        """Deve suportar apenas .nds."""
        assert extractor.supported_extensions == [".nds"]
