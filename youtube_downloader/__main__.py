"""Baixa videos do YouTube e converte para mp3, gif ou trechos cortados.

Uso:
    python -m youtube_downloader                      # menu interativo
    python -m youtube_downloader <url> --video        # baixa o video em mp4
    python -m youtube_downloader <url> --audio        # baixa apenas o audio em mp3
    python -m youtube_downloader <url> --gif 0 5      # baixa e gera um gif dos segundos 0 a 5
    python -m youtube_downloader <url> --cortar 10 30 # baixa e corta o trecho de 10s a 30s
    python -m youtube_downloader <url> --extrair      # baixa o video e extrai o audio
"""

import glob
import shutil
import sys
from pathlib import Path

from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError

# MoviePy 2.x expoe as classes na raiz; 1.x apenas em moviepy.editor.
try:
    from moviepy import VideoFileClip
except ImportError:
    from moviepy.editor import VideoFileClip

SAIDA = Path("saida")


def caminho_ffmpeg():
    """Localiza o FFmpeg. O yt-dlp precisa dele para juntar video e audio em mp4.

    Se nao estiver no PATH, usa o binario que vem com o imageio-ffmpeg (instalado
    junto com o moviepy). Esse binario tem nome versionado
    (ffmpeg-win-x86_64-v7.1.exe) e o yt-dlp so reconhece "ffmpeg.exe", entao ele e
    copiado uma vez para .ffmpeg/ com o nome esperado.

    Retorna a pasta a passar em ffmpeg_location, ou None se o FFmpeg ja estiver no
    PATH (ou se nao houver nenhum disponivel).
    """
    if shutil.which("ffmpeg"):
        return None  # ja esta no PATH, o yt-dlp acha sozinho

    try:
        import imageio_ffmpeg

        origem = Path(imageio_ffmpeg.get_ffmpeg_exe())
    except (ImportError, RuntimeError):
        return None

    if not origem.exists():
        return None

    pasta = Path(__file__).parent / ".ffmpeg"
    destino = pasta / ("ffmpeg.exe" if origem.suffix == ".exe" else "ffmpeg")
    if not destino.exists():
        pasta.mkdir(exist_ok=True)
        shutil.copy2(origem, destino)

    return str(pasta)


def runtimes_js():
    """Runtimes JavaScript disponiveis para o yt-dlp.

    O YouTube exige execucao de JavaScript para resolver as URLs de download; sem um
    runtime, varios formatos vem sem URL e o download falha com HTTP 403. O yt-dlp so
    habilita o "deno" por padrao, entao o node e adicionado quando estiver instalado.
    """
    # A API do yt-dlp espera {runtime: {config}} — diferente do --js-runtimes da CLI.
    return {nome: {} for nome in ("deno", "node", "bun") if shutil.which(nome)} or None


def opcoes_base():
    """Opcoes comuns a todos os downloads, ja com FFmpeg e runtime JS configurados."""
    opcoes = {"outtmpl": str(SAIDA / "%(title)s.%(ext)s")}

    pasta_ffmpeg = caminho_ffmpeg()
    if pasta_ffmpeg:
        opcoes["ffmpeg_location"] = pasta_ffmpeg

    runtimes = runtimes_js()
    if runtimes:
        opcoes["js_runtimes"] = runtimes

    return opcoes


def recortar(clip, inicio, fim):
    """Recorta um trecho do clip. O metodo mudou de nome no MoviePy 2.x."""
    if hasattr(clip, "subclipped"):
        return clip.subclipped(inicio, fim)
    return clip.subclip(inicio, fim)


def baixar_video(url):
    """Baixa o video sempre em mp4 (com audio). Retorna o caminho do arquivo."""
    SAIDA.mkdir(exist_ok=True)
    opcoes = opcoes_base()
    opcoes.update({
        "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/bestvideo+bestaudio/best",
        "merge_output_format": "mp4",
        # Converte para mp4 quando a melhor fonte disponivel for webm/mkv.
        "postprocessors": [{"key": "FFmpegVideoConvertor", "preferedformat": "mp4"}],
    })

    with YoutubeDL(opcoes) as ydl:
        info = ydl.extract_info(url, download=True)
        return caminho_final(ydl, info, ".mp4")


def caminho_final(ydl, info, extensao):
    """Descobre o caminho real do arquivo apos os pos-processadores.

    O yt-dlp muda a extensao ao converter, entao prepare_filename() pode apontar
    para um arquivo que nao existe mais.
    """
    previsto = Path(ydl.prepare_filename(info))
    convertido = previsto.with_suffix(extensao)

    if convertido.exists():
        return convertido
    if previsto.exists():
        return previsto

    # Ultimo recurso: procura pelo nome base, qualquer que seja a extensao final.
    candidatos = sorted(SAIDA.glob(f"{glob.escape(previsto.stem)}.*"))
    return candidatos[0] if candidatos else convertido


def baixar_audio(url):
    """Baixa apenas a trilha de audio e converte para mp3. Retorna o caminho."""
    SAIDA.mkdir(exist_ok=True)
    opcoes = opcoes_base()
    opcoes.update({
        "format": "bestaudio/best",
        "postprocessors": [
            {"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192"}
        ],
    })
    with YoutubeDL(opcoes) as ydl:
        info = ydl.extract_info(url, download=True)
        return caminho_final(ydl, info, ".mp3")


