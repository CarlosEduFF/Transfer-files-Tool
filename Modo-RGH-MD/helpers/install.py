
import os
import shutil


def mover_pasta_sem_mesclar(origem, destino_base):
    """
    Move uma pasta inteira para dentro de um diretório destino.
    Se já existir uma pasta com o mesmo nome, renomeia para não misturar.
    Ex.: Content -> Content_1
    """
    if not os.path.exists(origem):
        return

    os.makedirs(destino_base, exist_ok=True)

    nome_pasta = os.path.basename(origem)
    destino = os.path.join(destino_base, nome_pasta)
    destino = nome_seguro(destino)

    shutil.move(origem, destino)
def nome_seguro(destino):
    """
    Gera um nome novo caso já exista algo com o mesmo nome.
    Isso evita sobrescrever arquivos ou pastas.
    """
    if not os.path.exists(destino):
        return destino

    base, ext = os.path.splitext(destino)
    contador = 1

    while True:
        novo = f"{base}_{contador}{ext}"
        if not os.path.exists(novo):
            return novo
        contador += 1
