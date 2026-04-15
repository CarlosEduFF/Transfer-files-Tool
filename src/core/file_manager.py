import os
import json


def salvar_saida(resultado, caminho_audio, formato="txt", output_dir=None):
    if output_dir is None:
        raise ValueError("output_dir precisa ser informado")

    base = os.path.splitext(os.path.basename(caminho_audio))[0]

    # 🔧 Garante que a pasta existe
    os.makedirs(output_dir, exist_ok=True)

    if formato == "txt":
        path = os.path.join(output_dir, f"{base}.txt")
        with open(path, "w", encoding="utf-8") as f:
            f.write(resultado["text"])

    elif formato == "json":
        path = os.path.join(output_dir, f"{base}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(resultado, f, ensure_ascii=False, indent=2)

    elif formato == "srt":
        path = os.path.join(output_dir, f"{base}.srt")
        with open(path, "w", encoding="utf-8") as f:
            for i, seg in enumerate(resultado["segments"], 1):
                f.write(f"{i}\n")
                f.write(f"{seg['start']} --> {seg['end']}\n")
                f.write(f"{seg['text']}\n\n")

    else:
        raise ValueError(f"Formato inválido: {formato}")

    return path