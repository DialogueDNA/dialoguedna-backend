from __future__ import annotations
import importlib
import pkgutil
from typing import Iterable, List

def discover_plugins() -> List[str]:
    return autodiscover_plugin_modules([
        "app.database.gateways.providers",
        "app.database.repos.registry",
        "app.database.repos",
        "app.storage.providers",
        "app.storage.adapters",
        "app.services.audio.enhance.providers",
        "app.services.audio.separation.providers",
        "app.services.transcription.providers",
        "app.services.summary.providers",
        "app.services.emotions.text.providers",
        "app.services.emotions.audio.providers",
        "app.services.emotions.mixed.adapters",
    ])

def autodiscover_plugin_modules(packages: Iterable[str], suffix: str = "plugin") -> List[str]:
    """
    Import every '<...>.{suffix}' module under the given packages.
    Example layout it expects:
        app/services/transcription/providers/whisperx/plugin.py
        app/services/summary/providers/azure_openai/plugin.py
    Returns the list of imported module names.
    """
    imported: List[str] = []
    for pkg_name in packages:
        pkg = importlib.import_module(pkg_name)
        if not hasattr(pkg, "__path__"):
            continue  # not a package
        for m in pkgutil.walk_packages(pkg.__path__, prefix=pkg.__name__ + "."):
            if m.ispkg:
                continue
            if m.name.rsplit(".", 1)[-1] == suffix:
                importlib.import_module(m.name)
                imported.append(m.name)
    return imported
