import psutil

from hdmi_optimizer.models import SystemStats


def obter_status_sistema():
    memoria = psutil.virtual_memory()
    return SystemStats(
        cpu_percent=psutil.cpu_percent(),
        ram_percent=memoria.percent,
    )
