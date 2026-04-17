import os
import sys


def get_base_path():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

def configurar_ffmpeg():
    base_path = get_base_path()
    ffmpeg_path = os.path.join(base_path, "ffmpeg", "ffmpeg.exe")

    if os.path.isfile(ffmpeg_path):
        ffmpeg_dir = os.path.dirname(ffmpeg_path)

        # Evita duplicar PATH
        if ffmpeg_dir not in os.environ.get("PATH", ""):
            os.environ["PATH"] = ffmpeg_dir + os.pathsep + os.environ.get("PATH", "")

        print(f"✅ FFmpeg carregado: {ffmpeg_path}")
        return True
    else:
        print(f"❌ FFmpeg não encontrado: {ffmpeg_path}")
        return False



BASE_DIR = get_base_path()

INPUT_DIR = os.path.join(BASE_DIR, "data", "input")
OUTPUT_DIR = os.path.join(BASE_DIR, "data", "output")
FFMPEG_PATH = os.path.join(BASE_DIR, "ffmpeg", "ffmpeg.exe")


def garantir_pastas():
    os.makedirs(INPUT_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)