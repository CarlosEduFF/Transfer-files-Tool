import os
import shutil

# Pega o diretório onde o script está sendo executado.
# Como a ideia é rodar no pendrive, isso vira automaticamente a raiz do pen drive.
ROOT = os.getcwd()

# Definindo os caminhos das pastas que vamos usar
CRACK = os.path.join(ROOT, "Crack")
SMART_TV = os.path.join(ROOT, "Smart TV")
CONTENT = os.path.join(ROOT, "Content")


def modo_instalar():
    """
    Este modo simula a 'instalação'.

    Ele faz duas coisas:
    1) Move a pasta Content para dentro da pasta Smart TV
    2) Move os arquivos que estão dentro da pasta Crack para a raiz do pendrive
    """

    # caminho final da pasta Content
    destino_content = os.path.join(SMART_TV, "Content")

    # se a pasta Content existir na raiz, move ela
    if os.path.exists(CONTENT):
        shutil.move(CONTENT, destino_content)

    # percorre tudo que está dentro da pasta Crack
    for arquivo in os.listdir(CRACK):

        origem = os.path.join(CRACK, arquivo)
        destino = os.path.join(ROOT, arquivo)

        # move apenas arquivos (ignora pastas)
        if os.path.isfile(origem):
            shutil.move(origem, destino)


def modo_reverter():

    content_na_tv = os.path.join(SMART_TV, "Content")

    if os.path.exists(content_na_tv):
        shutil.move(content_na_tv, ROOT)

    IGNORAR = ["Crack", "Smart TV", "Content", "transfer_files.py", "transfer_files.exe"]

    for item in os.listdir(ROOT):

        if item in IGNORAR:
            continue

        origem = os.path.join(ROOT, item)
        destino = os.path.join(CRACK, item)

        shutil.move(origem, destino)

def main():

    # verifica se Content está dentro da pasta Smart TV
    content_dentro_tv = os.path.exists(
        os.path.join(SMART_TV, "Content")
    )

    # se estiver, significa que já foi executado antes
    if content_dentro_tv:
        print("Revertendo alterações...")
        modo_reverter()

    else:
        print("Executando instalação...")
        modo_instalar()


if __name__ == "__main__":
    main()