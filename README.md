# repo-migrator

Ferramenta de linha de comando para migrar repositórios GitHub inteiros (histórico
completo, uma ou várias branches) para dentro de um único repositório de destino,
cada projeto de origem virando uma branch própria.

Caso de uso: consolidar vários repositórios pessoais/de aula em um único
repositório de organização (`FatecAcademy/SchoolProjects`), sem perder commits,
sem sobrescrever branches já migradas, e sem repetir os comandos git manualmente
para cada repositório.

## Uso rápido

```bash
# Modo interativo (sem argumentos)
python migrate_repos.py

# Uma ou mais URLs direto na linha de comando
python migrate_repos.py https://github.com/user/RepoA https://github.com/user/RepoB

# Lista de URLs em arquivo (uma por linha, "#" comenta)
python migrate_repos.py --file repos.txt

# Repositório com múltiplas branches: leva todas, com nomes originais
python migrate_repos.py https://github.com/user/RepoMultiBranch --all-branches

# Destino e pasta de clone customizados
python migrate_repos.py --file repos.txt --target OutraOrg/OutroRepo --dir C:\tmp\migracao
```

Sem argumentos, o script cai no menu interativo: pede as URLs, o repositório de
destino, a pasta de clone, verifica quantas branches cada repositório tem e
pergunta (por repositório) se as múltiplas branches devem ser todas migradas —
depois mostra um resumo e pede confirmação antes de tocar em qualquer remoto.

## O que o script faz, por repositório

1. Clona o repositório de origem (ou reaproveita a pasta se já existir localmente).
2. Consulta as branches do repositório de origem (`git ls-remote --heads`).
3. **Se só há uma branch**: renomeia a branch local para o nome do repositório
   e dá push para o destino.
4. **Se há várias branches e `--all-branches` foi pedido**: clona em modo
   `--mirror` e envia todas as branches de uma vez (`git push origin
   refs/heads/*:refs/heads/*`), preservando os nomes originais.
5. **Antes de qualquer push**, verifica se o nome de branch já existe no
   destino. Se existir apontando para o *mesmo* commit, reaproveita (rodar de
   novo é seguro). Se existir apontando para um commit *diferente* — ou seja,
   pertence a outro projeto —, prefixa automaticamente o nome com o nome do
   repositório de origem (`main` → `MeuRepo-main`) em vez de arriscar
   sobrescrever histórico alheio.

Nenhum passo usa `--force`. Uma colisão de nome sempre resulta em renomeação
automática, nunca em sobrescrita silenciosa.

## Arquitetura

```
migrate_repos.py          ponto de entrada fino: chama repo_migrator.cli.main()

repo_migrator/
├── git_ops.py             wrappers sobre comandos git (clone, push, ls-remote, rev-parse...)
│                           não conhece a lógica de migração, só executa comandos
├── naming.py               resolve_branch_name(): decide se reaproveita ou prefixa
│                           um nome de branch — função pura, sem I/O, fácil de testar
├── migrator.py             orquestra: decide clone simples vs. mirror,
│                           chama git_ops + naming, imprime o progresso
├── menu.py                  modo interativo: prompts, resumo, confirmação
└── cli.py                   argparse, modo não-interativo, decide se cai no menu
```

Fluxo de dependências (sempre em uma direção, sem ciclos):

```
cli.py ──┬──> menu.py ──> migrator.py ──┬──> git_ops.py
         │                              └──> naming.py
         └──> migrator.py
```

- **`git_ops`** é a única camada que roda `subprocess`. Se um dia trocar de
  biblioteca git (ex: GitPython), só esse arquivo muda.
- **`naming`** não importa nada do resto do pacote — é lógica pura
  (`dict in, string out`), o que facilita testar a regra de colisão de nomes
  isoladamente.
- **`migrator`** é o único módulo que sabe orquestrar "single branch" vs.
  "all branches"; tanto `cli` quanto `menu` chamam a mesma função `migrate()`,
  então o comportamento de push é idêntico nos dois modos de uso.
- **`cli`** e **`menu`** são as duas "portas de entrada" (não-interativa e
  interativa) — nenhuma lógica de git mora nelas.

## Requisitos

- Python 3.8+
- `git` disponível no PATH e autenticado (SSH ou credential helper) com
  permissão de push no repositório de destino.
