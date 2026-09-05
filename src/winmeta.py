"""
Leitura da descrição de um executável (o campo FileDescription do Windows).

É o texto que o Gerenciador de Tarefas mostra no lugar do nome do arquivo:
'spoolsv.exe' vira 'Aplicativo de subsistema de spooler'. Sem ele, boa parte da
tabela fica ilegível — nomes como 'WmiPrvSE.exe' ou 'ipf_uf.exe' não dizem nada.

Usa a API version.dll via ctypes em vez de uma dependência nova: são três
chamadas, e o projeto já é específico para Windows por causa do psutil.
"""
from __future__ import annotations

import ctypes
from ctypes import wintypes

# use_last_error para que uma falha aqui não se confunda com erro de outra API.
_version = ctypes.WinDLL("version", use_last_error=True)

_version.GetFileVersionInfoSizeW.argtypes = [wintypes.LPCWSTR, wintypes.LPDWORD]
_version.GetFileVersionInfoSizeW.restype = wintypes.DWORD
_version.GetFileVersionInfoW.argtypes = [
    wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, wintypes.LPVOID
]
_version.GetFileVersionInfoW.restype = wintypes.BOOL
_version.VerQueryValueW.argtypes = [
    wintypes.LPCVOID, wintypes.LPCWSTR,
    ctypes.POINTER(wintypes.LPVOID), ctypes.POINTER(wintypes.UINT),
]
_version.VerQueryValueW.restype = wintypes.BOOL


def descricao_do_executavel(caminho: str) -> str | None:
    """
    Devolve o FileDescription do executável, ou None se não houver.

    None é resultado normal, não erro: executáveis sem bloco de versão (parte dos
    utilitários do próprio Windows) simplesmente não têm esse campo — dos 105
    executáveis desta máquina, 96 têm e 9 não.

    Custa ~16 ms por arquivo, então quem chama deve cachear por caminho. O
    resultado é imutável enquanto o arquivo não for substituído.
    """
    if not caminho:
        return None
    try:
        tamanho = _version.GetFileVersionInfoSizeW(caminho, None)
        if not tamanho:
            return None # sem bloco de versão

        buffer = ctypes.create_string_buffer(tamanho)
        if not _version.GetFileVersionInfoW(caminho, 0, tamanho, buffer):
            return None

        ponteiro = wintypes.LPVOID()
        bytes_lidos = wintypes.UINT()

        # O bloco de versão é traduzido por idioma. Precisamos descobrir qual
        # tradução o arquivo traz antes de pedir o texto: pedir um idioma fixo
        # (o inglês, por exemplo) devolveria None na maioria dos executáveis
        # de um Windows em português.
        if not _version.VerQueryValueW(
            buffer, "\\VarFileInfo\\Translation",
            ctypes.byref(ponteiro), ctypes.byref(bytes_lidos)
        ):
            return None

        idiomas = ctypes.cast(ponteiro, ctypes.POINTER(wintypes.WORD))
        idioma, codepage = idiomas[0], idiomas[1]

        if not _version.VerQueryValueW(
            buffer, f"\\StringFileInfo\\{idioma:04x}{codepage:04x}\\FileDescription",
            ctypes.byref(ponteiro), ctypes.byref(bytes_lidos)
        ):
            return None

        # bytes_lidos conta caracteres, e o valor vem com o terminador incluso.
        texto = ctypes.wstring_at(ponteiro.value, bytes_lidos.value).strip("\x00 ")
        return texto or None
    except OSError:
        # Arquivo removido, caminho inacessível ou executável corrompido. Nada a
        # fazer: a tabela mostra o nome do .exe, que é o comportamento anterior.
        return None
