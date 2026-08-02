# Remove BG

Remove o fundo de uma imagem ou de uma pasta inteira de imagens.

Requisitos: Python 3.9+, rembg, Pillow.
    pip install -r requirements.txt

Como executar (a partir da raiz do projeto):
    python -m remove_bg                            # input.jpg -> output.png
    python -m remove_bg foto.png resultado.png      # arquivo único
    python -m remove_bg fotos/ resultados/          # pasta inteira

Opções:
    --model               modelo de segmentação: u2net, u2netp, u2net_human_seg,
                           u2net_cloth_seg, silueta, isnet-general-use, isnet-anime
                           (padrão: u2net)
    --alpha-matting        bordas mais suaves (cabelo, pelos), com --af-threshold,
                           --ab-threshold e --matting-erode-size
    --bgcolor R,G,B[,A]    preenche o fundo com uma cor sólida em vez de transparência

Exemplos:
    python -m remove_bg foto.jpg saida.png --model isnet-general-use
    python -m remove_bg foto.jpg saida.png --alpha-matting
    python -m remove_bg foto.jpg saida.png --bgcolor 255,255,255
