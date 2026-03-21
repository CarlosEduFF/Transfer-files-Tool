# 📦 Mode RGH MD

Script em Python para alternar automaticamente entre dois modos:

* **Modo Instalar**
* **Modo Reverter**

Ele organiza pastas e arquivos entre os diretórios **Crack**, **Smart TV** e a **raiz do projeto**, garantindo que pastas com o mesmo nome (como `Content`) **não sejam misturadas**. 

---

🎮 Objetivo

Com este script, você pode alternar facilmente entre:

Jogar com mídias originais
Utilizar o desbloqueio RGH no Xbox 360

Tudo isso de forma automática, segura e sem risco de sobrescrever arquivos.

---

## 🚀 Como funciona

### ▶️ Modo Instalar

Executado quando a pasta `Crack` **não está vazia**.

**Passos:**

1. Move a pasta `Content` da raiz → `Smart TV`

   * Não mistura com outra `Content` existente
   * Renomeia automaticamente se necessário (`Content_1`, etc.)

2. Move todos os arquivos e pastas de `Crack` → raiz

   * Inclui outra possível pasta `Content`

---

### 🔄 Modo Reverter

Executado quando a pasta `Crack` **está vazia**.

**Passos:**

1. Move todos os arquivos da raiz → `Crack`

   * Ignora arquivos do sistema e do próprio script

2. Move a pasta `Content` de `Smart TV` → raiz

   * Prioriza `Content_1`, `Content_2`, etc. (instaladas anteriormente)

---

## 📁 Estrutura esperada

```
/projeto
│
├── Crack/
├── Smart TV/
├── Content/
├── main.py
```

---

## ▶️ Como executar

### Usando Python:

```
python main.py
```

### Usando executável (.exe):

Basta executar o arquivo:

```
main.exe
```

---

## ⚠️ Regras importantes

* Pastas `Content` **nunca são mescladas**
* Arquivos existentes **não são sobrescritos**
* Nomes duplicados são ajustados automaticamente:

  ```
  Content → Content_1 → Content_2
  ```
* O script decide automaticamente qual modo executar

---

## 🧠 Lógica de decisão

| Condição             | Modo     |
| -------------------- | -------- |
| `Crack` vazio        | Reverter |
| `Crack` com arquivos | Instalar |

---

## 📌 Observações

* Compatível com execução via `.exe` (PyInstaller)
* Evita perda de dados
* Estrutura modular (helpers + modes)

---

Projeto desenvolvido para automação de organização de arquivos.
