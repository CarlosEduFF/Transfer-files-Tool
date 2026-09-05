"""Janela principal: layout, ligação de sinais e ação de encerrar processo."""
from __future__ import annotations

import psutil
from PyQt6.QtCore import QSize, QSortFilterProxyModel, Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QAbstractItemView, QFrame, QHBoxLayout, QHeaderView, QLabel, QLineEdit,
    QListWidget, QListWidgetItem, QMainWindow, QMessageBox, QPushButton,
    QStackedWidget, QTabBar, QTableView, QVBoxLayout, QWidget,
)

from categorias import APLICATIVO, SEGUNDO_PLANO, SISTEMA
from categorias import NOMES as NOMES_CATEGORIA
from charts import LiveChart
from models import COL_CPU, COL_DESC, COL_NAME, ProcessTableModel
from packages_model import COL_PACOTE as KCOL_PACOTE
from packages_model import PackagesTableModel
from ports_model import COL_PORTA as PCOL_PORTA
from ports_model import COL_PROCESSO as PCOL_PROCESSO
from ports_model import PortsTableModel
from sampler import SamplerWorker, Snapshot
from toolchains import comando_desinstalar
from toolchains_worker import DeteccaoWorker, DesinstalacaoWorker, PacotesWorker

# Encerrar qualquer um destes derruba o Windows na hora, com perda de dados.
# Primeira das três camadas de proteção (decisão 4.9).
PROTEGIDOS = {
    "system", "system idle process", "smss.exe", "csrss.exe", "wininit.exe",
    "services.exe", "lsass.exe", "winlogon.exe", "registry", "memory compression",
}


