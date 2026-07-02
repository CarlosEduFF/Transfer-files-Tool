"""Contratos das fontes de dados de bateria."""

from abc import ABC, abstractmethod

from ..domain.models import BatteryStatus, HealthReport


class RealtimeCollector(ABC):
    """Fonte de leitura instantânea (carga, tomada, tempo restante)."""

    @abstractmethod
    def read(self) -> BatteryStatus:
        ...


class HealthCollector(ABC):
    """Fonte de relatório de desgaste (capacidade de fábrica vs. atual).

    Pode ser lenta (depende do SO); chame fora da thread da UI.
    """

    @abstractmethod
    def read(self) -> HealthReport:
        ...
