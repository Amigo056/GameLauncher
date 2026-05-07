"""Porta para catalogo/configuracao de emuladores."""

from typing import Protocol

from src.domain.entities.emulator import Emulator


class EmulatorRepository(Protocol):
    """Contrato para obter emuladores configurados."""

    def get_all(self) -> list[Emulator]:
        """Retorna todos os emuladores conhecidos."""
        ...

    def get_by_id(self, emulator_id: str) -> Emulator | None:
        """Retorna um emulador pelo id."""
        ...
