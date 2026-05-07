"""Testes unitários para PSPCoverExtractor."""
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from src.infrastructure.covers.psp_extractor import PSPCoverExtractor

class TestPSPCoverExtractor:
    """Testes para extração de covers PSP."""

    @pytest.fixture
    def extractor(self):
        return PSPCoverExtractor()

    def test_can_extract_rejects_non_iso(self, extractor):
        """Deve rejeitar ficheiros que não são ISO/CSO."""
        path = Path("game.nds")
        assert extractor.can_extract(path) is False

    @patch('builtins.open')
    def test_can_extract_valid_iso(self, mock_open, extractor):
        """Deve aceitar ISO com magic PSP_GAME."""
        mock_file = MagicMock()
        mock_file.read.return_value = b'PSP_GAME'
        mock_open.return_value.__enter__.return_value = mock_file
        
        path = Path("game.iso")
        assert extractor.can_extract(path) is True

    @patch('builtins.open')
    def test_can_extract_invalid_iso(self, mock_open, extractor):
        """Deve rejeitar ISO sem magic PSP_GAME."""
        mock_file = MagicMock()
        mock_file.read.return_value = b'NOT_A_PSP'
        mock_open.return_value.__enter__.return_value = mock_file
        
        path = Path("game.iso")
        assert extractor.can_extract(path) is False

    def test_parse_sfo_title_valid(self, extractor):
        """Deve extrair título de PARAM.SFO válido."""
        # SFO mínimo válido
        data = b'\\x00PSF'  # magic
        data += b'\\x00' * 4  # version
        data += struct.pack('<I', 32)   # key_table_start
        data += struct.pack('<I', 64)   # data_table_start
        data += struct.pack('<I', 1)    # index_entries
        
        # Entry
        data += struct.pack('<H', 0)    # key_offset
        data += b'\\x00' * 10           # padding
        data += struct.pack('<I', 0)    # val_offset
        
        # Key table
        data += b'TITLE\\x00'
        data += b'\\x00' * 10
        
        # Data table
        data += b'My Game Title\\x00'
        
        title = extractor._parse_sfo_title(data)
        assert title == "My Game Title"

    def test_supported_extensions(self, extractor):
        """Deve suportar .iso e .cso."""
        assert ".iso" in extractor.supported_extensions
        assert ".cso" in extractor.supported_extensions


import struct  # noqa: E402