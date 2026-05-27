from hdmi_optimizer.models import DisplayInfo


try:
    from screeninfo import get_monitors
except ImportError as exc:
    ERRO_IMPORT_SCREENINFO = exc
else:
    ERRO_IMPORT_SCREENINFO = None


def obter_telas():
    if ERRO_IMPORT_SCREENINFO is not None:
        return [], (
            "Dependencia ausente: instale screeninfo para ler as telas. "
            f"Detalhe: {ERRO_IMPORT_SCREENINFO}"
        )

    telas = []
    try:
        for monitor in get_monitors():
            telas.append(
                DisplayInfo(
                    tipo="Principal/Notebook"
                    if monitor.is_primary
                    else "TV/Monitor externo",
                    largura=monitor.width,
                    altura=monitor.height,
                    principal=monitor.is_primary,
                )
            )
    except Exception as exc:
        return [], f"Nao foi possivel ler os dados das telas: {exc}"

    return telas, None
