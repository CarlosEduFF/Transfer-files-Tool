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
MODELS_DIR = os.path.join(BASE_DIR, "data", "models")
WHISPER_MODELS_DIR = os.path.join(MODELS_DIR, "whisper")
HF_MODELS_DIR = os.path.join(MODELS_DIR, "huggingface")
HF_HUB_DIR = os.path.join(HF_MODELS_DIR, "hub")
FFMPEG_PATH = os.path.join(BASE_DIR, "ffmpeg", "ffmpeg.exe")


def garantir_pastas():
    os.makedirs(INPUT_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(WHISPER_MODELS_DIR, exist_ok=True)
    os.makedirs(HF_HUB_DIR, exist_ok=True)


# --------------------------------------------------------------------------- #
# HuggingFace Token (para diarização)
# --------------------------------------------------------------------------- #
HF_TOKEN_PATH = os.path.join(BASE_DIR, "hf_token.txt")


def carregar_hf_token() -> str | None:
    """
    Tenta carregar o token HuggingFace de:
      1. Variável de ambiente HF_TOKEN
      2. Arquivo hf_token.txt na raiz do projeto

    Returns:
        Token como string, ou None se não encontrado
    """
    # 1. Variável de ambiente
    token = os.environ.get("HF_TOKEN")
    if token:
        print("🔑 Token HuggingFace carregado (variável de ambiente)")
        return token.strip()

    # 2. Arquivo local
    if os.path.isfile(HF_TOKEN_PATH):
        with open(HF_TOKEN_PATH, "r", encoding="utf-8") as f:
            token = f.read().strip()
        if token:
            print("🔑 Token HuggingFace carregado (hf_token.txt)")
            return token

    return None