def para_gif(video, inicio, fim):
    """Gera um gif do trecho indicado. Retorna o caminho do gif."""
    destino = Path(video).with_suffix(".gif")
    # O clip precisa ser fechado: no Windows o arquivo fica travado enquanto aberto.
    with VideoFileClip(str(video)) as clip:
        with recortar(clip, inicio, fim) as trecho:
            trecho.write_gif(str(destino))
    return destino


def extrair_audio(video):
    """Extrai a trilha de audio do video ja baixado. Retorna o caminho do mp3."""
    destino = Path(video).with_suffix(".mp3")
    with VideoFileClip(str(video)) as clip:
        if clip.audio is None:
            raise ValueError("Esse video nao tem trilha de audio.")
        clip.audio.write_audiofile(str(destino))
    return destino


def cortar(video, inicio, fim):
    """Corta um trecho do video. Retorna o caminho do novo mp4."""
    origem = Path(video)
    destino = origem.with_name(f"{origem.stem}_corte.mp4")
    with VideoFileClip(str(video)) as clip:
        with recortar(clip, inicio, fim) as trecho:
            trecho.write_videofile(str(destino))
    return destino


def pedir_intervalo():
    """Le o intervalo em segundos. Retorna (inicio, fim) ou None se invalido."""
    try:
        inicio = float(input("Segundo inicial: ").strip())
        fim = float(input("Segundo final: ").strip())
    except ValueError:
        print("Informe numeros em segundos (ex.: 0 e 5).")
        return None

    if fim <= inicio:
        print("O segundo final precisa ser maior que o inicial.")
        return None

    return inicio, fim


def menu():
    print("\n=== Downloader de YouTube ===")
    print("1) Baixar video (mp4)")
    print("2) Baixar apenas audio (mp3)")
    print("3) Baixar e gerar gif de um trecho")
    print("4) Baixar e cortar um trecho")
    print("5) Baixar video e extrair o audio")
    print("0) Sair")

    escolha = input("\nEscolha: ").strip()

    if escolha == "0":
        return
    if escolha not in ("1", "2", "3", "4", "5"):
        print("Opcao invalida.")
        return

    url = input("\nURL do video do YouTube: ").strip()
    if not url:
        print("Nenhuma URL informada.")
        return

    if escolha == "1":
        print(f"Pronto: {baixar_video(url)}")
    elif escolha == "2":
        print(f"Pronto: {baixar_audio(url)}")
    elif escolha == "3":
        intervalo = pedir_intervalo()
        if intervalo:
            print(f"Pronto: {para_gif(baixar_video(url), *intervalo)}")
    elif escolha == "4":
        intervalo = pedir_intervalo()
        if intervalo:
            print(f"Pronto: {cortar(baixar_video(url), *intervalo)}")
    elif escolha == "5":
        print(f"Pronto: {extrair_audio(baixar_video(url))}")


def explicar_falha(erro):
    """Traduz os erros mais comuns do yt-dlp em uma orientacao util."""
    texto = str(erro)

    if "403" in texto or "Forbidden" in texto:
        print("\nO YouTube recusou o download (HTTP 403).")
        if not runtimes_js():
            print("Causa provavel: nenhum runtime JavaScript instalado.")
            print("O YouTube exige execucao de JS para liberar as URLs de download.")
            print("Instale o Node.js (https://nodejs.org) ou o Deno e tente de novo.")
        else:
            print("Seu yt-dlp pode estar desatualizado. Atualize com:")
            print("  pip install -U yt-dlp")
    elif "Private video" in texto or "members-only" in texto:
        print("\nEsse video e privado ou exclusivo para membros do canal.")
    elif "Video unavailable" in texto:
        print("\nVideo indisponivel. Confira se a URL esta correta.")
    elif "Sign in" in texto or "age" in texto.lower():
        print("\nEsse video exige login (restricao de idade ou conta).")
    else:
        print(f"\nNao consegui baixar: {texto}")


def main():
    try:
        executar_acao()
    except DownloadError as erro:
        # O yt-dlp ja imprime o motivo; aqui traduzimos para uma orientacao pratica.
        explicar_falha(erro)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nCancelado.")
        sys.exit(1)


def executar_acao():
    if len(sys.argv) < 2:
        menu()
        return

    url = sys.argv[1]
    acao = sys.argv[2] if len(sys.argv) > 2 else "--video"

    if acao == "--audio":
        print(f"Pronto: {baixar_audio(url)}")
    elif acao == "--gif":
        inicio, fim = float(sys.argv[3]), float(sys.argv[4])
        print(f"Pronto: {para_gif(baixar_video(url), inicio, fim)}")
    elif acao == "--cortar":
        inicio, fim = float(sys.argv[3]), float(sys.argv[4])
        print(f"Pronto: {cortar(baixar_video(url), inicio, fim)}")
    elif acao == "--extrair":
        print(f"Pronto: {extrair_audio(baixar_video(url))}")
    else:
        print(f"Pronto: {baixar_video(url)}")


if __name__ == "__main__":
    main()
