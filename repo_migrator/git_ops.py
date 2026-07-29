"""Wrappers de baixo nível sobre comandos git. Nenhuma lógica de migração aqui."""

import subprocess
from urllib.parse import urlparse


def run(cmd, cwd=None):
    print(f"$ {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cwd)
    if result.returncode != 0:
        raise RuntimeError(f"Comando falhou ({result.returncode}): {' '.join(cmd)}")


def capture(cmd, cwd=None):
    return subprocess.run(
        cmd, cwd=cwd, capture_output=True, text=True, check=True,
    ).stdout.strip()


def repo_name_from_url(url):
    path = urlparse(url).path
    name = path.rstrip("/").rsplit("/", 1)[-1]
    if name.endswith(".git"):
        name = name[:-4]
    return name


def normalize_target(target):
    """Aceita tanto 'org/repo' quanto uma URL completa do GitHub."""
    target = target.strip().rstrip("/")
    if target.startswith("http://") or target.startswith("https://"):
        path = urlparse(target).path.strip("/")
        if path.endswith(".git"):
            path = path[:-4]
        return path
    return target


def target_url_from(target):
    return f"https://github.com/{normalize_target(target)}.git"


def _parse_heads(ls_remote_output):
    prefix = "refs/heads/"
    for line in ls_remote_output.splitlines():
        line = line.strip()
        if not line:
            continue
        sha, ref = line.split("\t", 1)
        if ref.startswith(prefix):
            yield ref[len(prefix):], sha


def list_remote_branches(url):
    """Retorna a lista de branches remotas de um repositório."""
    output = capture(["git", "ls-remote", "--heads", url])
    return [name for name, _sha in _parse_heads(output)]


def list_remote_branch_shas(url):
    """Retorna {nome_da_branch: sha} para as branches existentes em um repositório."""
    output = capture(["git", "ls-remote", "--heads", url])
    return dict(_parse_heads(output))


def current_branch(repo_dir):
    return capture(["git", "branch", "--show-current"], cwd=repo_dir)


def rev_parse(repo_dir, ref):
    return capture(["git", "rev-parse", ref], cwd=repo_dir)


def clone(url, into_dir, mirror=False, dest_name=None):
    """Clona 'url' dentro de 'into_dir'. Se 'dest_name' for dado, esse é o nome final
    da pasta clonada (equivalente a 'git clone url dest_name')."""
    cmd = ["git", "clone"]
    if mirror:
        cmd.append("--mirror")
    cmd.append(url)
    if dest_name:
        cmd.append(dest_name)
    run(cmd, cwd=into_dir)


def set_remote_url(repo_dir, remote_url):
    run(["git", "remote", "set-url", "origin", remote_url], cwd=repo_dir)


def rename_branch(repo_dir, old_name, new_name):
    run(["git", "branch", "-m", old_name, new_name], cwd=repo_dir)


def push_branch(repo_dir, branch_name):
    run(["git", "push", "-u", "origin", branch_name], cwd=repo_dir)


def push_refspecs(repo_dir, refspecs):
    run(["git", "push", "origin", *refspecs], cwd=repo_dir)


def prepare_mirror_for_push(mirror_dir, target_url):
    """Um clone --mirror recusa refspecs customizados; isso desfaz o modo mirror."""
    run(["git", "config", "--unset", "remote.origin.mirror"], cwd=mirror_dir)
    run(
        ["git", "config", "remote.origin.fetch", "+refs/heads/*:refs/remotes/origin/*"],
        cwd=mirror_dir,
    )
    set_remote_url(mirror_dir, target_url)
