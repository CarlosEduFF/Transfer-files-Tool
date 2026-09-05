"""
Coleta das portas em escuta (LISTEN) e de quem as ocupa.

Responde à pergunta prática "quem está usando a porta 8080?", que aparece toda vez
que um servidor local não sobe por conflito de porta.

Diferente da varredura de processos, esta coleta é barata: psutil.net_connections
custa ~3 ms para as ~170 conexões da máquina (medido), porque lê a tabela de
conexões do sistema de uma vez, sem abrir um handle por processo.
"""
from __future__ import annotations

import socket
from dataclasses import dataclass

import psutil

# Serviços conhecidos que valem uma etiqueta: o número da porta sozinho não diz
# muito para quem está diagnosticando.
BEM_CONHECIDAS = {
    20: "FTP (dados)", 21: "FTP", 22: "SSH", 23: "Telnet", 25: "SMTP",
    53: "DNS", 67: "DHCP", 80: "HTTP", 110: "POP3", 135: "RPC (Windows)",
    137: "NetBIOS", 139: "NetBIOS", 143: "IMAP", 443: "HTTPS",
    445: "SMB (compartilhamento)", 587: "SMTP (envio)", 993: "IMAPS",
    1433: "SQL Server", 1521: "Oracle", 3000: "Dev (Node/React)",
    3306: "MySQL", 3389: "Área de Trabalho Remota", 5000: "Dev (Flask)",
    5173: "Dev (Vite)", 5432: "PostgreSQL", 5900: "VNC", 6379: "Redis",
    8000: "Dev (HTTP alternativo)", 8080: "HTTP alternativo",
    8443: "HTTPS alternativo", 9000: "Dev (PHP-FPM/SonarQube)",
    9200: "Elasticsearch", 27017: "MongoDB",
}


@dataclass(frozen=True)
class PortInfo:
    """
    Uma linha da tabela de portas. Imutável, como ProcInfo: é criada na thread de
    coleta e lida na thread da UI.
    """
    porta: int
    protocolo: str   # TCP ou UDP
    endereco: str    # em qual interface escuta
    pid: int         # 0 quando o sistema não revela o dono
    processo: str    # nome do executável, ou "" se desconhecido
    servico: str     # etiqueta de serviço conhecido, ou ""


def _rotulo_endereco(ip: str) -> str:
    """
    Traduz o endereço de escuta para algo legível.

    '0.0.0.0' e '::' significam "todas as interfaces" — é a diferença entre um
    serviço exposto na rede e um que só aceita conexões locais, e vale deixar
    isso explícito em vez de mostrar o IP cru.
    """
    if ip in ("0.0.0.0", "::"):
        return "todas as interfaces"
    if ip in ("127.0.0.1", "::1"):
        return "somente local"
    return ip


def coletar_portas(nomes_por_pid: dict[int, str] | None = None) -> list[PortInfo]:
    """
    Portas em escuta, uma linha por porta.

    `nomes_por_pid` permite reaproveitar os nomes que o sampler de processos já
    conhece, evitando abrir os processos de novo só para descobrir o nome. Quem
    não estiver no dicionário é resolvido aqui (são poucos).
    """
    nomes = dict(nomes_por_pid or {})
    portas: list[PortInfo] = []
    vistos: set[tuple[int, str, int]] = set()
    enderecos: dict[tuple[int, str, int], set[str]] = {}

    for conexao in psutil.net_connections(kind="inet"):
        # UDP não tem estado de conexão: no psutil, um socket UDP aberto vem com
        # status NONE. Ele é tão "ocupante da porta" quanto um TCP em LISTEN, então
        # entra na lista também.
        eh_tcp = conexao.type == socket.SOCK_STREAM
        if eh_tcp and conexao.status != psutil.CONN_LISTEN:
            continue
        if not conexao.laddr:
            continue

        pid = conexao.pid or 0
        nome = nomes.get(pid, "")
        if pid and not nome:
            try:
                nome = psutil.Process(pid).name()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                nome = ""
            nomes[pid] = nome

        protocolo = "TCP" if eh_tcp else "UDP"

        # Uma linha por porta+protocolo+processo, não por interface. O mesmo socket
        # costuma aparecer várias vezes (IPv4 e IPv6, e uma entrada por placa de
        # rede): são linhas repetidas com a mesma informação útil — quem ocupa a
        # porta. Os endereços viram um resumo em vez de linhas separadas.
        chave = (conexao.laddr.port, protocolo, pid)
        if chave in vistos:
            enderecos[chave].add(_rotulo_endereco(conexao.laddr.ip))
            continue
        vistos.add(chave)
        enderecos[chave] = {_rotulo_endereco(conexao.laddr.ip)}

        portas.append(PortInfo(
            porta=conexao.laddr.port,
            protocolo=protocolo,
            endereco="",   # preenchido abaixo, quando todos os endereços forem vistos
            pid=pid,
            processo=nome or ("Sistema" if pid in (0, 4) else "—"),
            servico=BEM_CONHECIDAS.get(conexao.laddr.port, ""),
        ))

    # Agora que cada porta tem o conjunto completo de endereços, monta o resumo.
    # "todas as interfaces" absorve o resto: se o socket escuta em 0.0.0.0, dizer
    # que também escuta em 192.168.x.y é redundante.
    resultado = []
    for p in portas:
        conjunto = enderecos[(p.porta, p.protocolo, p.pid)]
        if "todas as interfaces" in conjunto:
            rotulo = "todas as interfaces"
        elif conjunto == {"somente local"}:
            rotulo = "somente local"
        elif len(conjunto) == 1:
            rotulo = next(iter(conjunto))
        else:
            especificos = sorted(c for c in conjunto if c != "somente local")
            rotulo = especificos[0]
            if len(conjunto) > 1:
                rotulo += f" (+{len(conjunto) - 1})"
        resultado.append(PortInfo(
            porta=p.porta, protocolo=p.protocolo, endereco=rotulo,
            pid=p.pid, processo=p.processo, servico=p.servico,
        ))

    resultado.sort(key=lambda p: (p.porta, p.protocolo))
    return resultado
