"""Regras de resolução de nomes de branch — puras, sem I/O."""


def resolve_branch_name(desired_name, existing_target_shas, own_sha, repo_prefix):
    """Evita colidir com uma branch já existente no destino que aponte para outro histórico.

    Se 'desired_name' já existe no destino apontando para o mesmo commit, reaproveita
    (idempotente). Se aponta para um commit diferente, prefixa com o nome do repositório.
    """
    existing_sha = existing_target_shas.get(desired_name)
    if existing_sha is None or existing_sha == own_sha:
        return desired_name
    return f"{repo_prefix}-{desired_name}"
