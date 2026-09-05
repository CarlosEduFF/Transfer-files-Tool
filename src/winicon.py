"""
Aplica o ícone da janela no nível do Win32.

O Qt define o ícone da JANELA (WM_SETICON), mas não o da CLASSE da janela
(GCLP_HICON). Para uma QMainWindow, a barra de tarefas do Windows usa o ícone da
classe — que fica com o padrão do sistema e aparece genérico, mesmo com o
setWindowIcon correto e o AppUserModelID registrado.

Foi assim que o problema se manifestou: a barra de título mostrava o ícone certo
(desenhada pelo Qt) e a barra de tarefas mostrava o genérico (lida do Windows).
Um QLabel não reproduzia o defeito; uma QMainWindow sim.
"""
from __future__ import annotations

import ctypes
from ctypes import wintypes
from pathlib import Path

WM_SETICON = 0x0080
ICON_SMALL, ICON_BIG = 0, 1
GCLP_HICON, GCLP_HICONSM = -14, -34
IMAGE_ICON = 1
LR_LOADFROMFILE = 0x0010


def aplicar_icone_win32(hwnd: int, caminho_ico: Path) -> bool:
    """
    Grava o ícone na janela e na classe dela. Devolve True se conseguiu.

    Precisa de um arquivo .ico de verdade (LoadImageW não lê PNG) e da janela já
    criada — chame depois de show(), quando o handle existe.
    """
    if not caminho_ico.exists():
        return False

    try:
        user32 = ctypes.windll.user32
        user32.LoadImageW.restype = wintypes.HANDLE
        user32.SendMessageW.restype = ctypes.c_void_p
        user32.SetClassLongPtrW.restype = ctypes.c_void_p

        caminho = str(caminho_ico)
        # Os dois tamanhos que o shell pede: 16 px para a barra de título e listas,
        # 32 px para a barra de tarefas e o Alt+Tab.
        h_grande = user32.LoadImageW(None, caminho, IMAGE_ICON, 32, 32, LR_LOADFROMFILE)
        h_pequeno = user32.LoadImageW(None, caminho, IMAGE_ICON, 16, 16, LR_LOADFROMFILE)
        if not h_grande or not h_pequeno:
            return False

        user32.SendMessageW(hwnd, WM_SETICON, ICON_BIG, h_grande)
        user32.SendMessageW(hwnd, WM_SETICON, ICON_SMALL, h_pequeno)
        # A parte que o Qt não faz, e que resolve a barra de tarefas:
        user32.SetClassLongPtrW(hwnd, GCLP_HICON, h_grande)
        user32.SetClassLongPtrW(hwnd, GCLP_HICONSM, h_pequeno)
        return True
    except (AttributeError, OSError):
        # Outro sistema operacional ou API indisponível: o app abre igual, apenas
        # com o ícone genérico na barra de tarefas.
        return False
