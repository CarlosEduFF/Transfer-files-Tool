import os
import sys

# 🔧 BASE PATH (funciona no .exe e no código normal)
def get_base_path():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(__file__)


# 🔧 CONFIGURA FFmpeg (TEM QUE VIR PRIMEIRO)
def configurar_ffmpeg():
    base_path = get_base_path()

    ffmpeg_path = os.path.join(base_path, "ffmpeg", "ffmpeg.exe")

    if os.path.exists(ffmpeg_path):
        os.environ["PATH"] += os.pathsep + os.path.dirname(ffmpeg_path)
    else:
        print("⚠️ FFmpeg não encontrado:", ffmpeg_path)


configurar_ffmpeg()

# 👇 Imports depois da config
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