import subprocess
import time

from hdmi_optimizer.config import AGUARDAR_PROJECAO_SEGUNDOS


def definir_modo_projecao_apenas_tv(
    aguardar_segundos=AGUARDAR_PROJECAO_SEGUNDOS,
):
    """
    Usa o utilitario nativo do Windows para mudar a projecao para
    "Apenas segunda tela", equivalente ao atalho Win+P > Segunda tela somente.
    """
    print("[+] Alterando projecao para: Apenas segunda tela...")

    try:
        resultado = subprocess.run(["displayswitch.exe", "/external"], check=False)
    except FileNotFoundError:
        print("[ERRO] displayswitch.exe nao foi encontrado neste sistema.")
        return False

    time.sleep(aguardar_segundos)

    if resultado.returncode != 0:
        print(f"[AVISO] displayswitch.exe retornou codigo {resultado.returncode}.")

    return resultado.returncode == 0
