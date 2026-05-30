# PDF Tools

Ferramenta de linha de comando para manipulação completa de PDFs: cortar, mesclar,
comprimir, rotacionar, converter de/para imagens, converter HTML/URL em PDF, extrair
texto e inspecionar metadados.

Oferece duas interfaces sobre a **mesma** lógica:

- **CLI** — `pdftools <comando> [opções]`
- **Menu interativo** — `python -m pdftools`

## Instalação

Requer Python 3.10+.

```bash
pip install -e .
```

> O comando `pdftools` é instalado no diretório de scripts do Python. Se ele não estiver
> no seu `PATH`, use a forma equivalente `python -m pdftools` (menu) ou
> `python -m pdftools.presentation.cli <comando>` (CLI).

Para desenvolvimento (testes):

```bash
pip install -e ".[dev]"
```

> **WeasyPrint** (usado por `html2pdf`) depende de bibliotecas nativas (GTK/GObject).
> No Windows, siga a [documentação oficial](https://doc.courtbouillon.org/weasyprint/stable/first_steps.html#windows).
> As demais funcionalidades não exigem essas bibliotecas.

## Uso

### Menu interativo

```bash
python -m pdftools
```

O menu lista todas as operações disponíveis e guia você pelos parâmetros de cada uma.

### CLI

```bash
pdftools --help                       # lista todos os comandos

# Cortar um intervalo de páginas
pdftools split documento.pdf --pages "1-3" --output recorte.pdf

# Dividir em várias partes (cada parte é um intervalo)
pdftools split-parts documento.pdf --ranges "1-3;4-7;8-10"

# Mesclar PDFs (na ordem informada)
pdftools merge a.pdf b.pdf c.pdf --output final.pdf

# Comprimir
pdftools compress documento.pdf

# Rotacionar (ângulo múltiplo de 90)
pdftools rotate documento.pdf --degrees 90 --pages "1,3"

# PDF → imagens
pdftools pdf2img documento.pdf --format png --dpi 150 --pages "1-5"

# Imagens → PDF
pdftools img2pdf img1.png img2.jpg --output album.pdf

# HTML/URL → PDF
pdftools html2pdf https://exemplo.com --output pagina.pdf

# Extrair texto
pdftools extract-text documento.pdf --pages "1-2" --output texto.txt

# Metadados
pdftools metadata documento.pdf --format json
```

## Comandos disponíveis

| Comando        | Descrição                                            |
|----------------|------------------------------------------------------|
| `split`        | Extrai um intervalo de páginas para um único arquivo |
| `split-parts`  | Divide o PDF em várias partes                         |
| `merge`        | Mescla múltiplos PDFs                                 |
| `compress`     | Comprime o PDF                                        |
| `rotate`       | Rotaciona páginas                                     |
| `pdf2img`      | Converte páginas em imagens (PNG/JPG)                 |
| `img2pdf`      | Converte imagens em PDF                               |
| `html2pdf`     | Converte HTML/URL em PDF                              |
| `extract-text` | Extrai texto (backends `fitz` ou `pdfplumber`)       |
| `metadata`     | Exibe metadados (tabela ou JSON)                      |

## Arquitetura

O projeto usa uma **arquitetura de plugins (registry de operações)** em camadas. As
dependências apontam sempre para dentro: `presentation → operations → shared`.

```
src/pdftools/
├── shared/              # núcleo puro reutilizável (sem typer/rich)
│   ├── errors.py        # PdfToolsError + ValidationError, PdfOpenError, ...
│   ├── page_range.py    # parse_page_range()
│   ├── validation.py    # validate_pdf_path()
│   └── formatting.py    # format_size()
│
├── operations/          # cada arquivo = 1 operação autossuficiente e auto-registrada
│   ├── base.py          # Operation, Param, ParamType, Result (o contrato)
│   ├── registry.py      # @register / get() / all()
│   ├── split.py, merge.py, compress.py, ...
│   └── __init__.py      # importa os módulos para disparar o auto-registro
│
└── presentation/        # interfaces de usuário
    ├── console.py       # Console Rich compartilhado
    ├── cli.py           # Typer gerado dinamicamente a partir do registry
    └── menu.py          # menu interativo gerado a partir do registry
```

Princípios:

- **`shared/` e `operations/` são puros**: não conhecem Typer nem Rich. A lógica retorna
  um objeto de resultado (`Result`) em vez de imprimir.
- **Erros unificados**: tudo herda de `PdfToolsError`; só a camada de apresentação traduz
  para o formato do framework (ex.: `typer.BadParameter`).
- **CLI e menu derivam da mesma fonte**: cada operação declara seus parâmetros via `Param`,
  e tanto a CLI quanto o menu geram suas interfaces a partir dessa declaração.

### Adicionar uma nova operação

Basta **criar um arquivo** em `operations/` e registrá-lo. CLI e menu passam a expô-lo
automaticamente — sem editar `cli.py` nem `menu.py`.

```python
# src/pdftools/operations/watermark.py
from pathlib import Path
from .base import Operation, Param, ParamType, Result
from .registry import register


@register
class WatermarkOperation(Operation):
    name = "watermark"
    help = "Aplica uma marca d'água em um PDF."
    menu_label = "Aplicar marca d'água"
    params = [
        Param("input_pdf", ParamType.PDF, "Arquivo PDF de entrada"),
        Param("text", ParamType.STR, "Texto da marca d'água", cli_flags=("--text", "-t")),
        Param("output", ParamType.OUTPUT_PATH, "Arquivo de saída",
              required=False, cli_flags=("--output", "-o")),
    ]

    def run(self, input_pdf: Path, text: str, output: Path | None = None) -> Result:
        ...  # lógica aqui — retorne um Result, não imprima
        return Result(message=f"Marca d'água aplicada → {output}", outputs=[output])
```

Depois, adicione o import em [`operations/__init__.py`](src/pdftools/operations/__init__.py)
(o único ponto que lista os módulos a carregar):

```python
from . import (  # noqa: F401
    ...,
    watermark,
)
```

Operações com saída mais rica (tabelas) podem sobrescrever `render(self, result, console)`
— veja [`merge.py`](src/pdftools/operations/merge.py) e
[`metadata.py`](src/pdftools/operations/metadata.py) como exemplos.

## Testes

```bash
pytest
```

Os testes exercitam a lógica diretamente pelas operações do registry, asserindo sobre o
objeto de resultado retornado. Há ainda testes de domínio (`parse_page_range`) e do próprio
registry. O teste de `html2pdf` é pulado automaticamente quando o WeasyPrint não pode ser
carregado no ambiente.

## Dependências

- [PyMuPDF (`fitz`)](https://pymupdf.readthedocs.io/) — manipulação de PDF e rasterização
- [pdfplumber](https://github.com/jsvine/pdfplumber) — extração de texto/tabelas
- [Pillow](https://python-pillow.org/) — imagens
- [WeasyPrint](https://weasyprint.org/) — HTML → PDF
- [Typer](https://typer.tiangolo.com/) — CLI
- [Rich](https://rich.readthedocs.io/) — saída formatada no terminal

## Licença

MIT
