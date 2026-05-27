from __future__ import annotations

import warnings

from hdmi_optimizer.models import GPUStats


warnings.filterwarnings(
    "ignore",
    message="The pynvml package is deprecated.*",
    category=FutureWarning,
)

try:
    from pynvml import (
        NVML_TEMPERATURE_GPU,
        nvmlDeviceGetHandleByIndex,
        nvmlDeviceGetMemoryInfo,
        nvmlDeviceGetName,
        nvmlDeviceGetTemperature,
        nvmlDeviceGetUtilizationRates,
        nvmlInit,
        nvmlShutdown,
    )
except ImportError as exc:
    ERRO_IMPORT_NVML = exc
else:
    ERRO_IMPORT_NVML = None


def normalizar_nome_gpu(nome_gpu):
    if isinstance(nome_gpu, bytes):
        return nome_gpu.decode("utf-8", errors="replace")
    return str(nome_gpu)


class NvidiaGpuMonitor:
    def __init__(self, device_index=0):
        self.device_index = device_index
        self.device = None
        self.nome_gpu = "NVIDIA GPU"
        self.erro_inicializacao = None
        self.inicializado = False

    def start(self):
        if ERRO_IMPORT_NVML is not None:
            self.erro_inicializacao = (
                "Dependencia ausente: instale nvidia-ml-py para ler a GPU. "
                f"Detalhe: {ERRO_IMPORT_NVML}"
            )
            return False

        try:
            nvmlInit()
            self.device = nvmlDeviceGetHandleByIndex(self.device_index)
            self.nome_gpu = normalizar_nome_gpu(nvmlDeviceGetName(self.device))
            self.inicializado = True
            return True
        except Exception as exc:
            self.erro_inicializacao = f"Erro ao acessar Nvidia GPU: {exc}"
            self.nome_gpu = self.erro_inicializacao
            self.inicializado = False
            return False

    def read(self):
        if not self.inicializado or self.device is None:
            return GPUStats(
                nome=self.nome_gpu,
                disponivel=False,
                erro=self.erro_inicializacao or "GPU Nvidia nao inicializada.",
            )

        try:
            utilization = nvmlDeviceGetUtilizationRates(self.device)
            mem_info = nvmlDeviceGetMemoryInfo(self.device)
            vram_total = mem_info.total // (1024**2)
            vram_usada = mem_info.used // (1024**2)
            vram_percent = (vram_usada / vram_total) * 100
            temperatura = nvmlDeviceGetTemperature(self.device, NVML_TEMPERATURE_GPU)

            return GPUStats(
                nome=self.nome_gpu,
                disponivel=True,
                uso_percent=utilization.gpu,
                temperatura_c=temperatura,
                vram_usada_mb=vram_usada,
                vram_total_mb=vram_total,
                vram_percent=vram_percent,
            )
        except Exception as exc:
            return GPUStats(
                nome=self.nome_gpu,
                disponivel=False,
                erro=f"Erro ao ler sensores da GPU: {exc}",
            )

    def shutdown(self):
        if not self.inicializado or ERRO_IMPORT_NVML is not None:
            return

        try:
            nvmlShutdown()
        except Exception:
            pass
        finally:
            self.inicializado = False
