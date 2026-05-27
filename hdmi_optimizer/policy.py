from __future__ import annotations

from .config import ALTURA_4K, LARGURA_4K, LIMITE_RAM_PADRAO, LIMITE_VRAM_PADRAO
from .models import DiagnosticSnapshot, DisplayInfo


class OptimizationPolicy:
    def __init__(
        self,
        limite_vram=LIMITE_VRAM_PADRAO,
        limite_ram=LIMITE_RAM_PADRAO,
        largura_critica=LARGURA_4K,
        altura_critica=ALTURA_4K,
    ):
        self.limite_vram = limite_vram
        self.limite_ram = limite_ram
        self.largura_critica = largura_critica
        self.altura_critica = altura_critica

    def tem_tela_critica(self, telas: list[DisplayInfo]):
        return any(
            tela.largura >= self.largura_critica
            and tela.altura >= self.altura_critica
            for tela in telas
        )

    def deve_otimizar(self, snapshot: DiagnosticSnapshot):
        vram_percent = snapshot.gpu.vram_percent

        if vram_percent is None:
            return False

        return (
            self.tem_tela_critica(snapshot.telas)
            and vram_percent >= self.limite_vram
            and snapshot.sistema.ram_percent >= self.limite_ram
        )
