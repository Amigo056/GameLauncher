"""Adaptadores de covers por plataforma."""

from src.infrastructure.adapters.covers.fallback_extractor import FallbackCoverExtractor
from src.infrastructure.adapters.covers.gba_extractor import GBAScreenshotExtractor
from src.infrastructure.adapters.covers.nds_extractor import NDSCoverExtractor
from src.infrastructure.adapters.covers.psp_extractor import PSPCoverExtractor

__all__ = [
    "FallbackCoverExtractor",
    "GBAScreenshotExtractor",
    "NDSCoverExtractor",
    "PSPCoverExtractor",
]
