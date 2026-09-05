"""
Classificação dos processos em aplicativos, segundo plano e sistema.

É a mesma divisão que o Gerenciador de Tarefas mostra, e ela responde a uma
pergunta prática: dos ~270 processos da máquina, quais são programas que você
abriu e pode fechar, e quais são infraestrutura do Windows em que não se mexe.

Dois sinais bastam:

1. Ter janela visível — separa "aplicativo" de "serviço". É o critério do próprio
   Windows, obtido via EnumWindows (medido: 1,2 ms para varrer tudo).
2. O dono do processo — separa o que é seu do que é do sistema (SYSTEM, LOCAL
   SERVICE, NETWORK SERVICE).
"""
from __future__ import annotations

import ctypes
from ctypes import wintypes

APLICATIVO = 0
SEGUNDO_PLANO = 1
SISTEMA = 2

NOMES = {
    APLICATIVO: "Aplicativos",
    SEGUNDO_PLANO: "Processos em segundo plano",
    SISTEMA: "Processos do Windows",
}

# Contas de serviço do Windows. O nome chega do sampler já sem o domínio
# (ver ProcInfo.user), então a comparação é com o nome puro.
CONTAS_SISTEMA = {
    "system", "local service", "network service", "serviço local",
    "serviço de rede", "sistema",
}

_user32 = ctypes.windll.user32
_CALLBACK = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
_user32.EnumWindows.argtypes = [_CALLBACK, wintypes.LPARAM]


def pids_com_janela() -> set[int]:
    """
    PIDs que têm pelo menos uma janela visível e com título.

    O filtro por título não é decorativo: muitos processos criam janelas
    invisíveis de uso interno (mensagens, tray, contexto gráfico), e sem ele
    metade dos serviços apareceria como aplicativo.
    """
    pids: set[int] = set()

    def visitar(hwnd, _lparam):
        if _user32.IsWindowVisible(hwnd) and _user32.GetWindowTextLengthW(hwnd) > 0:
            pid = wintypes.DWORD()
            _user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            if pid.value:
                pids.add(pid.value)
        return True # continua a enumeração

    try:
        _user32.EnumWindows(_CALLBACK(visitar), 0)
    except OSError:
        # Sem a enumeração, tudo cai em segundo plano/sistema — a tabela continua
        # correta, só perde a separação dos aplicativos.
        return set()
    return pids


def classificar(proc, com_janela: set[int]) -> int:
    """Categoria de um ProcInfo."""
    if proc.pid in com_janela:
        return APLICATIVO
    if proc.user.lower() in CONTAS_SISTEMA or proc.pid in (0, 4):
        return SISTEMA
    return SEGUNDO_PLANO
