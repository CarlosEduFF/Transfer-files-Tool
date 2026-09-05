# ProcessMonitor

Monitor de processos para Windows, com gráficos de CPU/RAM em tempo real, mapa das
portas em escuta e inventário das linguagens de programação instaladas.

Interface em PyQt6, com três telas na barra lateral.

## Telas

### Monitor

Gráficos de CPU e RAM com um minuto de histórico e a lista de processos, separada
em abas por tipo — **Aplicativos**, **Processos em segundo plano** e **Processos do
Windows**, além de **Todos**.

Cada linha traz PID, nome do executável, descrição (o nome legível que o Windows
guarda no arquivo, o mesmo que o Gerenciador de Tarefas mostra), CPU%, memória,
usuário e status, com o ícone do programa.

A busca filtra por nome **ou** descrição: procurar por `spooler` encontra o
`spoolsv.exe`.

Encerrar um processo passa por três camadas de proteção: processos críticos do
Windows são recusados, a confirmação mostra os dados e tem "Não" como padrão, e o
encerramento tenta `terminate()` antes de `kill()`.

### Ports

Portas TCP e UDP em escuta, com o processo que ocupa cada uma. Responde à pergunta
"quem está usando a porta 8080?", que aparece toda vez que um servidor local não
sobe por conflito de porta.

Portas de serviços conhecidos são identificadas (PostgreSQL, MySQL, Redis, Vite,
Flask...), e o botão **Liberar porta** encerra o processo dono, com as mesmas
proteções da tela Monitor.

### Toolchains

Linguagens e SDKs instalados, com versão e caminho: Python, Node.js, Java, .NET, Go,
Rust, Flutter, Dart, Kotlin, PHP, Ruby, Perl, Deno, Bun, Git, GCC, Gradle, Maven e as
ferramentas do Android SDK (adb, emulator, cmdline-tools).

Ferramentas instaladas mas **fora do PATH** — caso comum do Android SDK e do Kotlin
do Android Studio — são localizadas assim mesmo e sinalizadas, porque "não instalado"
e "instalado mas invisível ao terminal" pedem ações diferentes.

Para as linguagens com gerenciador de pacotes (pip, npm, gem, cargo, pub, composer),
lista os pacotes instalados e permite desinstalá-los. A confirmação mostra o comando
exato que será executado antes de rodar.

## Requisitos

Windows e Python 3.10+.

```bash
pip install -r requirements.txt
```

## Uso

```bash
python src/main.py
```

## Notas de implementação

**A varredura de processos é feita em lotes.** Ler CPU, memória e status dos ~270
processos de uma vez custa cerca de 1,2 s nesta classe de máquina — no Windows cada
um desses campos abre um handle por processo (medido: `status` 1177 ms,
`memory_info` 534 ms, `cpu_percent` 521 ms). Como a coleta roda em `QThread` mas o
GIL continua sendo disputado, esse bloco contínuo travava a interface e a rolagem da
tabela. O sampler relê apenas 15 processos por ciclo, em rodízio, e devolve o GIL a
cada 25 ms de trabalho; o custo por ciclo cai para ~100 ms. Em troca, CPU% e memória
de um processo são renovados a cada ~17 s.

**Nome, usuário, descrição e ícone são resolvidos uma vez só.** São imutáveis durante
a vida do processo, e a descrição e o ícone são cacheados por caminho de executável —
os 88 `svchost.exe` desta máquina compartilham uma leitura.

**A tabela atualiza sem perder seleção nem rolagem.** O modelo casa as linhas por PID
e emite uma única notificação de mudança por ciclo; `beginResetModel` a cada segundo
jogaria a rolagem para o topo e limparia a seleção.

**O ícone da barra de tarefas é aplicado pelo Win32.** O Qt define o ícone da janela,
mas não o da classe da janela (`GCLP_HICON`) — e é esse que o shell do Windows usa
para uma `QMainWindow`. Sem `SetClassLongPtr`, a barra de título mostrava o ícone
correto e a barra de tarefas mostrava o genérico.

## Estrutura

```
src/
  main.py               ponto de entrada, ícone e AppUserModelID
  window.py             janela, navegação e ações
  sampler.py            coleta em thread de fundo
  models.py             modelo da tabela de processos
  categorias.py         classificação em app / segundo plano / sistema
  charts.py             gráficos de CPU e RAM
  ports.py              portas em escuta
  ports_model.py        modelo da tabela de portas
  toolchains.py         detecção de linguagens e pacotes
  toolchains_worker.py  threads das operações lentas
  packages_model.py     modelo da tabela de pacotes
  winmeta.py            descrição do executável (version.dll)
  winicon.py            ícone da janela no nível do Win32
tools/
  gerar_icone.py        gera Icon.ico a partir de Icon.png
```
