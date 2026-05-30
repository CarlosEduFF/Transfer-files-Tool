"""Registry de operações.

Operações se auto-registram via o decorador @register. A CLI e o menu
descobrem as operações disponíveis chamando `all()` / `get(name)`.
"""

from __future__ import annotations

from .base import Operation

_REGISTRY: dict[str, Operation] = {}


def register(cls: type[Operation]) -> type[Operation]:
    """Decorador de classe: instancia a operação e a adiciona ao registry."""
    instance = cls()
    if not instance.name:
        raise ValueError(f"Operação {cls.__name__} não definiu 'name'.")
    if instance.name in _REGISTRY:
        raise ValueError(f"Operação duplicada: '{instance.name}'")
    _REGISTRY[instance.name] = instance
    return cls


def get(name: str) -> Operation:
    if name not in _REGISTRY:
        raise KeyError(f"Operação desconhecida: '{name}'")
    return _REGISTRY[name]


def all() -> list[Operation]:
    """Operações registradas, na ordem de registro."""
    return list(_REGISTRY.values())
