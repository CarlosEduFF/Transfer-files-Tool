"""
Coleta de métricas do sistema em thread separada.

Este módulo não importa nada de interface gráfica além do mínimo de QtCore
(QThread/pyqtSignal). Isso é proposital: a coleta continua testável sem abrir janela.
"""

from __future__ import annotations

import time 
from dataclasses import dataclass, replace

import psutil
from PyQt6.QtCore import QThread, pyqtSignal

from categorias import SEGUNDO_PLANO, classificar, pids_com_janela
from ports import PortInfo, coletar_portas
from winmeta import descricao_do_executavel

#Número de CPUs lógicas, lido uma única vez: não muda durante a execução
#e é usadi para normalizar o CPU% de cada processo.
CPU_COUNT = psutil.cpu_count() or 1

# Quantos processos têm os dados caros relidos por ciclo. Ler os ~254 de uma vez
# custava ~1200 ms e travava a UI: no Windows cada campo abre um handle por
# processo (medido para 254 deles — status 1177 ms, memory_info 534 ms,
# cpu_percent 521 ms). Com 15 por ciclo o custo cai para ~70 ms; em troca, cada
# processo tem esses campos renovados a cada ~17 ciclos.
LOTE = 15

@dataclass(frozen=True)
class ProcInfo:
    """
    Uma linha da tabela. Imutável: é criada na trherad de coleta e lida na thread da UI -
    um objeto congelado elimina quelquer dúvida sobre sobre quem pode alterá-lo.
    """
    pid: int
    name: str
    cpu: float # já normalizado para 0-100, independente do n° de núcleos
    rss: int # memória residente em bytes (o que o processo ocupa na Ram física)
    user: str
    status: str
    desc: str # descrição do executável ("" quando o arquivo não traz uma)
    exe: str  # caminho do executável ("" se protegido); a UI extrai o ícone dele
    categoria: int = SEGUNDO_PLANO # ver categorias.py
    
    
@dataclass(frozen=True)
class Snapshot:
    """
    Fotografia completa de um instante: agregado da máquina + total de linhas
    """
    cpu_total: float
    ram_used: int
    ram_total: int
    ram_percent: float
    procs: list[ProcInfo]
    portas: list[PortInfo]
    timestamp: float
    
    