class FiltroProxy(QSortFilterProxyModel):
    """
    Proxy que filtra por texto (nome do executável OU descrição) e por categoria.

    O QSortFilterProxyModel padrão só filtra uma coluna (setFilterKeyColumn), e aqui
    as duas importam: quem procura "spooler" não sabe que o processo se chama
    spoolsv.exe, e quem procura "chrome.exe" não quer depender da descrição.

    A categoria vem das abas embaixo da tabela; None mostra todas.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._categoria = None

    def definir_categoria(self, categoria: int | None) -> None:
        self._categoria = categoria
        self.invalidateFilter()

    def filterAcceptsRow(self, row: int, parent) -> bool:
        modelo = self.sourceModel()

        if self._categoria is not None:
            if modelo.categoria_da_linha(row) != self._categoria:
                return False

        padrao = self.filterRegularExpression().pattern()
        if not padrao:
            return True
        for coluna in (COL_NAME, COL_DESC):
            texto = modelo.data(modelo.index(row, coluna, parent), Qt.ItemDataRole.DisplayRole)
            if texto and padrao.lower() in texto.lower():
                return True
        return False


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ProcessMonitor")
        self.resize(1000, 700)

        # Estado da aba Toolchains. None = ainda não detectado; a detecção só roda
        # quando a aba é aberta pela primeira vez.
        self._toolchains = None
        self._detectou = False    # a aba já disparou a detecção alguma vez?
        self._worker_deteccao = None
        self._worker_desinstalacao = None
        # QThread coletado pelo GC no meio da execução mata a thread; a lista
        # mantém a referência viva até o fim.
        self._workers_pacotes = []

        # ---------- gráficos ----------
        self.cpu_chart = LiveChart("CPU", "#4fc3f7")
        self.ram_chart = LiveChart("RAM", "#81c784")
        graficos = QHBoxLayout()
        graficos.addWidget(self.cpu_chart)
        graficos.addWidget(self.ram_chart)

        # ---------- barra de controles ----------
        self.busca = QLineEdit()
        self.busca.setPlaceholderText("Filtrar por nome ou descrição...")
        self.busca.setClearButtonEnabled(True)
        self.btn_kill = QPushButton("Encerrar processo")
        self.btn_kill.setEnabled(False)   # só habilita quando houver linha selecionada
        self.lbl_status = QLabel("Iniciando...")

        controles = QHBoxLayout()
        controles.addWidget(self.busca, stretch=1)
        controles.addWidget(self.btn_kill)

        # ---------- tabela: model → proxy → view ----------
        self.model = ProcessTableModel()
        self.proxy = FiltroProxy()
        self.proxy.setSourceModel(self.model)
        # Ordena pelo valor bruto guardado em UserRole, não pelo texto exibido:
        # é o que faz 1.2 GB ficar acima de 999 MB (ver models.data).
        self.proxy.setSortRole(Qt.ItemDataRole.UserRole)
        self.proxy.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        # False: não reordena a cada dataChanged. Com True, uma linha cujo CPU mudou
        # saltaria de posição no instante em que você fosse clicar nela — exatamente
        # o defeito do Gerenciador de Tarefas que motivou este projeto.
        self.proxy.setDynamicSortFilter(False)

        self.table = QTableView()
        self.table.setModel(self.proxy)
        self.table.setSortingEnabled(True)
        self.table.sortByColumn(COL_CPU, Qt.SortOrder.DescendingOrder)  # maiores no topo
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        # Ícones de 16px com uma folga. setDefaultSectionSize em vez de deixar o Qt
        # medir linha a linha: com altura fixa ele não precisa consultar o modelo
        # para calcular o layout da rolagem.
        self.table.verticalHeader().setDefaultSectionSize(22)
        self.table.setIconSize(QSize(16, 16))
        # A Descrição é a coluna que estica: é o texto mais longo e o mais útil para
        # identificar o processo. O nome do .exe tem largura previsível.
        self.table.horizontalHeader().setSectionResizeMode(
            COL_DESC, QHeaderView.ResizeMode.Stretch
        )
        self.table.horizontalHeader().setSectionResizeMode(
            COL_NAME, QHeaderView.ResizeMode.ResizeToContents
        )
        # ---------- abas de categoria, no rodapé da tabela ----------
        self.abas = QTabBar()
        self.abas.setExpanding(False)
        self.abas.setDrawBase(False)
        # Formato de "documento": no Qt é o que desenha as abas presas à borda,
        # como as planilhas do Excel.
        self.abas.setShape(QTabBar.Shape.RoundedSouth)
        self.abas.setDocumentMode(True)
        # A ordem das abas segue as constantes de categorias.py; _CATS_ABA faz a
        # tradução do índice da aba para a categoria (None = todas).
        self._CATS_ABA = [None, APLICATIVO, SEGUNDO_PLANO, SISTEMA]
        for titulo in ("Todos", *(NOMES_CATEGORIA[c] for c in self._CATS_ABA[1:])):
            self.abas.addTab(titulo)
        self.abas.setCurrentIndex(0)
        self.abas.currentChanged.connect(self._on_aba_categoria)
        self.abas.setStyleSheet("""
            QTabBar::tab { background: #2d2d30; color: #cccccc;
                           padding: 5px 14px; margin-right: 2px;
                           border: 1px solid #3c3c3c; border-top: none;
                           border-bottom-left-radius: 4px;
                           border-bottom-right-radius: 4px; }
            QTabBar::tab:selected { background: #1e1e1e; color: #ffffff;
                                    border-bottom: 2px solid #4fc3f7; }
            QTabBar::tab:hover:!selected { background: #37373d; }
        """)

        # ---------- página Monitor ----------
        pagina_monitor = QWidget()
        layout_monitor = QVBoxLayout(pagina_monitor)
        layout_monitor.setContentsMargins(0, 0, 0, 0)
        layout_monitor.addLayout(graficos, stretch=1)
        layout_monitor.addLayout(controles)
        layout_monitor.addWidget(self.table, stretch=3)
        # Abas coladas na base da tabela, sem espaçamento entre as duas.
        layout_monitor.addWidget(self.abas)

        # ---------- página Ports ----------
        pagina_portas = self._montar_pagina_portas()

        # ---------- página Toolchains ----------
        pagina_tools = self._montar_pagina_toolchains()

        # ---------- montagem: barra lateral + páginas ----------
        self.paginas = QStackedWidget()
        self.paginas.addWidget(pagina_monitor)
        self.paginas.addWidget(pagina_portas)
        self.paginas.addWidget(pagina_tools)

        self.menu = self._montar_menu_lateral()

        conteudo = QVBoxLayout()
        conteudo.setContentsMargins(8, 8, 8, 4)
        conteudo.addWidget(self.paginas)
        conteudo.addWidget(self.lbl_status)

        central = QWidget()
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.menu)
        layout.addLayout(conteudo, stretch=1)
        self.setCentralWidget(central)

        # ---------- sinais ----------
        self.busca.textChanged.connect(self.proxy.setFilterFixedString)
        self.btn_kill.clicked.connect(self._on_kill)
        self.table.selectionModel().selectionChanged.connect(self._on_selection)
        self.table.doubleClicked.connect(lambda _: self._on_kill())

        # ---------- thread de coleta ----------
        # 1 s: com a coleta em lotes (ver LOTE no sampler), cada ciclo custa ~70 ms
        # em vez dos ~1200 ms da varredura completa, então cabe folgado no intervalo.
        self.worker = SamplerWorker(interval_ms=1000)
        # Sinal entre threads: o Qt enfileira a entrega na thread da UI
        # automaticamente. É por isso que não precisamos de Lock aqui.
        self.worker.snapshot_ready.connect(self._on_snapshot)
        self.worker.start()

    # ---------- montagem das partes ----------

    def _montar_menu_lateral(self) -> QListWidget:
        """
        Barra lateral de navegação entre as páginas.

        Um QListWidget em vez de botões soltos: ele já traz seleção exclusiva,
        realce do item ativo e navegação por teclado, que teriam de ser refeitos à
        mão com QPushButton.
        """
        menu = QListWidget()
        menu.addItem(QListWidgetItem("  Monitor"))
        menu.addItem(QListWidgetItem("  Ports"))
        menu.addItem(QListWidgetItem("  Toolchains"))
        menu.setCurrentRow(0)
        menu.setFixedWidth(150)
        menu.setFrameShape(QFrame.Shape.NoFrame)
        menu.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        menu.setStyleSheet("""
            QListWidget { background: #252526; border-right: 1px solid #3c3c3c;
                          outline: none; padding-top: 6px; }
            QListWidget::item { color: #cccccc; padding: 10px 6px; }
            QListWidget::item:selected { background: #37373d; color: #ffffff;
                                         border-left: 2px solid #4fc3f7; }
            QListWidget::item:hover:!selected { background: #2d2d30; }
        """)
        menu.currentRowChanged.connect(self._on_pagina_mudou)
        return menu

    def _montar_pagina_portas(self) -> QWidget:
        """Página com a tabela de portas em escuta."""
        self.busca_porta = QLineEdit()
        self.busca_porta.setPlaceholderText("Filtrar por porta, processo ou serviço...")
        self.busca_porta.setClearButtonEnabled(True)

        self.btn_kill_porta = QPushButton("Liberar porta (encerrar processo)")
        self.btn_kill_porta.setEnabled(False) # só com uma linha que tenha PID

        self.lbl_portas = QLabel("Portas em escuta na máquina")

        self.ports_model = PortsTableModel()
        self.ports_proxy = QSortFilterProxyModel()
        self.ports_proxy.setSourceModel(self.ports_model)
        self.ports_proxy.setSortRole(Qt.ItemDataRole.UserRole)
        # -1: filtra por qualquer coluna. Assim tanto "8080" quanto "postgres" ou
        # "Code.exe" encontram a linha, que é como a busca é usada aqui.
        self.ports_proxy.setFilterKeyColumn(-1)
        self.ports_proxy.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)

        self.ports_table = QTableView()
        self.ports_table.setModel(self.ports_proxy)
        self.ports_table.setSortingEnabled(True)
        self.ports_table.sortByColumn(PCOL_PORTA, Qt.SortOrder.AscendingOrder)
        self.ports_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.ports_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.ports_table.setAlternatingRowColors(True)
        self.ports_table.verticalHeader().setVisible(False)
        self.ports_table.verticalHeader().setDefaultSectionSize(22)
        self.ports_table.horizontalHeader().setSectionResizeMode(
            PCOL_PROCESSO, QHeaderView.ResizeMode.Stretch
        )

        self.busca_porta.textChanged.connect(self.ports_proxy.setFilterFixedString)
        self.btn_kill_porta.clicked.connect(self._on_kill_porta)
        self.ports_table.selectionModel().selectionChanged.connect(
            self._on_selection_porta
        )
        # O modelo é resetado a cada ciclo (beginResetModel), e o reset limpa a
        # seleção — sem religar aqui, o botão ficaria habilitado sem linha marcada.
        self.ports_model.modelReset.connect(self._on_selection_porta)

        controles = QHBoxLayout()
        controles.addWidget(self.busca_porta, stretch=1)
        controles.addWidget(self.btn_kill_porta)

        pagina = QWidget()
        layout = QVBoxLayout(pagina)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.lbl_portas)
        layout.addLayout(controles)
        layout.addWidget(self.ports_table, stretch=1)
        return pagina

    def _montar_pagina_toolchains(self) -> QWidget:
        """
        Página com as linguagens instaladas e os pacotes de cada uma.

        Nada é carregado aqui: a detecção custa ~1 s e a listagem de pacotes pode
        levar dezenas de segundos na primeira vez. Tudo acontece sob demanda, em
        thread própria (ver toolchains_worker.py), quando a aba é aberta.
        """
        self.tools_lista = QListWidget()
        self.tools_lista.setFixedWidth(230)
        self.tools_lista.currentRowChanged.connect(self._on_toolchain_escolhida)

        self.lbl_tools = QLabel("Abrindo…")
        self.lbl_tools.setWordWrap(True)

        self.btn_detectar = QPushButton("Verificar novamente")
        self.btn_detectar.clicked.connect(lambda: self._detectar_toolchains())

        self.busca_pacote = QLineEdit()
        self.busca_pacote.setPlaceholderText("Filtrar pacotes...")
        self.busca_pacote.setClearButtonEnabled(True)

        self.btn_desinstalar = QPushButton("Desinstalar pacote")
        self.btn_desinstalar.setEnabled(False)

        self.pkg_model = PackagesTableModel()
        self.pkg_proxy = QSortFilterProxyModel()
        self.pkg_proxy.setSourceModel(self.pkg_model)
        self.pkg_proxy.setSortRole(Qt.ItemDataRole.UserRole)
        self.pkg_proxy.setFilterKeyColumn(-1)
        self.pkg_proxy.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)

        self.pkg_table = QTableView()
        self.pkg_table.setModel(self.pkg_proxy)
        self.pkg_table.setSortingEnabled(True)
        self.pkg_table.sortByColumn(KCOL_PACOTE, Qt.SortOrder.AscendingOrder)
        self.pkg_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.pkg_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.pkg_table.setAlternatingRowColors(True)
        self.pkg_table.verticalHeader().setVisible(False)
        self.pkg_table.verticalHeader().setDefaultSectionSize(22)
        self.pkg_table.horizontalHeader().setSectionResizeMode(
            KCOL_PACOTE, QHeaderView.ResizeMode.Stretch
        )

        self.busca_pacote.textChanged.connect(self.pkg_proxy.setFilterFixedString)
        self.btn_desinstalar.clicked.connect(self._on_desinstalar)
        self.pkg_table.selectionModel().selectionChanged.connect(
            self._on_selection_pacote
        )
        self.pkg_model.modelReset.connect(self._on_selection_pacote)

        topo = QHBoxLayout()
        topo.addWidget(self.lbl_tools, stretch=1)
        topo.addWidget(self.btn_detectar)

        controles = QHBoxLayout()
        controles.addWidget(self.busca_pacote, stretch=1)
        controles.addWidget(self.btn_desinstalar)

        direita = QVBoxLayout()
        direita.setContentsMargins(0, 0, 0, 0)
        direita.addLayout(controles)
        direita.addWidget(self.pkg_table, stretch=1)
        painel_direito = QWidget()
        painel_direito.setLayout(direita)

        corpo = QHBoxLayout()
        corpo.addWidget(self.tools_lista)
        corpo.addWidget(painel_direito, stretch=1)

        pagina = QWidget()
        layout = QVBoxLayout(pagina)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(topo)
        layout.addLayout(corpo, stretch=1)
        return pagina

    # ---------- aba Toolchains ----------

    def _on_pagina_mudou(self, indice: int) -> None:
        self.paginas.setCurrentIndex(indice)
        # Detecta na primeira vez que a aba é aberta, não no arranque: gastar ~1 s
        # com subprocessos para uma aba que talvez não seja visitada atrasaria a
        # janela à toa.
        if indice == 2 and not self._detectou and self._worker_deteccao is None:
            self._detectou = True
            self._detectar_toolchains()

    def _detectar_toolchains(self) -> None:
        if self._worker_deteccao is not None:
            return # já em andamento
        self.btn_detectar.setEnabled(False)
        self._toolchains = None   # descarta o resultado anterior
        self.tools_lista.clear()
        self.pkg_model.update([])
        self.lbl_tools.setText("Procurando linguagens instaladas…")

        self._worker_deteccao = DeteccaoWorker(self)
        self._worker_deteccao.progresso.connect(
            lambda nome, i, total: self.lbl_tools.setText(
                f"Verificando {nome}… ({i + 1}/{total})"
            )
        )
        # Preenche a lista aos poucos: a varredura leva ~6 s (o flutter sozinho
        # responde por ~5 s), e deixar a lista vazia até o fim parece travamento.
        self._worker_deteccao.encontrado.connect(self._on_toolchain_encontrada)
        self._worker_deteccao.concluido.connect(self._on_toolchains_detectadas)
        self._worker_deteccao.start()

    def _on_toolchain_encontrada(self, tc) -> None:
        # Vai preenchendo _toolchains junto com a lista visível: sem isto, clicar
        # num item durante a varredura não faria nada, porque _on_toolchain_escolhida
        # consulta esta lista para saber qual linguagem foi escolhida.
        if self._toolchains is None:
            self._toolchains = []
        self._toolchains.append(tc)

        rotulo = f"{tc.nome}  {tc.versao}"
        if tc.gerenciador:
            rotulo += f"   ({tc.gerenciador})"
        item = QListWidgetItem(rotulo)
        if not tc.no_path:
            # Instalado, mas invisível ao terminal. Vale sinalizar: é a diferença
            # entre "não tenho" e "tenho, mas o comando não funciona no console".
            item.setToolTip(f"{tc.caminho}\n(fora do PATH)")
            item.setForeground(QColor("#c8a35a"))
        self.tools_lista.addItem(item)

    def _on_toolchains_detectadas(self, achados) -> None:
        self._toolchains = achados
        self._worker_deteccao = None
        self.btn_detectar.setEnabled(True)

        if not achados:
            self.lbl_tools.setText("Nenhuma linguagem encontrada no PATH.")
            return

        # A lista já foi preenchida item a item por _on_toolchain_encontrada; aqui
        # só resta o resumo e a seleção inicial.
        com_ger = sum(1 for t in achados if t.gerenciador)
        self.lbl_tools.setText(
            f"{len(achados)} linguagens encontradas — {com_ger} com gerenciador de "
            "pacotes. Selecione uma para ver os pacotes instalados."
        )
        self.tools_lista.setCurrentRow(0)

    def _on_toolchain_escolhida(self, linha: int) -> None:
        if self._toolchains is None or not (0 <= linha < len(self._toolchains)):
            return
        tc = self._toolchains[linha]
        self.pkg_model.update([])

        if not tc.gerenciador:
            aviso = "" if tc.no_path else "  ⚠ fora do PATH"
            self.lbl_tools.setText(
                f"{tc.nome} {tc.versao} — {tc.caminho}{aviso}\n"
                "Sem gerenciador de pacotes detectado para esta linguagem."
            )
            return

        if tc.pacotes_carregados:
            self.pkg_model.update(tc.pacotes)
            self._mostrar_resumo(tc)
            return

        self.lbl_tools.setText(
            f"{tc.nome} {tc.versao} — listando pacotes com {tc.gerenciador}… "
            "(pode levar alguns segundos)"
        )
        worker = PacotesWorker(tc.gerenciador, self)
        worker.concluido.connect(self._on_pacotes_listados)
        self._workers_pacotes.append(worker) # mantém referência viva
        worker.start()

    def _on_pacotes_listados(self, gerenciador: str, pacotes) -> None:
        # A resposta pode chegar depois de o usuário ter trocado de linguagem;
        # guardar no toolchain certo (e não no selecionado agora) evita atribuir
        # os pacotes do pip ao Node, por exemplo.
        for tc in self._toolchains or []:
            if tc.gerenciador == gerenciador:
                tc.pacotes = pacotes
                tc.pacotes_carregados = True
                break

        atual = self._toolchain_atual()
        if atual and atual.gerenciador == gerenciador:
            self.pkg_model.update(pacotes)
            self._mostrar_resumo(atual)

    def _mostrar_resumo(self, tc) -> None:
        aviso = "" if tc.no_path else "  ⚠ fora do PATH"
        self.lbl_tools.setText(
            f"{tc.nome} {tc.versao} — {tc.caminho}{aviso}\n"
            f"{len(tc.pacotes)} pacotes instalados via {tc.gerenciador}."
        )

    def _toolchain_atual(self):
        linha = self.tools_lista.currentRow()
        if self._toolchains and 0 <= linha < len(self._toolchains):
            return self._toolchains[linha]
        return None

    def _on_selection_pacote(self) -> None:
        self.btn_desinstalar.setEnabled(
            bool(self.pkg_table.selectionModel().selectedRows())
            and self._worker_desinstalacao is None
        )

    def _on_desinstalar(self) -> None:
        linhas = self.pkg_table.selectionModel().selectedRows()
        if not linhas:
            return
        pacote = self.pkg_model.pacote_at(self.pkg_proxy.mapToSource(linhas[0]).row())
        if pacote is None:
            return

        cmd = comando_desinstalar(pacote)
        if not cmd:
            QMessageBox.warning(
                self, "Não suportado",
                f"Não sei desinstalar pacotes de '{pacote.gerenciador}'.",
            )
            return

        # Mostra o comando exato antes de executar. Desinstalar é destrutivo e nem
        # sempre trivial de desfazer — diferente de encerrar um processo, que basta
        # reabrir —, então o usuário aprova sabendo o que vai rodar.
        resposta = QMessageBox.question(
            self, "Confirmar desinstalação",
            f"Desinstalar este pacote?\n\n"
            f"Pacote: {pacote.nome}\nVersão: {pacote.versao}\n"
            f"Gerenciador: {pacote.gerenciador}\n\n"
            f"Será executado:\n    {' '.join(cmd)}\n\n"
            "Outros programas podem depender deste pacote.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if resposta != QMessageBox.StandardButton.Yes:
            return

        self.btn_desinstalar.setEnabled(False)
        self.lbl_tools.setText(f"Desinstalando {pacote.nome}…")
        self._worker_desinstalacao = DesinstalacaoWorker(pacote, self)
        self._worker_desinstalacao.concluido.connect(self._on_desinstalado)
        self._worker_desinstalacao.start()

    def _on_desinstalado(self, ok: bool, saida: str, pacote) -> None:
        self._worker_desinstalacao = None
        if ok:
            self.lbl_status.setText(f"{pacote.nome} desinstalado.")
        else:
            QMessageBox.critical(
                self, "Falha ao desinstalar",
                f"Não foi possível desinstalar '{pacote.nome}'.\n\n"
                f"{saida[:800]}",
            )
        # Relista de qualquer jeito: mesmo numa falha parcial, a lista atualizada
        # mostra o estado real em vez de depender da heurística de sucesso.
        atual = self._toolchain_atual()
        if atual:
            atual.pacotes_carregados = False
            self._on_toolchain_escolhida(self.tools_lista.currentRow())

    # ---------- reações ----------

    def _on_snapshot(self, snap: Snapshot) -> None:
        """Recebe um snapshot da thread de fundo. Executa na thread da UI."""
        self.cpu_chart.push(snap.cpu_total)
        self.ram_chart.push(
            snap.ram_percent,
            legenda=f"{snap.ram_used / 1024**3:.1f} / {snap.ram_total / 1024**3:.1f} GB",
        )
        self.model.update(snap.procs)

        # Contagem por categoria, exibida no título de cada aba.
        contagens: dict[int, int] = {}
        for p in snap.procs:
            contagens[p.categoria] = contagens.get(p.categoria, 0) + 1
        for i, cat in enumerate(self._CATS_ABA):
            total = len(snap.procs) if cat is None else contagens.get(cat, 0)
            base = "Todos" if cat is None else NOMES_CATEGORIA[cat]
            self.abas.setTabText(i, f"{base} ({total})")

        # Reaplica a ordenação escolhida pelo usuário. Necessário porque
        # setDynamicSortFilter(False) desliga a reordenação automática — aqui ela
        # acontece uma vez por ciclo, em ponto previsível, e não embaixo do cursor.
        self.proxy.sort(self.proxy.sortColumn(), self.proxy.sortOrder())

        # O reset do modelo limpa a seleção. Sem restaurá-la, a linha marcada some a
        # cada segundo e não dá tempo de selecionar uma porta e clicar em liberar.
        marcada = self._porta_selecionada()
        chave = (marcada.porta, marcada.protocolo, marcada.pid) if marcada else None

        self.ports_model.update(snap.portas)
        self.ports_proxy.sort(
            self.ports_proxy.sortColumn(), self.ports_proxy.sortOrder()
        )

        if chave is not None:
            self._reselecionar_porta(chave)
        self.lbl_portas.setText(
            f"{len(snap.portas)} portas em escuta — quem está ocupando cada uma"
        )

        self.lbl_status.setText(f"{len(snap.procs)} processos — atualiza a cada 1 s")

    def _on_aba_categoria(self, indice: int) -> None:
        self.proxy.definir_categoria(self._CATS_ABA[indice])
        self.proxy.sort(self.proxy.sortColumn(), self.proxy.sortOrder())
        # Trocar de aba muda o conjunto de linhas; volta ao topo em vez de manter
        # uma posição de rolagem que não corresponde mais a nada.
        self.table.scrollToTop()

    def _on_selection(self) -> None:
        self.btn_kill.setEnabled(bool(self.table.selectionModel().selectedRows()))

    def _proc_selecionado(self):
        """Traduz a linha visível (proxy) para a linha real do modelo.

        Sem mapToSource() pegaríamos o processo errado sempre que houvesse
        ordenação ou filtro ativo — e mataríamos algo que o usuário não escolheu.
        """
        linhas = self.table.selectionModel().selectedRows()
        if not linhas:
            return None
        return self.model.proc_at(self.proxy.mapToSource(linhas[0]).row())

    def _encerrar(self, pid: int, nome: str, detalhes: str) -> None:
        """
        Encerra um processo com as três camadas de proteção.

        Compartilhado pelas duas telas: encerrar quem ocupa uma porta é a mesma
        operação de encerrar um processo da lista, e duplicar as proteções abriria
        espaço para elas divergirem — uma tela ficaria menos segura que a outra.

        `detalhes` é o corpo da confirmação, que cada tela monta com o que sabe.
        """
        # Camada 1: recusa processos críticos do sistema.
        if nome.lower() in PROTEGIDOS or pid in (0, 4):
            QMessageBox.warning(
                self, "Processo protegido",
                f"'{nome}' (PID {pid}) é essencial ao Windows.\n"
                "Encerrá-lo travaria o sistema, então esta ação foi bloqueada.",
            )
            return

        # Camada 2: confirmação com os dados à vista e "Não" como padrão,
        # para que um Enter distraído cancele em vez de matar.
        resposta = QMessageBox.question(
            self, "Confirmar encerramento", detalhes,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if resposta != QMessageBox.StandardButton.Yes:
            return

        # Camada 3: encerramento gentil primeiro, forçado só se necessário.
        try:
            p = psutil.Process(pid)
            p.terminate()          # pede o encerramento; o programa ainda pode salvar
            try:
                p.wait(timeout=3)
            except psutil.TimeoutExpired:
                p.kill()           # ignorou o pedido: encerramento abrupto
            self.lbl_status.setText(f"Processo {nome} (PID {pid}) encerrado.")
        except psutil.NoSuchProcess:
            # Morreu sozinho entre a confirmação e a ação. Não é erro.
            self.lbl_status.setText(f"PID {pid} já não existia.")
        except psutil.AccessDenied:
            QMessageBox.critical(
                self, "Acesso negado",
                f"Sem permissão para encerrar '{nome}' (PID {pid}).\n\n"
                "Processos de outro usuário ou do sistema exigem executar o "
                "ProcessMonitor como administrador.",
            )

    def _on_kill(self) -> None:
        proc = self._proc_selecionado()
        if proc is None:
            return
        self._encerrar(
            proc.pid, proc.name,
            f"Encerrar este processo?\n\n"
            f"Nome: {proc.name}\nPID: {proc.pid}\nUsuário: {proc.user}\n\n"
            "Dados não salvos deste programa podem ser perdidos.",
        )

    # ---------- aba Ports ----------

    def _porta_selecionada(self):
        """Traduz a linha visível da tabela de portas para a linha do modelo."""
        linhas = self.ports_table.selectionModel().selectedRows()
        if not linhas:
            return None
        return self.ports_model.porta_at(
            self.ports_proxy.mapToSource(linhas[0]).row()
        )

    def _reselecionar_porta(self, chave: tuple[int, str, int]) -> None:
        """
        Remarca a linha da porta identificada por (porta, protocolo, pid).

        Busca pela chave, não pelo índice: a lista é reordenável e portas entram e
        saem entre ciclos, então guardar a posição selecionaria outra linha. Se a
        porta deixou de existir, a seleção fica vazia — que é o correto.
        """
        for linha in range(self.ports_model.rowCount()):
            p = self.ports_model.porta_at(linha)
            if p and (p.porta, p.protocolo, p.pid) == chave:
                indice = self.ports_proxy.mapFromSource(self.ports_model.index(linha, 0))
                if indice.isValid():
                    self.ports_table.selectRow(indice.row())
                return

    def _on_selection_porta(self) -> None:
        porta = self._porta_selecionada()
        # Sem PID não há o que encerrar: acontece quando o Windows não revela o
        # dono do socket (processos protegidos).
        self.btn_kill_porta.setEnabled(bool(porta and porta.pid))

    def _on_kill_porta(self) -> None:
        porta = self._porta_selecionada()
        if porta is None or not porta.pid:
            return
        servico = f"\nServiço: {porta.servico}" if porta.servico else ""
        self._encerrar(
            porta.pid, porta.processo,
            f"Encerrar o processo que ocupa a porta {porta.porta}?\n\n"
            f"Porta: {porta.porta}/{porta.protocolo}{servico}\n"
            f"Processo: {porta.processo}\nPID: {porta.pid}\n\n"
            "A porta será liberada, e dados não salvos deste programa podem ser "
            "perdidos.",
        )

    def closeEvent(self, event) -> None:
        """Para a thread antes de fechar.

        Sem isto, a QThread continuaria viva e o processo Python não terminaria —
        a janela some da tela mas o programa fica pendurado.
        """
        self.worker.stop()
        self.worker.wait(3000)   # dá até 3 s para o ciclo em andamento terminar

        # As threads da aba Toolchains rodam subprocessos e não têm como ser
        # interrompidas no meio; esperar é o único caminho seguro. Sem isto, fechar
        # durante uma detecção deixaria o processo Python pendurado.
        for w in [self._worker_deteccao, self._worker_desinstalacao,
                  *self._workers_pacotes]:
            if w is not None and w.isRunning():
                w.wait(5000)
        event.accept()
