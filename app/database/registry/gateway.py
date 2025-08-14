from __future__ import annotations
from typing import Callable, Dict

from app.ports.db.table_gateway import TableGateway

TableGatewayFactory = Callable[[str], TableGateway]

class GatewayRegistry:
    def __init__(self) -> None:
        self._map: Dict[str, TableGatewayFactory] = {}

    def register(self, backend: str, factory: TableGatewayFactory) -> None:
        self._map[backend] = factory

    def for_backend(self, backend: str) -> TableGatewayFactory:
        try:
            return self._map[backend]
        except KeyError:
            raise ValueError(f"Unknown backend: {backend}") from None
