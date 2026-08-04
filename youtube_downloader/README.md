# Downloader de YouTube

Baixa videos do YouTube e converte para mp3, gif ou trechos cortados.

## Instalacao

```bash
pip install -r requirements.txt
```

### Runtime JavaScript (Node.js)

O YouTube exige a execucao de JavaScript para liberar as URLs de download. Sem um
runtime instalado, o yt-dlp escolhe formatos cuja URL nao funciona e o download falha
com **HTTP 403 Forbidden**.

Instale o [Node.js](https://nodejs.org) (ou o Deno). O programa detecta o runtime
sozinho e o habilita — o yt-dlp, por padrao, so procura pelo Deno.

Mantenha tambem o yt-dlp atualizado, porque o YouTube muda com frequencia:

```bash
pip install -U yt-dlp
```

### FFmpeg

O FFmpeg e obrigatorio: sem ele o YouTube entrega video e audio em arquivos separados
e o yt-dlp nao consegue junta-los num mp4 unico.

Nao e preciso instalar nada a parte. O `moviepy` traz o `imageio-ffmpeg` junto, e o
programa localiza esse binario sozinho (ele e copiado uma vez para `.ffmpeg/`, porque
o yt-dlp so reconhece um executavel chamado `ffmpeg.exe`). Se voce ja tiver o FFmpeg
no PATH, o seu e usado no lugar.

## Uso

```bash
python -m youtube_downloader                       # menu interativo
python -m youtube_downloader <url> --video         # baixa o video em mp4
python -m youtube_downloader <url> --audio         # baixa apenas o audio em mp3
python -m youtube_downloader <url> --gif 0 5       # gera um gif dos segundos 0 a 5
python -m youtube_downloader <url> --cortar 10 30  # corta o trecho de 10s a 30s
python -m youtube_downloader <url> --extrair       # baixa o video e extrai o audio
```

Os arquivos sao salvos na pasta `saida/`.

O download de video sai **sempre em mp4 com audio**: o yt-dlp prefere as faixas mp4/m4a,
junta as duas e, se a unica fonte disponivel for webm ou mkv, converte o resultado.

## Nota sobre o pytube

Este projeto usa `yt-dlp` em vez de `pytube`: o pytube quebra a cada mudanca do YouTube
e esta sem manutencao ativa.
