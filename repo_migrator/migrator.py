"""Orquestra a migração de um repositório (single-branch ou all-branches) para o destino."""

from . import git_ops
from .naming import resolve_branch_name

DEFAULT_TARGET = "FatecAcademy/SchoolProjects"


def migrate(url, base_dir, target, all_branches=False):
    name = git_ops.repo_name_from_url(url)
    dest_dir = base_dir / name
    target_url = git_ops.target_url_from(target)

    remote_branches = git_ops.list_remote_branches(url)
    multi_branch = len(remote_branches) > 1

    if multi_branch and not all_branches:
        print(
            f"[{name}] aviso: repositório tem {len(remote_branches)} branches "
            f"({', '.join(remote_branches)}), mas apenas a branch atual será migrada. "
            f"Use --all-branches para migrar todas.\n"
        )

    if multi_branch and all_branches:
        _migrate_all_branches(url, dest_dir, target_url, remote_branches, name)
        return

    _migrate_single_branch(url, dest_dir, base_dir, target_url, name, target)


def _migrate_single_branch(url, dest_dir, base_dir, target_url, name, target):
    if dest_dir.exists():
        print(f"[{name}] pasta já existe em {dest_dir}, pulando clone.")
    else:
        git_ops.clone(url, into_dir=base_dir)

    git_ops.set_remote_url(dest_dir, target_url)

    current = git_ops.current_branch(dest_dir)
    own_sha = git_ops.rev_parse(dest_dir, current)

    existing = git_ops.list_remote_branch_shas(target_url)
    final_name = resolve_branch_name(name, existing, own_sha, name)
    if final_name != name:
        print(
            f"[{name}] aviso: já existe uma branch '{name}' no destino com histórico "
            f"diferente. Usando '{final_name}' para evitar sobrescrita.\n"
        )

    if current != final_name:
        git_ops.rename_branch(dest_dir, current, final_name)

    git_ops.push_branch(dest_dir, final_name)
    print(f"[{name}] migrado com sucesso para {target} (branch '{final_name}').\n")


def _migrate_all_branches(url, dest_dir, target_url, remote_branches, name):
    mirror_dir = dest_dir.parent / f"{dest_dir.name}-mirror"

    if mirror_dir.exists():
        print(f"[{name}] mirror já existe em {mirror_dir}, pulando clone.")
    else:
        git_ops.clone(url, into_dir=dest_dir.parent, mirror=True, dest_name=mirror_dir.name)

    git_ops.prepare_mirror_for_push(mirror_dir, target_url)

    existing = git_ops.list_remote_branch_shas(target_url)
    renamed = []
    refspecs = []
    for branch in remote_branches:
        own_sha = git_ops.rev_parse(mirror_dir, f"refs/heads/{branch}")
        final_name = resolve_branch_name(branch, existing, own_sha, name)
        if final_name != branch:
            renamed.append((branch, final_name))
        refspecs.append(f"refs/heads/{branch}:refs/heads/{final_name}")

    if renamed:
        print(f"[{name}] branches renomeadas por colisão de nome no destino:")
        for old, new in renamed:
            print(f"    {old} -> {new}")

    git_ops.push_refspecs(mirror_dir, refspecs)

    print(
        f"[{name}] {len(remote_branches)} branches migradas com sucesso "
        f"({', '.join(remote_branches)}).\n"
    )
