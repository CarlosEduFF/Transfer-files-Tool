import os
import shutil
from helpers.install import mover_pasta_sem_mesclar, nome_seguro

def mover_itens(origem_dir, destino_dir, ignorar=None):
    """
    Move todos os itens de uma pasta para outra.
    Usa lista estática para evitar pular arquivos durante a movimentação.
    """
    if not os.path.exists(origem_dir):
        return

    os.makedirs(destino_dir, exist_ok=True)
    ignorar = set(ignorar or [])

    itens = list(os.listdir(origem_dir))

    for item in itens:
        if item in ignorar:
            continue

        origem = os.path.join(origem_dir, item)
        if not os.path.exists(origem):
            continue

        destino = os.path.join(destino_dir, item)
        destino = nome_seguro(destino)

        print(f"Movendo {item} -> {destino_dir}")
        shutil.move(origem, destino)


def mover_content_instalado_de_smart_tv_para_raiz(SMART_TV, ROOT):
    """
    No modo reverter, traz de volta para a raiz apenas o Content
    que foi instalado dentro de Smart TV.

    Regra:
    - Se existir Content_1, Content_2, etc., esses são tratados como os
      Content instalados e voltam para a raiz.
    - Se não existirem sufixados e houver apenas Smart TV/Content,
      esse Content é o que volta para a raiz.
    """
    if not os.path.exists(SMART_TV):
        return

    itens = list(os.listdir(SMART_TV))

    # Primeiro tenta mover os Content com sufixo, que normalmente são os
    # Content vindos da raiz quando já existia outro Content na Smart TV.
    sufixados = [
        item for item in itens
        if item.startswith("Content_") and os.path.isdir(os.path.join(SMART_TV, item))
    ]

    if sufixados:
        for item in sufixados:
            origem = os.path.join(SMART_TV, item)
            mover_pasta_sem_mesclar(origem, ROOT)
        return

    # Se não houver Content_1, Content_2, etc., move o Content padrão.
    caminho_content = os.path.join(SMART_TV, "Content")
    if os.path.isdir(caminho_content):
        mover_pasta_sem_mesclar(caminho_content, ROOT)

