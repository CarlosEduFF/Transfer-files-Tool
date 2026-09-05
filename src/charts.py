"""
Widgets de gráfico ao vivo para CPU e RAM.
"""
from __future__ import annotations
from collections import deque

import pyqtgraph as pg
from PyQt6.QtWidgets import QVBoxLayout, QWidget

# 60 pontso 1 amostra por segundo = 1 minuto visível de histórico
HISTORY = 60

class LiveChart(QWidget):
    """
    Gráfico de uma métrica em percentual, com histórico deslizante.
    """
    def __init__(self, titulo: str, cor: str, parent=None):
        super().__init__(parent)
        self._titulo = titulo
        
        # deque com maxlen descarta o ponto mais antigo sozinho ao inserir o 61°
        # Uma lista comum exigiria fatiar a cada ciclo e cresceria sem limite.
        
        self._dados: deque[float] = deque([0.0] * HISTORY, maxlen=HISTORY)
        self._plot = pg.PlotWidget()
        self._plot.setBackground("#1e1e1e")
        self._plot.showGrid(x=False, y=True, alpha=0.2)
        #Eixo fixo: sem isso o pyqtgraph autoescala e uma variação de 2% ocupa
        # a altura toda, dando impressão falsa de pico.
        self._plot.setYRange(0, 100, padding=0)
        self._plot.setMouseEnabled(x=False, y=False)
        # é painel, não gráfico exploratório
        self._plot.hideButtons()
        self._plot.setMenuEnabled(False)
        
        pen = pg.mkPen(color=cor, width=2)
        # fillevel=0 preenche a área sob a curva: lê se melhor de relace.
        
        self._curva = self._plot.plot(list(self._dados), pen=pen, fillLevel=0, brush=pg.mkBrush(cor + "40"))
        
        self._plot.setTitle(f"{titulo}: --", color="#dddddd", size="10pt")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._plot)
        
    def push(self, valor: float, legenda: str | None = None) -> None: 
        """
        Adiciona um ponto e redesenha. Chamado uma vez por segundo, na thread da UI.
        """
        self._dados.append(valor)
        # setData substitui os dados do item já existente — bem mais barato que
        # criar um item de plot novo a cada atualização.
        self._curva.setData(list(self._dados))
        self._plot.setTitle(
            f"{self._titulo}: {legenda or f'{valor:.1f}%'}", color="#dddddd", size="10pt"
        )