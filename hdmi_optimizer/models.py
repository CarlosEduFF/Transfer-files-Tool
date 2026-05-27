from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class DisplayInfo:
    tipo: str
    largura: int
    altura: int
    principal: bool = False

    @property
    def resolucao(self):
        return f"{self.largura}x{self.altura}"


@dataclass(frozen=True)
class GPUStats:
    nome: str
    disponivel: bool
    uso_percent: int | None = None
    temperatura_c: int | None = None
    vram_usada_mb: int | None = None
    vram_total_mb: int | None = None
    vram_percent: float | None = None
    erro: str | None = None


@dataclass(frozen=True)
class SystemStats:
    cpu_percent: float
    ram_percent: float


@dataclass(frozen=True)
class DiagnosticSnapshot:
    horario: datetime
    gpu: GPUStats
    sistema: SystemStats
    telas: list[DisplayInfo] = field(default_factory=list)
    erro_telas: str | None = None
    acao: str | None = None
    resultado: str | None = None