class SamplerWorker(QThread):
    """
    Varre os processos em laço e emite um Snapshot pronto para desenhar
    Roda em thread própria porque a varredura completa custa 900ms nesta máquina
    (medido: 289 processos). Na thread da UI isso congelaria a janela a cada ciclo.
    """
    
    snapshot_ready = pyqtSignal(object) # emite Snapshot; 'object' porque é tipo python puro 
    def __init__(self, interval_ms: float = 1000, parent=None):
        super().__init__(parent)
        self._interval = interval_ms / 1000.0
        self._running = True
        # Cache PID -> username. Resolver o dono de um processo no Windows exige
        # consultar o SID processo a processo — era o grosso dos ~1400 ms de cada
        # varredura (medido). O dono nunca muda durante a vida do processo, então
        # basta resolver uma vez. A entrada morre junto com o PID (ver _collect).
        self._user_cache: dict[int, str] = {}
        # Estado acumulado PID -> ProcInfo. Cada ciclo lê os dados caros (memory_info,
        # cpu_percent) de apenas LOTE processos; os demais são reaproveitados daqui.
        # Sem isto, quem não fosse visitado no ciclo sumiria da tabela.
        self._estado: dict[int, ProcInfo] = {}
        # Posição da fatia na lista de PIDs, para o rodízio entre os ciclos.
        self._cursor = 0
        # Cache PID -> objeto psutil.Process. NÃO é otimização: cpu_percent() mede
        # a diferença desde a leitura anterior DO MESMO objeto. Criando um Process
        # novo a cada ciclo, toda leitura é a primeira — e a primeira devolve
        # sempre 0.0, deixando a coluna CPU% inteira zerada.
        self._proc_cache: dict[int, psutil.Process] = {}
        # Cache caminho do .exe -> descrição. É por CAMINHO, não por PID: 262
        # processos usam só 105 executáveis distintos nesta máquina (88 deles são
        # svchost.exe), então uma leitura serve para dezenas de linhas. A descrição
        # só muda se o arquivo for substituído, então vale para toda a sessão.
        # Não é podado como os outros: cresce com o número de executáveis distintos
        # já vistos, não com o de processos — algumas centenas de strings no pior
        # caso de uma sessão longa.
        self._desc_cache: dict[str, str] = {}
        
    def stop(self):
        """
        Pede a parada. Chamado pela thread da UI ao fechar a janela.
        Só levanta a flag: a thread termina o cilco atual e sai sozinha. matar uma thread no meo de uma chamada ao SO é o caminho
        mais curto para um travamento ao fechar
        """
        self._running = False
        
    def run(self) -> None:
        # --- Aquecimento ---
        # cpu_percent() mede o intervalo desde a chamada anterior. Sem esta primeira
        # passada para estabelecer o marco, cada processo apareceria com 0.0% na sua
        # primeira leitura. Esta varredura é descartada de propósito — e não pede
        # atributos ao process_iter(), então não paga o custo por processo.
        psutil.cpu_percent()
        for proc in psutil.process_iter():
            try:
                proc.cpu_percent()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass #processo morreu ou é protegido: irrelevante no aquecimento
            
        while self._running:
            ciclo_inicio = time.perf_counter()
            snap = self._collect()
            if not self._running:
                break # o usuário fechou a janela durante a coleta
            
            self.snapshot_ready.emit(snap)
            # Descontamos o tempo gasto na coleta do tempo de espera.
            
            #Intervalo real seria 900ms de coleta + 1000 ms de sono, quase 2s
            gasto = time.perf_counter() - ciclo_inicio
            # Piso de 150 ms: se a varredura estourar o intervalo, sem este piso o
            # tempo restante zera e a thread emenda uma coleta na outra, segurando o
            # GIL sem pausa — a UI trava e a rolagem fica presa (medido: coleta de
            # ~1400 ms contra intervalo de 1000 ms). O piso garante que o loop de
            # eventos do Qt sempre tenha uma janela para respirar.
            restante = max(0.15, self._interval - gasto)
            #fatiamos o sona para que stop() tenha efeito rápido, em vez do fechmanto da janela esperar o intervalo inteiro
            
            dormindo = 0.0
            while dormindo < restante and self._running:
                fatia = min(0.05, restante - dormindo)
                time.sleep(fatia)
                dormindo += fatia
    
    def _exe_e_descricao(self, proc: psutil.Process) -> tuple[str, str]:
        """
        Caminho do executável e sua descrição, via cache por caminho.

        Chamado só quando um PID entra no estado, nunca em todo ciclo. exe() custa
        ~13 ms para os ~260 processos e a leitura do arquivo ~0,5 ms por executável
        distinto — desprezível perto dos campos do rodízio, e pago uma vez só.

        O caminho também vai para a UI, que extrai o ícone dele: QIcon não pode ser
        criado nesta thread (objetos gráficos do Qt só nascem na thread da UI).
        """
        try:
            caminho = proc.exe()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            # Processos protegidos do Windows não expõem o caminho. A tabela fica
            # com o nome do .exe e sem ícone nesses casos.
            return "", ""
        if not caminho:
            return "", ""
        desc = self._desc_cache.get(caminho)
        if desc is None:
            desc = descricao_do_executavel(caminho) or ""
            self._desc_cache[caminho] = desc # "" também é cacheado: evita reler
        return caminho, desc

    def _collect(self) -> Snapshot:
        """
        Um ciclo de coleta. Executa na thread de fundo.

        Relê os campos caros (status, memory_info, cpu_percent) de apenas LOTE
        processos por vez, em rodízio; os demais vêm do estado acumulado. Ler os ~254
        de uma vez custava ~1200 ms e travava a UI (o GIL ficava preso nesta thread).
        O preço desta escolha é que esses campos são renovados a cada ~17 ciclos.
        """
        cpu_total = psutil.cpu_percent()
        vm = psutil.virtual_memory()

        # 1) Quem está vivo agora. pids() é barato — não abre handle por processo —
        #    então dá para fazer todo ciclo e manter a lista de linhas correta.
        vivos = set(psutil.pids())

        # Processos que morreram somem do estado e do cache de usuário. Sem isto o
        # dicionário cresceria sem limite e, como o Windows recicla PIDs, uma entrada
        # obsoleta atribuiria dados antigos a um processo novo.
        if len(self._estado) > len(vivos):
            self._estado = {p: i for p, i in self._estado.items() if p in vivos}
            self._user_cache = {p: u for p, u in self._user_cache.items() if p in vivos}
            self._proc_cache = {p: o for p, o in self._proc_cache.items() if p in vivos}

        # 2) Processos novos entram na tabela já neste ciclo, com os campos baratos
        #    (medido para os ~254 processos: name 7 ms, username 13 ms — contra
        #    status 1177 ms, memory_info 534 ms e cpu_percent 521 ms). Assim a lista
        #    aparece completa quase de imediato; os campos caros chegam pelo rodízio.
        for pid in [p for p in vivos if p not in self._estado]:
            try:
                proc = self._proc_cache.get(pid)
                if proc is None:
                    proc = psutil.Process(pid)
                    self._proc_cache[pid] = proc
                    # Primeira chamada estabelece o marco do cpu_percent; o valor
                    # devolvido aqui é sempre 0.0 e é descartado de propósito.
                    proc.cpu_percent()
                user = self._user_cache.get(pid)
                if user is None:
                    try:
                        user = (proc.username() or "SYSTEM").split("\\")[-1]
                    except psutil.AccessDenied:
                        user = "SYSTEM"
                    self._user_cache[pid] = user
                # cpu/rss ficam zerados e status vazio até este PID entrar no rodízio.
                caminho, desc = self._exe_e_descricao(proc)
                self._estado[pid] = ProcInfo(
                    pid=pid, name=proc.name(), cpu=0.0, rss=0, user=user,
                    status="", desc=desc, exe=caminho,
                )
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        # 3) A fatia deste ciclo, em rodízio pelos processos já conhecidos.
        conhecidos = sorted(p for p in vivos if p in self._estado)
        if self._cursor >= len(conhecidos):
            self._cursor = 0
        fatia = conhecidos[self._cursor:self._cursor + LOTE]
        self._cursor += LOTE

        # 4) Relê os dados caros só da fatia.
        ultima_pausa = time.perf_counter()
        for pid in fatia:
            # Devolve o GIL periodicamente para o loop de eventos do Qt rodar. A pausa
            # é por tempo decorrido, não a cada N processos: o custo por processo varia,
            # e contar iterações deixava blocos longos sem pausa — era onde um gesto de
            # rolagem travava. sleep(0.001), não sleep(0), porque sleep(0) devolve o GIL
            # mas esta thread costuma readquiri-lo antes de a UI fazer trabalho útil.
            if time.perf_counter() - ultima_pausa >= 0.025:
                time.sleep(0.001)
                ultima_pausa = time.perf_counter()
                if not self._running:
                    break # janela fechando: o snapshot seria descartado mesmo
            anterior = self._estado.get(pid)
            try:
                # Reaproveita o objeto: ver _proc_cache no __init__ — sem isso o
                # cpu_percent() devolve 0.0 sempre.
                proc = self._proc_cache.get(pid)
                if proc is None:
                    proc = psutil.Process(pid)
                    self._proc_cache[pid] = proc
                with proc.oneshot():   # agrupa as leituras num único acesso ao SO
                    mem = proc.memory_info()
                    # cpu_percent() sem argumento mede desde a leitura anterior DESTE
                    # processo. Com o rodízio, esse intervalo é de ~17 ciclos, então o
                    # valor é a média do processo nesse período — não o uso instantâneo.
                    self._estado[pid] = ProcInfo(
                        pid=pid,
                        name=proc.name(),
                        cpu=proc.cpu_percent() / CPU_COUNT,
                        rss=mem.rss if mem else 0,
                        # username, desc e exe já foram resolvidos quando o PID entrou
                        # no estado; são imutáveis durante a vida do processo.
                        user=anterior.user if anterior else "SYSTEM",
                        status=proc.status() or "",
                        desc=anterior.desc if anterior else "",
                        exe=anterior.exe if anterior else "",
                    )
            except psutil.NoSuchProcess:
                # Morreu entre listar e ler — rotina. Sai da tabela agora; se não
                # saísse aqui, sairia no próximo ciclo pela poda com 'vivos'.
                self._estado.pop(pid, None)
                continue
            except psutil.AccessDenied:
                # Processo protegido do Windows. A linha continua na tabela com o que
                # já se sabe dele (nome e usuário vindos da entrada barata); apenas os
                # campos protegidos seguem sem valor.
                continue

        # A categoria é recalculada para TODOS a cada ciclo, fora do rodízio: ela
        # muda quando uma janela abre ou fecha, e ficaria até ~17 s desatualizada
        # se acompanhasse os campos caros. Custa ~1 ms para a máquina inteira.
        com_janela = pids_com_janela()
        procs = [
            replace(p, categoria=classificar(p, com_janela))
            for p in self._estado.values()
        ]

        # Portas em escuta. Custa ~5 ms (lê a tabela do sistema de uma vez, sem abrir
        # handle por processo), então cabe no mesmo ciclo sem merecer rodízio. Os
        # nomes já conhecidos são reaproveitados para não reabrir os processos.
        nomes = {p.pid: p.name for p in procs}
        try:
            portas = coletar_portas(nomes)
        except psutil.AccessDenied:
            # Sem privilégio para ler a tabela de conexões: a aba de portas fica
            # vazia, mas o monitor de processos continua funcionando.
            portas = []

        return Snapshot(
            cpu_total=cpu_total,
            ram_used=vm.used,
            ram_total=vm.total,
            ram_percent=vm.percent,
            procs=procs,
            portas=portas,
            timestamp=time.time(),
        )
            