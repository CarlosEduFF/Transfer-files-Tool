"""Ponto de entrada do ProcessMonitor."""
from __future__ import annotations

import sys
from pathlib import Path


def _identidade_windows() -> None:
    """
    Registra um AppUserModelID próprio para a barra de tarefas do Windows.

    Sem isto o Windows trata a janela como pertencente ao python.exe: a barra de
    tarefas agrupa o app com outros scripts e mostra o ícone do interpretador,
    ignorando o setWindowIcon.

    Precisa rodar ANTES de qualquer import do Qt — por isso está aqui em cima, e
    não dentro de main(). Importar window/charts carrega o pyqtgraph, que já
    inicializa o Qt e faz o processo se apresentar ao shell do Windows; a partir
    daí o AppID passa a ser ignorado e a barra de tarefas mantém o ícone do
    interpretador.
    """
    try:
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            "CarlosEduFF.ProcessMonitor"
        )
    except (ImportError, AttributeError, OSError):
        # Outro sistema operacional ou API indisponível: o app funciona igual,
        # apenas sem ícone próprio na barra de tarefas.
        pass


_identidade_windows()

from PyQt6.QtCore import QTimer           # noqa: E402 — depois de _identidade_windows()
from PyQt6.QtGui import QIcon             # noqa: E402
from PyQt6.QtWidgets import QApplication  # noqa: E402

from winicon import aplicar_icone_win32   # noqa: E402
from window import MainWindow             # noqa: E402

# Resolvidos a partir deste arquivo, não do diretório de trabalho: o app pode ser
# iniciado de qualquer pasta ("python src/main.py" ou de dentro de src/), e um
# caminho relativo não acharia o arquivo em metade dos casos.
#
# O .ico é o formato nativo de ícone do Windows e traz as sete resoluções num
# arquivo só, já com a margem branca do PNG recortada e os cantos transparentes.
# Gere-o com "python tools/gerar_icone.py" sempre que trocar o Icon.png.
RAIZ = Path(__file__).resolve().parent.parent
ICONE_ICO = RAIZ / "Icon.ico"
ICONE_PNG = RAIZ / "Icon.png"


def _icone() -> QIcon:
    """Ícone do app, preferindo o .ico e caindo para o .png se ele não existir."""
    if ICONE_ICO.exists():
        return QIcon(str(ICONE_ICO))
    if ICONE_PNG.exists():
        # Sem o .ico o ícone aparece com a moldura branca do PNG original, mas o
        # app abre normalmente. Rode tools/gerar_icone.py para corrigir.
        return QIcon(str(ICONE_PNG))
    return QIcon()


def main() -> int:
    # _identidade_windows() já rodou no topo do módulo, antes dos imports do Qt.
    app = QApplication(sys.argv)
    app.setApplicationName("ProcessMonitor")
    # Estilo Fusion: consistente entre versões do Windows e combina com o
    # fundo escuro dos gráficos, que é fixo no pyqtgraph.
    app.setStyle("Fusion")

    # No QApplication, não só na janela: assim as QMessageBox de confirmação
    # herdam o mesmo ícone.
    app.setWindowIcon(_icone())

    janela = MainWindow()
    janela.show()

    # Depois do show(): o handle da janela só existe a partir daí. O Qt já definiu
    # o ícone da janela, mas não o da classe dela — e é o da classe que a barra de
    # tarefas usa numa QMainWindow. Ver winicon.py.
    hwnd = int(janela.winId())
    aplicar_icone_win32(hwnd, ICONE_ICO)

    # E de novo com um atraso. A gravação acima persiste (medido: o valor da classe
    # não é revertido), mas o shell captura o ícone no instante em que registra a
    # janela na barra de tarefas, e não relê depois. Gravar antes desse instante
    # não tem efeito visível; esta segunda passagem cai depois dele.
    QTimer.singleShot(1500, lambda: aplicar_icone_win32(hwnd, ICONE_ICO))

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
