"""Adaptadores e presets de configuracao grafica."""

from src.infrastructure.adapters.graphics.local_config_writer import LocalGraphicsConfigWriter
from src.infrastructure.adapters.graphics.noop_config_writer import NoopGraphicsConfigWriter
from src.infrastructure.adapters.graphics.profile_registry import GraphicsProfileRegistry

__all__ = [
    "GraphicsProfileRegistry",
    "LocalGraphicsConfigWriter",
    "NoopGraphicsConfigWriter",
]
