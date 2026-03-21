import os
import shutil
import sys
from modes.installMode import modo_instalar
from modes.revertMode import modo_reverter
# Define ROOT corretamente
if getattr(sys, 'frozen', False):
    ROOT = os.getcwd()
else:
    ROOT = os.path.dirname(os.path.abspath(__file__))

CRACK = os.path.join(ROOT, "Crack")
SMART_TV = os.path.join(ROOT, "Smart TV")
CONTENT = os.path.join(ROOT, "Content")


def crack_esta_vazio():
    if not os.path.exists(CRACK):
        return False

    itens = os.listdir(CRACK)

    # ignora lixo comum
    ignorar = {
        "System Volume Information",
        "$RECYCLE.BIN"
    }

    itens_validos = [i for i in itens if i not in ignorar]

    return len(itens_validos) == 0

def main():

    if crack_esta_vazio():
        print("Modo reversão detectado")
        modo_reverter(CRACK, SMART_TV, ROOT)
    else:
        print("Modo instalação detectado")
        modo_instalar(CRACK, SMART_TV, CONTENT, ROOT)


if __name__ == "__main__":
    main()