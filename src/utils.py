import os
from src.config import INPUT_DIR
import torch 
EXTENSOES = (".mp3", ".wav", ".m4a", ".mp4")


def escolher_audio():
    arquivos = [
        f for f in os.listdir(INPUT_DIR)
        if f.lower().endswith(EXTENSOES)
    ]

    if not arquivos:
        print("❌ Nenhum áudio encontrado em /data/input")
        return None

    print("\n🎵 Áudios disponíveis:")
    for i, nome in enumerate(arquivos, 1):
        print(f"[{i}] {nome}")

    escolha = int(input("Escolha: "))
    return os.path.join(INPUT_DIR, arquivos[escolha - 1])


def resolver_device(opcao: str) -> str:
    if opcao == "cpu":
        return "cpu"

    if opcao == "gpu":
        if not torch.cuda.is_available():
            raise RuntimeError("❌ GPU não disponível (CUDA não detectado)")
        return "cuda"

    # auto
    return "cuda" if torch.cuda.is_available() else "cpu"