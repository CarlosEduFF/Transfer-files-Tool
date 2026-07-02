"""Tipos de domínio que circulam entre as camadas."""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class BatteryStatus:
    """Estado instantâneo da bateria.

    plugged: True (na tomada), False (na bateria) ou None (desconhecido).
    secs_left: segundos restantes, ou None se ilimitado/desconhecido.
    """

    percent: Optional[float]
    plugged: Optional[bool]
    secs_left: Optional[int]

    @property
    def present(self) -> bool:
        """False quando nenhuma bateria foi detectada."""
        return self.percent is not None


@dataclass(frozen=True)
class HealthReport:
    """Relatório de desgaste extraído do powercfg.

    Quando ``error`` está preenchido, os demais campos não são confiáveis.
    """

    design_mwh: Optional[int] = None
    full_mwh: Optional[int] = None
    health_pct: Optional[float] = None
    cycle_count: Optional[int] = None
    error: Optional[str] = None

    @classmethod
    def failed(cls, message: str) -> "HealthReport":
        return cls(error=message)
