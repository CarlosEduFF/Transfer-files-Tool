"""
Modelo de dados da tabela de processos (camada model do Qt)
"""

from __future__ import annotations

from PyQt6.QtCore import QAbstractTableModel, QFileInfo, Qt, QModelIndex
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QFileIconProvider

from categorias import NOMES as NOMES_CATEGORIA
from sampler import ProcInfo

# Role própria para a view saber se a linha é um cabeçalho de seção. Um valor
# alto e fixo evita colidir com as roles do Qt.
ROLE_CABECALHO = Qt.ItemDataRole.UserRole + 1

#Indices das colunas. Nomeados para não espalhar números mágicos pelo código
COL_PID, COL_NAME, COL_DESC, COL_CPU, COL_MEM, COL_USER, COL_STATUS = range(7)
HEADERS = ["PID", "Nome", "Descrição", "CPU%", "Memória", "Usuário", "Status"]

def fmt_bytes(num_bytes: int) -> str:
    """
    Bytes em unidade legível 1.24GB comunica melhor que 1331439616
    """
    n = num_bytes
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if n < 1024 or unit == "GB":
            return f"{n:.1f} {unit}" if unit != "B" else f'{n} B'
        n/= 1024.0
    return f"{n:.1f} GB"

class ProcessTableModel(QAbstractTableModel):
    """
    Guarda a lista de processos e avisa a view sobre mudanças.
    A ordenação não acontece aqui - fica a cargo do QSortFilterProxyModel.
    Este modelo mantém sempre a ordem em que os dados chegaram.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._rows: list[ProcInfo] = []
        # Ícones: cache caminho do .exe -> QIcon. Precisa viver na thread da UI, pois
        # QIcon/QPixmap não podem ser criados na thread de coleta — por isso o sampler
        # entrega só o caminho do arquivo.
        #
        # A extração custa ~6,5 ms por executável (medido). Fazê-la para os ~103
        # executáveis de uma vez seriam ~670 ms de UI travada; como só acontece dentro
        # de data(), o Qt a dispara apenas para as linhas visíveis (~30), e o custo se
        # dilui conforme a rolagem. Cada executável é lido uma única vez na sessão.
        self._icon_cache: dict[str, QIcon] = {}
        self._icon_provider = QFileIconProvider()
        
    # ---- interfac obrigatória do QAbstractTableModel ----
    
    def rowCount(self, parent=QModelIndex()) -> int: 
        return 0 if parent.isValid() else len(self._rows)
    
    def columnCount(self, parent=QModelIndex()) -> int:
        return 0 if parent.isValid() else len(HEADERS)
    
    def _icone(self, caminho: str) -> QIcon | None:
        """
        Ícone do executável, extraído sob demanda e cacheado por caminho.

        O cache é por CAMINHO, não por PID: os 88 svchost.exe compartilham um ícone
        só. Devolve None para processos protegidos, que não expõem o caminho — a
        célula fica sem ícone, apenas com o nome.
        """
        if not caminho:
            return None
        icone = self._icon_cache.get(caminho)
        if icone is None:
            # ~6,5 ms nesta chamada. Acontece na thread da UI, mas só para as linhas
            # que o Qt está desenhando, e uma única vez por executável.
            icone = self._icon_provider.icon(QFileInfo(caminho))
            self._icon_cache[caminho] = icone
        return icone

    def data(self, index: QModelIndex, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        proc = self._rows[index.row()]
        col = index.column()

        if role == Qt.ItemDataRole.DisplayRole:
            #O que o olhoo lê: formatado.
            return {
                COL_PID: str(proc.pid),
                COL_NAME: proc.name,
                COL_DESC: proc.desc,
                COL_CPU: f"{proc.cpu:.1f}",
                COL_MEM: fmt_bytes(proc.rss),
                COL_USER: proc.user,
                COL_STATUS: proc.status,
            }[col]
        if role == Qt.ItemDataRole.DecorationRole and col == COL_NAME:
            # Ícone ao lado do nome. Só nesta coluna: repetir por linha inteira
            # poluiria a tabela sem acrescentar informação.
            return self._icone(proc.exe)

        if role == Qt.ItemDataRole.UserRole:
            # O que o proxy ordena: valor numérico bruto.
            # Sem isto a ordenação seria alfabética sobre o texto formatado, e
            # "999 MB" apareceria acima de "1.2 GB" — o erro clássico deste tipo de tela.
            return {
                COL_PID: proc.pid,
                COL_NAME: proc.name.lower(),
                COL_DESC: proc.desc.lower(),
                COL_CPU: proc.cpu,
                COL_MEM: proc.rss,
                COL_USER: proc.user.lower(),
                COL_STATUS: proc.status,
            }[col]
        
        if role == Qt.ItemDataRole.TextAlignmentRole and col in (COL_PID, COL_CPU, COL_MEM):
            # Números alinhados à direita ficam comparáveis coluna abaixo.
            return int(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        return None
    
    def headerData(self, section: int, orientation, role= Qt.ItemDataRole.DisplayRole):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return HEADERS[section]
        
        return None
    
    # --- Atualizações ----
    
    def update(self, procs: list[ProcInfo]) -> None:
        """
        Aplica um novo snapshot preservando seleção e rolagem.
        A implementação ingênua seria beginResetModel()/endResetModel(). Funciona, mas limpa a selação e joga a rolagem para o topo a cada segundo - inutilizavel.
        Em vez disso: casamos as linhas por PID e emitimos apenas o que mudou.
        """
        novos_por_pid = {p.pid: p for p in procs}
        pids_atuais = [p.pid for p in self._rows]
        # 1) Remover, de trás para frente. De frente para trás, cada remoção
        #    deslocaria os índices seguintes e removeríamos a linha errada.
        for i in range(len(pids_atuais) -1, -1 , -1):
            if pids_atuais[i] not in novos_por_pid:
                self.beginRemoveRows(QModelIndex(), i, i)
                del self._rows[i]
                self.endRemoveRows()
        # 2) Atualizar os que continuam vivos, no lugar.
        # Uma única emissão de dataChanged cobrindo o menor..maior índice alterado,
        # em vez de uma emissão por linha: com a maioria das ~250+ linhas mudando
        # de CPU% a cada ciclo, emitir por linha custava dezenas de ms em overhead
        # de sinal/slot (medido: até ~200ms/ciclo, travando a UI).
        pids_restantes = {p.pid for p in self._rows}
        primeiro_alterado = None
        ultimo_alterado = None
        for i, antigo in enumerate(self._rows):
            novo = novos_por_pid[antigo.pid]
            if novo != antigo: # dataclass frozen compara campo a campo
                self._rows[i] = novo
                if primeiro_alterado is None:
                    primeiro_alterado = i
                ultimo_alterado = i
        if primeiro_alterado is not None:
            self.dataChanged.emit(
                self.index(primeiro_alterado, 0),
                self.index(ultimo_alterado, len(HEADERS) - 1),
            )

        # 3) Inserir os processos que nasceram desde o último snapshot.
        novatos = [p for pid , p in novos_por_pid.items() if pid not in pids_restantes]
        if novatos:
            inicio = len(self._rows)
            self.beginInsertRows(QModelIndex(), inicio, inicio + len(novatos) - 1)
            self._rows.extend(novatos)
            self.endInsertRows()
            
    def categoria_da_linha(self, row: int) -> int:
        """Categoria do processo naquela linha; usado pelo proxy para agrupar."""
        return self._rows[row].categoria if 0 <= row < len(self._rows) else 0

    def proc_at(self, row: int) -> ProcInfo | None:
        """
        Usado pela janela para saber qual processo o usuário selecionou.
        """
        return self._rows[row] if 0 <= row < len(self._rows) else None
    