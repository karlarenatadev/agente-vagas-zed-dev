"""Contrato central de dependências entre artefatos."""

from __future__ import annotations


DEPENDENCY_GRAPH: dict[str, frozenset[str]] = {
    "profile": frozenset(
        {
            "jobs",
            "courses",
            "match",
            "reconciliation",
            "tailoring",
            "pdi",
            "interview",
        }
    ),
    "resume": frozenset(
        {
            "match",
            "reconciliation",
            "tailoring",
            "pdi",
            "interview",
        }
    ),
    "job_description": frozenset(
        {
            "match",
            "reconciliation",
            "tailoring",
            "pdi",
            "interview",
        }
    ),
    "match": frozenset(
        {
            "reconciliation",
            "tailoring",
            "pdi",
            "interview",
        }
    ),
    "focus": frozenset(
        {
            "reconciliation",
            "tailoring",
            "pdi",
            "interview",
        }
    ),
    "tailoring": frozenset({"pdi"}),
}


def get_direct_dependents(artifact_name: str) -> set[str]:
    """Retorna uma cópia dos dependentes diretos conhecidos."""
    return set(DEPENDENCY_GRAPH.get(artifact_name, ()))


def get_all_dependents(artifact_name: str) -> set[str]:
    """Percorre o grafo e retorna dependentes transitivos sem duplicatas."""
    dependents: set[str] = set()
    pending = list(get_direct_dependents(artifact_name))

    while pending:
        dependent = pending.pop()
        if dependent in dependents:
            continue
        dependents.add(dependent)
        pending.extend(get_direct_dependents(dependent))

    return dependents
