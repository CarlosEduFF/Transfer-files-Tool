MODELOS = ["tiny", "base", "small", "medium", "large"]
IDIOMAS = ["auto", "portuguese", "english", "spanish"]
FORMATOS = ["txt", "srt", "json"]
DISPOSITIVOS = ["auto", "cpu", "gpu"]
DIARIZACAO = ["Não", "Sim"]
MODO_PROCESSAMENTO = ["Único", "Fila (sequencial)", "Paralelo (simultâneo)"]


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
    modo = escolher_opcao(MODO_PROCESSAMENTO, "Modo de processamento")
    modelo = escolher_opcao(MODELOS, "Escolha o modelo")
    idioma = escolher_opcao(IDIOMAS, "Escolha o idioma")
    formato = escolher_opcao(FORMATOS, "Formato de saída")
    device = escolher_opcao(DISPOSITIVOS, "Dispositivo (CPU/GPU)")
    diarizar = escolher_opcao(DIARIZACAO, "Separar falantes? (requer token HuggingFace)")

    if idioma == "auto":
        idioma = None

    # Mapeia modo para valor simples
    if "Fila" in modo:
        modo_valor = "fila"
    elif "Paralelo" in modo:
        modo_valor = "paralelo"
    else:
        modo_valor = "unico"

    return {
        "modo": modo_valor,
        "modelo": modelo,
        "idioma": idioma,
        "formato": formato,
        "device": device,       # 👈 ESSENCIAL
        "diarizar": diarizar == "Sim"  # 👈 True/False
    }