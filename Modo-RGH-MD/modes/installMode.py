import os
import shutil
from helpers.install import mover_pasta_sem_mesclar, nome_seguro

def modo_instalar(CRACK, SMART_TV, CONTENT, ROOT ):
    print("Executando instalação...")

    # 1️⃣ GARANTIR que Content da raiz foi movido
    if os.path.exists(CONTENT):
        print("Movendo Content da raiz -> Smart TV")
        mover_pasta_sem_mesclar(CONTENT, SMART_TV)

    # 🔒 Verificação crítica (evita bug que você teve)
    if os.path.exists(CONTENT):
        raise Exception("ERRO: Content ainda está na raiz após tentativa de mover")

    # 2️⃣ mover tudo de Crack → raiz
    if not os.path.exists(CRACK):
        return

    itens = list(os.listdir(CRACK))

    for item in itens:
        origem = os.path.join(CRACK, item)

        # 🔥 tratamento especial para Content do Crack
        if item == "Content":
            destino = os.path.join(ROOT, "Content")

            # se já existir, renomeia explicitamente
            destino = nome_seguro(destino)

        else:
            destino = os.path.join(ROOT, item)
            destino = nome_seguro(destino)

        print(f"Movendo {item} -> ROOT")
        shutil.move(origem, destino)
