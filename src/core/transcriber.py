import os
import shutil
import sys

import whisper


def get_base_path():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Transcriber:
    def __init__(self, modelo: str, device: str):
        print(f"Carregando modelo: {modelo} ({device})")

        model_dir = self._model_dir()
        os.makedirs(model_dir, exist_ok=True)

        model_path = os.path.join(model_dir, f"{modelo}.pt")
        self._copiar_modelo_existente(modelo, model_path)

        if os.path.isfile(model_path):
            print(f"Usando modelo local: {model_path}")
            self.model = whisper.load_model(model_path, device=device)
        else:
            print("Modelo nao encontrado localmente. Baixando...")
            self.model = whisper.load_model(
                modelo,
                device=device,
                download_root=model_dir,
            )
            print(f"Modelo baixado em: {model_dir}")

    def transcrever(self, caminho_audio: str, idioma=None):
        opcoes = {"language": idioma} if idioma else {}
        return self.model.transcribe(caminho_audio, **opcoes)

    @staticmethod
    def _model_dir() -> str:
        base_path = get_base_path()
        return os.path.join(base_path, "data", "models", "whisper")

    @staticmethod
    def _copiar_modelo_existente(modelo: str, model_path: str) -> None:
        if os.path.isfile(model_path):
            return

        base_path = get_base_path()
        candidatos = [
            os.path.join(base_path, "core", "model", f"{modelo}.pt"),
            os.path.join(base_path, "model", f"{modelo}.pt"),
            os.path.join(os.path.expanduser("~"), ".cache", "whisper", f"{modelo}.pt"),
        ]

        for origem in candidatos:
            if os.path.isfile(origem):
                print(f"Copiando modelo Whisper para data/models: {origem}")
                os.makedirs(os.path.dirname(model_path), exist_ok=True)
                shutil.copy2(origem, model_path)
                return
