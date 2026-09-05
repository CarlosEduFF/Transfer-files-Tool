"""
Threads para as operações lentas da aba Toolchains.

Tudo que este módulo faz custa segundos (detecção ~1 s, listagem de pacotes até
dezenas de segundos na primeira vez, desinstalação idem). Na thread da UI isso
congelaria a janela — o mesmo problema que a coleta de processos causou neste
projeto. Cada operação vira uma QThread descartável que sinaliza o resultado.
"""
from __future__ import annotations

from PyQt6.QtCore import QThread, pyqtSignal

from toolchains import Pacote, Toolchain, desinstalar, detectar, listar_pacotes


class DeteccaoWorker(QThread):
    """Varre o PATH atrás das linguagens instaladas."""

    progresso = pyqtSignal(str, int, int)   # nome, indice, total
    encontrado = pyqtSignal(object)         # Toolchain, assim que identificado
    concluido = pyqtSignal(object)          # list[Toolchain]

    def run(self) -> None:
        try:
            achados = detectar(
                progresso=self.progresso.emit, encontrado=self.encontrado.emit
            )
        except Exception:
            # Uma falha aqui não pode derrubar a thread em silêncio: a UI ficaria
            # esperando um sinal que nunca chega, com a mensagem "detectando..."
            # presa na tela.
            achados = []
        self.concluido.emit(achados)


class PacotesWorker(QThread):
    """Lista os pacotes de um gerenciador."""

    concluido = pyqtSignal(str, object)     # gerenciador, list[Pacote]

    def __init__(self, gerenciador: str, parent=None):
        super().__init__(parent)
        self._gerenciador = gerenciador

    def run(self) -> None:
        try:
            pacotes = listar_pacotes(self._gerenciador)
        except Exception:
            pacotes = []
        self.concluido.emit(self._gerenciador, pacotes)


class DesinstalacaoWorker(QThread):
    """Executa a desinstalação de um pacote."""

    concluido = pyqtSignal(bool, str, object)   # sucesso, saída, Pacote

    def __init__(self, pacote: Pacote, parent=None):
        super().__init__(parent)
        self._pacote = pacote

    def run(self) -> None:
        try:
            ok, saida = desinstalar(self._pacote)
        except Exception as e:
            ok, saida = False, f"Falha ao executar: {e}"
        self.concluido.emit(ok, saida, self._pacote)
