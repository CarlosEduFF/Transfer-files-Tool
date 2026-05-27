from __future__ import annotations

from hdmi_optimizer.models import DiagnosticSnapshot


SEPARADOR = "-----------------------------------------"


def formatar_telas(snapshot: DiagnosticSnapshot):
    if snapshot.erro_telas:
        return [f"  - {snapshot.erro_telas}"]

    if not snapshot.telas:
        return ["  - Nenhuma tela detectada."]

    return [f"  - {tela.tipo}: {tela.resolucao}" for tela in snapshot.telas]


def formatar_snapshot(snapshot: DiagnosticSnapshot):
    linhas = [
        f"Horario: {snapshot.horario.strftime('%H:%M:%S')}",
        SEPARADOR,
    ]

    gpu = snapshot.gpu
    if gpu.disponivel:
        linhas.extend(
            [
                f"PLACA DE VIDEO ({gpu.nome}):",
                f"  - Uso da GPU: {gpu.uso_percent}%",
                f"  - Temperatura: {gpu.temperatura_c} C",
                "  - Memoria VRAM: "
                f"{gpu.vram_usada_mb}MB / {gpu.vram_total_mb}MB "
                f"({gpu.vram_percent:.1f}%)",
            ]
        )
    else:
        linhas.append(gpu.erro or "GPU Nvidia nao inicializada corretamente.")

    linhas.extend(
        [
            SEPARADOR,
            "SISTEMA:",
            f"  - Uso da CPU: {snapshot.sistema.cpu_percent}%",
            f"  - Uso da RAM: {snapshot.sistema.ram_percent}%",
            SEPARADOR,
            "RESOLUCAO DETECTADA:",
        ]
    )
    linhas.extend(formatar_telas(snapshot))
    linhas.append(SEPARADOR)

    if snapshot.acao:
        linhas.append(snapshot.acao)

    if snapshot.resultado:
        linhas.append(snapshot.resultado)

    linhas.append("")
    return linhas


class DiagnosticLogWriter:
    def __init__(self, caminho):
        self.caminho = caminho
        self._arquivo = None

    def __enter__(self):
        self._arquivo = open(self.caminho, "w", encoding="utf-8")
        return self

    def __exit__(self, exc_type, exc, traceback):
        if self._arquivo:
            self._arquivo.close()

    def escrever_cabecalho(self, nome_gpu):
        self._arquivo.write(f"=== LOG DE MONITORAMENTO - {nome_gpu} ===\n\n")

    def escrever_snapshot(self, snapshot: DiagnosticSnapshot):
        self._arquivo.write("\n".join(formatar_snapshot(snapshot)) + "\n")
        self._arquivo.flush()
