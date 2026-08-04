"""Baixa um video do YouTube e transcreve a fala para texto.

Pega a URL, baixa o audio, converte para WAV 16kHz mono e transcreve em blocos,
salvando o resultado em um .txt. Tambem aceita arquivos locais.

A transcricao usa a API do Google (via SpeechRecognition), que precisa de internet.
Para transcricao offline de arquivos locais, com deteccao de falantes e saida em
SRT/JSON, veja a ferramenta AudioTranscriber (baseada em Whisper).

Uso:
    python -m youtube_to_text                       # menu interativo
    python -m youtube_to_text <url-do-youtube>
    python -m youtube_to_text caminho/do/video.mp4
    python -m youtube_to_text <url> --bloco 30      # blocos de 30s em vez de 50s
"""

import shutil
import sys
from pathlib import Path

import speech_recognition as sr
from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError

# MoviePy 2.x expoe as classes na raiz; 1.x apenas em moviepy.editor.
try:
    from moviepy import AudioFileClip, VideoFileClip
except ImportError:
    from moviepy.editor import AudioFileClip, VideoFileClip

SAIDA = Path("saida")

# O reconhecedor do Google rejeita audios muito longos; ~50s por bloco e o limite pratico.
BLOCO_PADRAO = 50


def runtimes_js():
    """Runtimes JavaScript disponiveis para o yt-dlp.

    O YouTube exige execucao de JavaScript para resolver as URLs de download; sem um
    runtime, o download falha com HTTP 403. O yt-dlp so habilita o "deno" por padrao,
    entao o node e adicionado quando estiver instalado.
    """
    # A API do yt-dlp espera {runtime: {config}} — diferente do --js-runtimes da CLI.
    return {nome: {} for nome in ("deno", "node", "bun") if shutil.which(nome)} or None


def baixar(url):
    """Baixa o audio do video da URL. Retorna o caminho do arquivo."""
    SAIDA.mkdir(exist_ok=True)
    opcoes = {
        "format": "bestaudio/best",
        "outtmpl": str(SAIDA / "%(title)s.%(ext)s"),
    }

    runtimes = runtimes_js()
    if runtimes:
        opcoes["js_runtimes"] = runtimes

    with YoutubeDL(opcoes) as ydl:
        info = ydl.extract_info(url, download=True)
        return Path(ydl.prepare_filename(info))


def para_wav(origem):
    """Converte qualquer video/audio para WAV 16kHz mono, o formato que o
    speech_recognition aceita. Retorna o caminho do wav."""
    origem = Path(origem)
    destino = SAIDA / f"{origem.stem}.wav"
    SAIDA.mkdir(exist_ok=True)

    # Videos tem trilha de audio em .audio; arquivos de audio abrem direto.
    try:
        clip = VideoFileClip(str(origem))
        audio = clip.audio
        if audio is None:
            clip.close()
            raise ValueError("Esse arquivo nao tem trilha de audio.")
    except (KeyError, OSError, IndexError):
        clip = None
        audio = AudioFileClip(str(origem))

    try:
        audio.write_audiofile(str(destino), fps=16000, nbytes=2, ffmpeg_params=["-ac", "1"])
    finally:
        # No Windows o arquivo fica travado enquanto o clip estiver aberto.
        audio.close()
        if clip is not None:
            clip.close()

    return destino


def duracao(wav):
    with sr.AudioFile(str(wav)) as fonte:
        return fonte.DURATION


def transcrever(wav, segundos_por_bloco=BLOCO_PADRAO):
    """Transcreve o wav em blocos. Retorna o texto completo."""
    reconhecedor = sr.Recognizer()
    total = duracao(wav)
    partes = []

    inicio = 0.0
    # A margem evita um ultimo bloco vazio quando a soma dos blocos bate com o total.
    while inicio < total - 0.1:
        with sr.AudioFile(str(wav)) as fonte:
            audio = reconhecedor.record(fonte, offset=inicio, duration=segundos_por_bloco)

        fim = min(inicio + segundos_por_bloco, total)
        print(f"  transcrevendo {inicio:.0f}s - {fim:.0f}s de {total:.0f}s...")

        try:
            partes.append(reconhecedor.recognize_google(audio, language="pt-BR"))
        except sr.UnknownValueError:
            print("    (trecho sem fala reconhecivel)")
        except sr.RequestError as erro:
            print(f"    (falha no servico: {erro})")
            break

        inicio += segundos_por_bloco

    return " ".join(partes)


def perguntar_bloco():
    """Pergunta o tamanho do bloco, aceitando vazio para usar o padrao."""
    resposta = input(f"Segundos por bloco [{BLOCO_PADRAO:.0f}]: ").strip()
    if not resposta:
        return BLOCO_PADRAO
    try:
        return float(resposta)
    except ValueError:
        print(f"Valor invalido, usando {BLOCO_PADRAO:.0f}s.")
        return BLOCO_PADRAO


def menu():
    """Menu interativo. Retorna (entrada, bloco) ou None para sair."""
    print("\n=== YouTube to Text ===")
    print("1) Transcrever video do YouTube (URL)")
    print("2) Transcrever arquivo local")
    print("0) Sair")

    escolha = input("\nEscolha: ").strip()

    if escolha == "1":
        url = input("URL do video: ").strip()
        if not url:
            print("Nenhuma URL informada.")
            return None
        return url, perguntar_bloco()

    if escolha == "2":
        caminho = input("Caminho do arquivo: ").strip().strip('"')
        if not caminho:
            print("Nenhum caminho informado.")
            return None
        return caminho, perguntar_bloco()

    if escolha == "0":
        return None

    print("Opcao invalida.")
    return None


def executar(entrada, bloco):
    """Roda o pipeline completo para a entrada informada."""
    if entrada.startswith("http"):
        print("\nBaixando video...")
        origem = baixar(entrada)
    else:
        origem = Path(entrada)
        if not origem.exists():
            print(f"Arquivo nao encontrado: {origem}")
            return

    print("Convertendo para WAV 16kHz mono...")
    wav = para_wav(origem)

    print("Transcrevendo...")
    texto = transcrever(wav, bloco)

    if not texto.strip():
        print("\nNada foi reconhecido no audio.")
        return

    destino = SAIDA / f"{Path(origem).stem}.txt"
    destino.write_text(texto, encoding="utf-8")

    print(f"\nTranscricao salva em: {destino}")
    print(f"\n{texto[:500]}{'...' if len(texto) > 500 else ''}")


def main():
    try:
        executar_acao()
    except DownloadError as erro:
        texto = str(erro)
        if "403" in texto or "Forbidden" in texto:
            print("\nO YouTube recusou o download (HTTP 403).")
            if not runtimes_js():
                print("Causa provavel: nenhum runtime JavaScript instalado.")
                print("Instale o Node.js (https://nodejs.org) e tente de novo.")
            else:
                print("Seu yt-dlp pode estar desatualizado: pip install -U yt-dlp")
        else:
            print(f"\nNao consegui baixar o video: {texto}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nCancelado.")
        sys.exit(1)


def executar_acao():
    # Sem argumentos: menu interativo. Com argumentos: modo direto.
    if len(sys.argv) < 2:
        escolha = menu()
        if escolha is None:
            return
        executar(*escolha)
        return

    bloco = BLOCO_PADRAO
    if "--bloco" in sys.argv:
        bloco = float(sys.argv[sys.argv.index("--bloco") + 1])

    executar(sys.argv[1], bloco)


if __name__ == "__main__":
    main()
