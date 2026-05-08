import os
import json


def _formatar_tempo_srt(segundos: float) -> str:
    """Converte segundos para formato SRT (HH:MM:SS,mmm)."""
    h = int(segundos // 3600)
    m = int((segundos % 3600) // 60)
    s = int(segundos % 60)
    ms = int((segundos - int(segundos)) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def salvar_saida(resultado, caminho_audio, formato="txt", output_dir=None, segmentos_diarizados=None):
    """
    Salva a transcrição em arquivo.

    Args:
        resultado: Resultado do Whisper (dict com 'text' e 'segments')
        caminho_audio: Caminho do áudio original
        formato: "txt", "json" ou "srt"
        output_dir: Pasta de saída
        segmentos_diarizados: Lista de segmentos com campo 'speaker' (opcional)
    """
    if output_dir is None:
        raise ValueError("output_dir precisa ser informado")

    base = os.path.splitext(os.path.basename(caminho_audio))[0]

    # 🔧 Garante que a pasta existe
    os.makedirs(output_dir, exist_ok=True)

    # Decide se usa segmentos diarizados ou originais
    tem_diarizacao = (
        segmentos_diarizados is not None
        and len(segmentos_diarizados) > 0
        and all("speaker" in seg for seg in segmentos_diarizados)
    )

    if formato == "txt":
        path = os.path.join(output_dir, f"{base}.txt")
        with open(path, "w", encoding="utf-8") as f:
            if tem_diarizacao:
                falante_atual = None
                for seg in segmentos_diarizados:
                    if seg["speaker"] != falante_atual:
                        falante_atual = seg["speaker"]
                        f.write(f"\n[{falante_atual}]\n")
                    f.write(f"{seg['text'].strip()}\n")
            else:
                f.write(resultado["text"])

    elif formato == "json":
        path = os.path.join(output_dir, f"{base}.json")
        with open(path, "w", encoding="utf-8") as f:
            if tem_diarizacao:
                dados = {
                    "text": resultado["text"],
                    "segments": segmentos_diarizados
                }
            else:
                dados = resultado
            json.dump(dados, f, ensure_ascii=False, indent=2)

    elif formato == "srt":
        path = os.path.join(output_dir, f"{base}.srt")
        with open(path, "w", encoding="utf-8") as f:
            segmentos = segmentos_diarizados if tem_diarizacao else resultado["segments"]
            for i, seg in enumerate(segmentos, 1):
                f.write(f"{i}\n")
                inicio = _formatar_tempo_srt(seg['start'])
                fim = _formatar_tempo_srt(seg['end'])
                f.write(f"{inicio} --> {fim}\n")
                if tem_diarizacao:
                    f.write(f"[{seg['speaker']}] {seg['text'].strip()}\n\n")
                else:
                    f.write(f"{seg['text'].strip()}\n\n")

    else:
        raise ValueError(f"Formato inválido: {formato}")

    return path
