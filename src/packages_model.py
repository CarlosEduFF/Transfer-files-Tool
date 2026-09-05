"""Modelo da tabela de pacotes instalados."""
from __future__ import annotations

from PyQt6.QtCore import QAbstractTableModel, Qt, QModelIndex

from toolchains import Pacote

COL_PACOTE, COL_VERSAO, COL_GERENCIADOR = range(3)
HEADERS = ["Pacote", "Versão", "Gerenciador"]


class PackagesTableModel(QAbstractTableModel):
    """
    Lista de pacotes de um gerenciador. Reset simples na atualização: a lista só
    muda quando o usuário troca de linguagem ou desinstala algo, não a cada ciclo.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._rows: list[Pacote] = []

    def rowCount(self, parent=QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self._rows)

    def columnCount(self, parent=QModelIndex()) -> int:
        return 0 if parent.isValid() else len(HEADERS)

    def data(self, index: QModelIndex, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        pacote = self._rows[index.row()]
        col = index.column()

        if role == Qt.ItemDataRole.DisplayRole:
            return {
                COL_PACOTE: pacote.nome,
                COL_VERSAO: pacote.versao,
                COL_GERENCIADOR: pacote.gerenciador,
            }[col]

        if role == Qt.ItemDataRole.UserRole:
            return {
                COL_PACOTE: pacote.nome.lower(),
                COL_VERSAO: pacote.versao,
                COL_GERENCIADOR: pacote.gerenciador,
            }[col]

        return None

    def headerData(self, section: int, orientation, role=Qt.ItemDataRole.DisplayRole):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return HEADERS[section]
        return None

    def update(self, pacotes: list[Pacote]) -> None:
        self.beginResetModel()
        self._rows = pacotes
        self.endResetModel()

    def pacote_at(self, row: int) -> Pacote | None:
        return self._rows[row] if 0 <= row < len(self._rows) else None
