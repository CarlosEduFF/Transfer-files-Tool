# 🎙️ Transcritor de Áudio com Whisper

Projeto em Python para transcrição de áudio para texto utilizando o modelo Whisper localmente.

---

## 🚀 Funcionalidades

* Transcrição de áudios (mp3, wav, m4a, mp4, etc.)
* Escolha de modelo (tiny → large)
* Seleção de idioma ou detecção automática
* Suporte a CPU ou GPU (CUDA)
* Exportação em múltiplos formatos:

  * TXT
  * JSON
  * SRT (legendas)
* Estrutura organizada de entrada/saída

---

## 📁 Estrutura do Projeto

```
transcritor/
│
├── main.py
├── menu.py
├── utils.py
├── config.py
│
├── core/
│   ├── transcriber.py
│   └── file_manager.py
│
├── data/
│   ├── input/        # coloque os áudios aqui
│   └── output/       # transcrições geradas
```

---

## ⚙️ Instalação

### 1. Clonar ou baixar o projeto

```
git clone <repo-url>
cd transcritor
```

### 2. Criar ambiente virtual (recomendado)

```
python -m venv venv
venv\Scripts\activate
```

### 3. Instalar dependências

```
pip install openai-whisper
pip install torch torchvision torchaudio
pip install ffmpeg-python
```

---

## 🎧 Instalar FFmpeg

### Windows

1. Baixe: [https://ffmpeg.org/download.html](https://ffmpeg.org/download.html)
2. Extraia
3. Adicione ao PATH:

```
C:\ffmpeg\bin
```

Teste:

```
ffmpeg -version
```

---

## ▶️ Como usar

1. Coloque o áudio em:

```
data/input/
```

2. Execute:

```
python main.py
```

3. Escolha:

* Modelo
* Idioma
* Formato
* CPU ou GPU

4. Resultado será salvo em:

```
data/output/
```

---

## ⚡ Uso com GPU (recomendado)

Verifique se possui GPU NVIDIA:

```
nvidia-smi
```

Instale PyTorch com CUDA:

```
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

Teste:

```
python -c "import torch; print(torch.cuda.is_available())"
```

---

## 🧠 Modelos Whisper

| Modelo | Velocidade   | Precisão   |
| ------ | ------------ | ---------- |
| tiny   | Muito rápido | Baixa      |
| base   | Rápido       | Média      |
| small  | Equilíbrio   | Boa        |
| medium | Lento        | Alta       |
| large  | Muito lento  | Muito alta |

---

## 🧹 Limpar modelos baixados

Os modelos ficam em:

```
C:\Users\SEU_USUARIO\.cache\whisper
```

Você pode deletar os arquivos `.pt` para liberar espaço.

---

## 📦 Gerar executável (.exe)

```
pip install pyinstaller
pyinstaller --onefile main.py
```

O executável ficará em:

```
dist/main.exe
```

---

## ⚠️ Problemas comuns

### Torch não funciona

* Reinstale:

```
pip uninstall torch -y
pip install torch
```

### GPU não detectada

* Verifique drivers
* Verifique CUDA compatível

### FFmpeg não encontrado

* Adicione ao PATH

---

## 📌 Próximas melhorias

* Interface gráfica
* Processamento em lote
* Barra de progresso
* Logs

---

## 👨‍💻 Autor

Projeto para estudo e uso prático de transcrição automática com IA.
