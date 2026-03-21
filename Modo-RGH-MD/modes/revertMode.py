from helpers.revert import mover_content_instalado_de_smart_tv_para_raiz, mover_itens
def modo_reverter(CRACK, SMART_TV,  ROOT):
    print("Revertendo alterações...")

    IGNORAR = [
        "Crack",
        "Smart TV",
        "transfer_files.py",
        "transfer_files.exe",
        "README.md",
        ".gitignore",
        "build",
        "dist",
        "transfer_files.spec",
        "System Volume Information",
        "$RECYCLE.BIN",
        "main.exe",
    ]

    # 1) primeiro move tudo da raiz para Crack
    mover_itens(ROOT, CRACK, ignorar=IGNORAR)

    # 2) depois traz de volta o Content instalado dentro de Smart TV para a raiz
    mover_content_instalado_de_smart_tv_para_raiz(SMART_TV, ROOT)

    print("Reversão concluída")
