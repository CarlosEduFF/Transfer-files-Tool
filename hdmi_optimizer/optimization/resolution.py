from hdmi_optimizer.config import (
    ALTURA_OTIMIZADA,
    FREQUENCIA_OTIMIZADA,
    LARGURA_OTIMIZADA,
)


def forcar_resolucao(
    largura=LARGURA_OTIMIZADA,
    altura=ALTURA_OTIMIZADA,
    frequencia=FREQUENCIA_OTIMIZADA,
):
    """
    Altera a resolucao da tela ativa usando a API Win32.
    Depois do modo "Apenas segunda tela", a tela ativa tende a ser a TV.
    """
    try:
        import win32api
        import win32con
    except ImportError as exc:
        print("[ERRO] Dependencia ausente: instale pywin32 para alterar a resolucao.")
        print(f"Detalhe: {exc}")
        return False

    print(f"[+] Configurando resolucao para {largura}x{altura} ({frequencia}Hz)...")

    try:
        devmode = win32api.EnumDisplaySettings(None, win32con.ENUM_CURRENT_SETTINGS)
        devmode.PelsWidth = largura
        devmode.PelsHeight = altura
        devmode.DisplayFrequency = frequencia
        devmode.Fields = (
            win32con.DM_PELSWIDTH
            | win32con.DM_PELSHEIGHT
            | win32con.DM_DISPLAYFREQUENCY
        )

        resultado = win32api.ChangeDisplaySettings(devmode, 0)
    except Exception as exc:
        print(f"[ERRO] Falha ao chamar a API Win32: {exc}")
        return False

    if resultado == win32con.DISP_CHANGE_SUCCESSFUL:
        print(f"[SUCESSO] Tela configurada para {largura}x{altura} @ {frequencia}Hz.")
        return True

    print(f"[ERRO] Falha ao alterar resolucao. Codigo de erro: {resultado}")
    return False


def forcar_resolucao_1080p():
    return forcar_resolucao(
        LARGURA_OTIMIZADA,
        ALTURA_OTIMIZADA,
        FREQUENCIA_OTIMIZADA,
    )
