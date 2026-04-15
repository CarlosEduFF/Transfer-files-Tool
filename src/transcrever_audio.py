"""
Transcritor de Áudio para Texto
================================
Usa o modelo Whisper (OpenAI) localmente para transcrever áudios.

Instalação das dependências:
    pip install openai-whisper
    pip install ffmpeg-python

Também é necessário ter o ffmpeg instalado no sistema:
    - Windows: https://ffmpeg.org/download.html  (adicione ao PATH)
    - macOS:   brew install ffmpeg
    - Linux:   sudo apt install ffmpeg

Formatos suportados: mp3, mp4, wav, m4a, ogg, flac, webm, etc.

Uso:
    1. Coloque o arquivo de áudio na mesma pasta deste script.
    2. Execute: python transcrever_audio.py
    3. O resultado será salvo em transcricao_<nome_do_arquivo>.txt
"""

import os
import sys

# --------------------------------------------------------------------------- #
# Configurações — ajuste aqui se quiser
# --------------------------------------------------------------------------- #

# Deixe None para o script listar os áudios disponíveis e você escolher,
# ou defina o nome do arquivo diretamente, ex: ARQUIVO_AUDIO = "entrevista.mp3"
ARQUIVO_AUDIO = None

# Modelo Whisper: "tiny", "base", "small", "medium", "large"
#   tiny/base  → rápido, menos preciso
#   small      → bom equilíbrio (recomendado para começar)
#   medium/large → mais lento, mais preciso
MODELO = "large"

# Idioma do áudio (None = detecção automática)
# Exemplos: "portuguese", "english", "spanish"
IDIOMA = "portuguese"

# --------------------------------------------------------------------------- #

EXTENSOES_AUDIO = {".mp3", ".mp4", ".wav", ".m4a", ".ogg", ".flac", ".webm", ".aac", ".wma"}


def listar_audios(pasta: str) -> list[str]:
    """Retorna lista de arquivos de áudio na pasta."""
    return [
        f for f in os.listdir(pasta)
        if os.path.splitext(f)[1].lower() in EXTENSOES_AUDIO
    ]


def escolher_audio(pasta: str) -> str:
    """Permite o usuário escolher o áudio se ARQUIVO_AUDIO não estiver definido."""
    audios = listar_audios(pasta)

    if not audios:
        print("❌ Nenhum arquivo de áudio encontrado na pasta do script.")
        print(f"   Formatos suportados: {', '.join(sorted(EXTENSOES_AUDIO))}")
        sys.exit(1)

    if len(audios) == 1:
        print(f"✅ Áudio encontrado: {audios[0]}")
        return audios[0]

    print("🎵 Arquivos de áudio encontrados:")
    for i, nome in enumerate(audios, 1):
        print(f"   [{i}] {nome}")

    while True:
        try:
            escolha = int(input("\nDigite o número do arquivo que deseja transcrever: "))
            if 1 <= escolha <= len(audios):
                return audios[escolha - 1]
            print(f"   Por favor, escolha um número entre 1 e {len(audios)}.")
        except ValueError:
            print("   Entrada inválida. Digite apenas o número.")


def transcrever(caminho_audio: str, modelo: str, idioma: str | None) -> str:
    """Carrega o modelo Whisper e transcreve o áudio."""
    try:
        import whisper
    except ImportError:
        print("❌ Biblioteca 'openai-whisper' não encontrada.")
        print("   Instale com: pip install openai-whisper")
        sys.exit(1)

    print(f"\n⏳ Carregando modelo '{modelo}'... (pode demorar na primeira vez)")
    model = whisper.load_model(modelo)

    print(f"🎙️  Transcrevendo: {os.path.basename(caminho_audio)}")
    opcoes = {"language": idioma} if idioma else {}
    resultado = model.transcribe(caminho_audio, **opcoes)

    return resultado["text"]


def salvar_txt(texto: str, caminho_audio: str) -> str:
    """Salva a transcrição em um arquivo .txt ao lado do áudio."""
    base = os.path.splitext(os.path.basename(caminho_audio))[0]
    pasta = os.path.dirname(caminho_audio)
    caminho_saida = os.path.join(pasta, f"transcricao_{base}.txt")

    with open(caminho_saida, "w", encoding="utf-8") as f:
        f.write(texto)

    return caminho_saida


def main():
    pasta_script = os.path.dirname(os.path.abspath(__file__))

    # Determina qual arquivo usar
    if ARQUIVO_AUDIO:
        nome_arquivo = ARQUIVO_AUDIO
        caminho_audio = os.path.join(pasta_script, nome_arquivo)
        if not os.path.isfile(caminho_audio):
            print(f"❌ Arquivo não encontrado: {caminho_audio}")
            sys.exit(1)
    else:
        nome_arquivo = escolher_audio(pasta_script)
        caminho_audio = os.path.join(pasta_script, nome_arquivo)

    # Transcreve
    texto = transcrever(caminho_audio, MODELO, IDIOMA)

    # Salva
    caminho_saida = salvar_txt(texto, caminho_audio)

    print(f"\n✅ Transcrição concluída!")
    print(f"   Arquivo salvo em: {caminho_saida}")
    print("\n--- PRÉVIA (primeiros 500 caracteres) ---")
    print(texto[:500])
    if len(texto) > 500:
        print("... [texto continua no arquivo]")


if __name__ == "__main__":
    main()