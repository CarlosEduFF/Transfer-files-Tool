"""Leitura em tempo real via psutil."""

from .base import RealtimeCollector
from ..domain.models import BatteryStatus

try:
    import psutil
except ImportError:
    raise SystemExit("psutil não encontrado. Instale com:  pip install psutil")


class PsutilRealtimeCollector(RealtimeCollector):
    """Lê o estado instantâneo da bateria com ``psutil.sensors_battery``."""

    def read(self) -> BatteryStatus:
        batt = psutil.sensors_battery()
        if batt is None:
            return BatteryStatus(percent=None, plugged=None, secs_left=None)

        secs = batt.secsleft
        if secs in (psutil.POWER_TIME_UNLIMITED, psutil.POWER_TIME_UNKNOWN):
            secs = None
        return BatteryStatus(
            percent=batt.percent,
            plugged=batt.power_plugged,
            secs_left=secs,
        )
