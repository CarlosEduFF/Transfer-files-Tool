# QR Code Generator

Gera um QR code a partir de texto ou URL, em PNG ou SVG.

Requisitos: Python 3.9+, qrcode[pil].
    pip install -r requirements.txt

Como executar (a partir da raiz do projeto):
    python -m qrcode_generator                                              # padrão
    python -m qrcode_generator "minha url" saida.png --fill-color darkblue --back-color "#eeeeee"
    python -m qrcode_generator "minha url" saida.svg --error-correction H

Opções:
    --fill-color / --back-color   cores (padrão: black / white)
    --error-correction {L,M,Q,H}  nível de correção de erro (padrão: M)
    --box-size / --border          tamanho da caixa em pixels e borda em caixas
    --version                      versão do QR 1-40, controla tamanho/capacidade (padrão: automático)

O formato de saída é escolhido pela extensão do arquivo: .svg gera um SVG,
qualquer outra gera uma imagem raster (PNG, etc.).
