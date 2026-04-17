import os
from src.config import INPUT_DIR
import torch 
EXTENSOES = (".mp3", ".wav", ".m4a", ".mp4")


def escolher_audio(pasta):
    arquivos = [
        f for f in os.listdir(pasta)
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

import torch

def resolver_device(opcao: str) -> str:
    opcao = opcao.lower()

    if opcao == "cpu":
        print("🖥️ Usando CPU")
        return "cpu"

    if opcao == "gpu":
        if torch.cuda.is_available():
            print("🚀 Usando GPU (CUDA)")
            return "cuda"
        else:
            print("⚠️ GPU não disponível, usando CPU")
            return "cpu"

    # auto
    if torch.cuda.is_available():
        print("🤖 AUTO: GPU detectada (CUDA)")
        return "cuda"
    else:
        print("🤖 AUTO: usando CPU")
        return "cpu"