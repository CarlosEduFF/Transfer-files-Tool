"""Modelo da tabela de portas (camada model do Qt)."""
from __future__ import annotations

from PyQt6.QtCore import QAbstractTableModel, Qt, QModelIndex

from ports import PortInfo

COL_PORTA, COL_PROTO, COL_PROCESSO, COL_PID, COL_ENDERECO, COL_SERVICO = range(6)
HEADERS = ["Porta", "Proto", "Processo", "PID", "Escutando em", "Serviço"]


class PortsTableModel(QAbstractTableModel):
    """
    Guarda as portas em escuta. Ao contrário do modelo de processos, aqui a
    atualização usa reset simples: são poucas dezenas de linhas e elas mudam
    raramente, então o diff por chave não se pagaria.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._rows: list[PortInfo] = []

    def rowCount(self, parent=QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self._rows)

    def columnCount(self, parent=QModelIndex()) -> int:
        return 0 if parent.isValid() else len(HEADERS)

    def data(self, index: QModelIndex, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        porta = self._rows[index.row()]
        col = index.column()

        if role == Qt.ItemDataRole.DisplayRole:
            return {
                COL_PORTA: str(porta.porta),
                COL_PROTO: porta.protocolo,
                COL_PROCESSO: porta.processo,
                COL_PID: str(porta.pid) if porta.pid else "—",
                COL_ENDERECO: porta.endereco,
                COL_SERVICO: porta.servico,
            }[col]

        if role == Qt.ItemDataRole.UserRole:
            # Porta e PID ordenam como número; sem isto a porta 9 viria depois da
            # 1000 por comparação de texto.
            return {
                COL_PORTA: porta.porta,
                COL_PROTO: porta.protocolo,
                COL_PROCESSO: porta.processo.lower(),
                COL_PID: porta.pid,
                COL_ENDERECO: porta.endereco.lower(),
                COL_SERVICO: porta.servico.lower(),
            }[col]

        if role == Qt.ItemDataRole.TextAlignmentRole and col in (COL_PORTA, COL_PID):
            return int(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        return None

    def headerData(self, section: int, orientation, role=Qt.ItemDataRole.DisplayRole):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return HEADERS[section]
        return None

    def update(self, portas: list[PortInfo]) -> None:
        """Substitui a lista inteira."""
        self.beginResetModel()
        self._rows = portas
        self.endResetModel()

    def porta_at(self, row: int) -> PortInfo | None:
        return self._rows[row] if 0 <= row < len(self._rows) else None
