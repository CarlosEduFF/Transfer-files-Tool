from __future__ import annotations

import os
import time
from dataclasses import replace
from datetime import datetime

from hdmi_optimizer.config import (
    INTERVALO_PADRAO,
    LIMITE_RAM_PADRAO,
    LIMITE_VRAM_PADRAO,
    LOG_PADRAO,
)
from hdmi_optimizer.models import DiagnosticSnapshot
from hdmi_optimizer.monitoring.displays import obter_telas
from hdmi_optimizer.monitoring.gpu import NvidiaGpuMonitor
from hdmi_optimizer.monitoring.logger import DiagnosticLogWriter, formatar_snapshot
from hdmi_optimizer.monitoring.system import obter_status_sistema
from hdmi_optimizer.optimization.service import OptimizationService
from hdmi_optimizer.policy import OptimizationPolicy


def limpar_tela():
    os.system("cls" if os.name == "nt" else "clear")


class MonitoringService:
    def __init__(
        self,
        log_file=LOG_PADRAO,
        intervalo=INTERVALO_PADRAO,
        auto_otimizar=False,
        limite_vram=LIMITE_VRAM_PADRAO,
        limite_ram=LIMITE_RAM_PADRAO,
        gpu_monitor=None,
        optimizer=None,
    ):
        self.log_file = log_file
        self.intervalo = intervalo
        self.auto_otimizar = auto_otimizar
        self.policy = OptimizationPolicy(limite_vram=limite_vram, limite_ram=limite_ram)
        self.gpu_monitor = gpu_monitor or NvidiaGpuMonitor()
        self.optimizer = optimizer or OptimizationService()
        self.otimizacao_executada = False

    def run(self):
        self.gpu_monitor.start()
        self._mostrar_inicio()
        time.sleep(3)

        try:
            with DiagnosticLogWriter(self.log_file) as writer:
                writer.escrever_cabecalho(self.gpu_monitor.nome_gpu)

                while True:
                    limpar_tela()
                    snapshot = self._coletar_snapshot()
                    snapshot = self._otimizar_se_necessario(snapshot)

                    print("\n".join(formatar_snapshot(snapshot)))
                    writer.escrever_snapshot(snapshot)

                    time.sleep(self.intervalo)
        finally:
            self.gpu_monitor.shutdown()

    def _mostrar_inicio(self):
        print("=== MONITOR DE DIAGNOSTICO NVIDIA ATIVADO ===")
        print(f"Detectado: {self.gpu_monitor.nome_gpu}")
        print(f"Logs salvando em: {os.path.abspath(self.log_file)}")

        if self.auto_otimizar:
            print(
                "Auto-otimizacao ativa: o monitor chamara a camada de otimizacao "
                "se detectar 4K + VRAM/RAM criticas."
            )

        print("\nAbra o jogo na TV e jogue ate comecar a travar...")
        print("Pressione CTRL+C para encerrar.\n")

    def _coletar_snapshot(self):
        telas, erro_telas = obter_telas()
        return DiagnosticSnapshot(
            horario=datetime.now(),
            gpu=self.gpu_monitor.read(),
            sistema=obter_status_sistema(),
            telas=telas,
            erro_telas=erro_telas,
        )

    def _otimizar_se_necessario(self, snapshot):
        if (
            not self.auto_otimizar
            or self.otimizacao_executada
            or not self.policy.deve_otimizar(snapshot)
        ):
            return snapshot

        snapshot = replace(
            snapshot,
            acao=(
                "[ACAO] Gargalo detectado: 4K + VRAM/RAM em nivel critico. "
                "Executando otimizacao de resolucao..."
            ),
        )

        sucesso = self.optimizer.optimize_for_game()
        self.otimizacao_executada = True

        return replace(
            snapshot,
            resultado=(
                "[RESULTADO] Otimizacao automatica "
                f"{'concluida' if sucesso else 'falhou'}."
            ),
        )


def monitorar_nvidia(
    log_file=LOG_PADRAO,
    intervalo=INTERVALO_PADRAO,
    auto_otimizar=False,
    limite_vram=LIMITE_VRAM_PADRAO,
    limite_ram=LIMITE_RAM_PADRAO,
):
    service = MonitoringService(
        log_file=log_file,
        intervalo=intervalo,
        auto_otimizar=auto_otimizar,
        limite_vram=limite_vram,
        limite_ram=limite_ram,
    )
    service.run()
