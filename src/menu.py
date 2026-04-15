MODELOS = ["tiny", "base", "small", "medium", "large"]
IDIOMAS = ["auto", "portuguese", "english", "spanish"]
FORMATOS = ["txt", "srt", "json"]
DISPOSITIVOS = ["auto", "cpu", "gpu"]


def escolher_opcao(lista, titulo):
    print(f"\n📌 {titulo}")
    for i, item in enumerate(lista, 1):
        print(f"[{i}] {item}")

    while True:
        try:
            escolha = int(input("Escolha: "))
            if 1 <= escolha <= len(lista):
                return lista[escolha - 1]
        except:
            pass
        print("❌ Opção inválida")


def menu_configuracao():
    modelo = escolher_opcao(MODELOS, "Escolha o modelo")
    idioma = escolher_opcao(IDIOMAS, "Escolha o idioma")
    formato = escolher_opcao(FORMATOS, "Formato de saída")
    device = escolher_opcao(DISPOSITIVOS, "Dispositivo (CPU/GPU)")

    if idioma == "auto":
        idioma = None

    return {
        "modelo": modelo,
        "idioma": idioma,
        "formato": formato,
        "device": device   # 👈 ESSENCIAL
    }