from __future__ import annotations
from typing import Callable, Dict, Generic, Mapping, TypeVar

TConfig = TypeVar("TConfig")
TService = TypeVar("TService")
PluginBuilder = Callable[[TConfig], TService]


class PluginRegistry(Generic[TConfig, TService]):
    """
    Registry for named plugin builders: name -> (cfg -> service).
    Provides: register(name), get(name), create(name, cfg), names(), items(), alias().
    """
    def __init__(self) -> None:
        self._plugins: Dict[str, PluginBuilder[TConfig, TService]] = {}

    def register(self, name: str) -> Callable[[PluginBuilder[TConfig, TService]], PluginBuilder[TConfig, TService]]:
        """Decorator: @registry.register('name')"""
        key = name.strip().lower()
        def deco(fn: PluginBuilder[TConfig, TService]) -> PluginBuilder[TConfig, TService]:
            if key in self._plugins:
                raise ValueError(f"Plugin '{key}' already registered")
            self._plugins[key] = fn
            return fn
        return deco

    def alias(self, new_name: str, target_name: str) -> None:
        """Create alias new_name -> target_name."""
        t = target_name.strip().lower()
        n = new_name.strip().lower()
        if t not in self._plugins:
            raise KeyError(f"Target plugin '{t}' not found")
        if n in self._plugins:
            raise ValueError(f"Plugin '{n}' already registered")
        self._plugins[n] = self._plugins[t]

    def get(self, name: str) -> PluginBuilder[TConfig, TService]:
        key = name.strip().lower()
        fn = self._plugins.get(key)
        if fn is None:
            raise KeyError(f"Unknown plugin '{key}'. Available: {', '.join(self._plugins)}")
        return fn

    def create(self, name: str, cfg: TConfig) -> TService:
        """Build service instance by name."""
        return self.get(name)(cfg)

    def names(self) -> list[str]:
        return sorted(self._plugins.keys())

    def items(self) -> Mapping[str, PluginBuilder[TConfig, TService]]:
        # shallow, read-only-ish view
        return dict(self._plugins)
