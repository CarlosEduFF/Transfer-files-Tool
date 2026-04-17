import os
import sys

from src.config import get_base_path, configurar_ffmpeg

# 🔥 EXECUTA PRIMEIRO
configurar_ffmpeg()

# 👇 Só depois disso vêm os outros imports
from menu import menu_configuracao
from utils import escolher_audio, resolver_device
from core.transcriber import Transcriber
from core.file_manager import salvar_saida

def main():
    base_path = get_base_path()

    # 📁 Estrutura padrão
    input_dir = os.path.join(base_path, "data", "input")
    output_dir = os.path.join(base_path, "data", "output")

    # 🔧 Garante que as pastas existem
    os.makedirs(input_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)

    # 🎧 Escolher áudio da pasta correta
    audio = escolher_audio(input_dir)

    config = menu_configuracao()

    device = resolver_device(config["device"])

    transcriber = Transcriber(
        config["modelo"],
        device
    )

    resultado = transcriber.transcrever(audio, config["idioma"])

    # 💾 Salva na pasta output correta
    saida = salvar_saida(resultado, audio, config["formato"], output_dir)

    print(f"\n✅ Arquivo gerado: {saida}")


if __name__ == "__main__":
    main()