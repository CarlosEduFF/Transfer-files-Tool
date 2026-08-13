# 🎵 8-Bit Music Maker & Audio Sequencer

Estúdio de composição musical e sequenciador de notas em Python com interface gráfica (Tkinter), reprodução de sintetizadores em tempo real e exportação para arquivos MIDI.

---

## 🚀 Funcionalidades

- **🎹 Sequenciador Interativo de Notas**: Adicione, edite, remova e reordene notas musicais com altura (oitava), acidentes (# / b), duração e volume.
- **🎼 Sintetizador de Instrumentos**:
  - Piano Acústico (Realista)
  - Violão de Náilon
  - Flauta (Sopro Suave)
  - Órgão / Sanfona
  - Sintetizador 8-Bit
- **🥁 Acompanhamento Rítmico / Bateria**:
  - Pop / Rock (4/4)
  - Eletrônico / Dance
  - Valsa (3/4)
  - Forró Tradicional / Baião
- **🔄 Modo de Repetição (Loop Contínuo)**: Mantém o áudio tocando continuamente enquanto você compõe.
- **💾 Exportação MIDI**: Salve suas composições em arquivos `.mid` compatíveis com qualquer DAW ou software de áudio.
- **🎶 Presets de Exemplo**: Inclui temas pré-carregados (Brilha Brilha Estrelinha, Tema Game 8-Bit, Asa Branca, Escala Maior).

---

## 📁 Estrutura do Projeto

```
/
├── README.md
├── requirements.txt
├── .gitignore
└── src/
    ├── __init__.py
    ├── engine.py       # Motor de síntese de áudio e gerador MIDI (Pygame + NumPy)
    ├── gui.py          # Interface gráfica em Tkinter
    └── main.py         # Ponto de entrada do aplicativo
```

---

## ⚙️ Pré-requisitos & Instalação

1. Certifique-se de ter o **Python 3.10+** instalado.
2. Instale as dependências executando:

```bash
pip install -r requirements.txt
```

---

## ▶️ Como Executar

Execute o comando na raiz do projeto:

```bash
python src/main.py
```

---

## 🛠️ Tecnologias Utilizadas

- **Python 3**
- **Tkinter** (Interface Gráfica)
- **Pygame** (Reprodução de áudio e síntese sonora)
- **NumPy** (Cálculos de formas de onda e síntese de harmônicos)
- **MIDIUtil** (Geração de arquivos `.mid`)

---

Projeto desenvolvido para automação e criação musical em Python.
