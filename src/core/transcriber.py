import whisper
import os
import sys


def get_base_path():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


class Transcriber:
    def __init__(self, modelo: str, device: str):
        print(f"⏳ Carregando modelo: {modelo} ({device})")

        base_path = get_base_path()

        # 📁 Pasta de modelos ao lado do .exe
        model_dir = os.path.join(base_path, "model")
        os.makedirs(model_dir, exist_ok=True)

        model_path = os.path.join(model_dir, f"{modelo}.pt")

        # 🔥 Estratégia híbrida
        if os.path.isfile(model_path):
            print(f"📦 Usando modelo local: {model_path}")
            self.model = whisper.load_model(model_path, device=device)
        else:
            print("🌐 Modelo não encontrado localmente. Baixando...")
            self.model = whisper.load_model(
                modelo,
                device=device,
                download_root=model_dir
            )
            print(f"✅ Modelo baixado em: {model_dir}")

    def transcrever(self, caminho_audio: str, idioma=None):
        opcoes = {"language": idioma} if idioma else {}
        return self.model.transcribe(caminho_audio, **opcoes)