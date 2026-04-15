import whisper
import os
import sys


class Transcriber:
    def __init__(self, modelo: str, device: str):
        print(f"⏳ Carregando modelo: {modelo} ({device})")

        # 🔧 Resolve caminho base (normal ou .exe)
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(__file__)

        # 🔥 Caminho completo do modelo
        model_path = os.path.join(base_path, "..", "model", f"{modelo}.pt")
        model_path = os.path.abspath(model_path)

        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Modelo não encontrado: {model_path}")

        # 🚀 Carrega modelo local (SEM internet)
        self.model = whisper.load_model(model_path, device=device)

    def transcrever(self, caminho_audio: str, idioma=None):
        opcoes = {"language": idioma} if idioma else {}
        return self.model.transcribe(caminho_audio, **opcoes)