"""Testes do contrato central de linhagem de artefatos."""

from artifact_lineage import get_all_dependents, get_direct_dependents


def test_profile_invalida_derivados_esperados():
    assert get_all_dependents("profile") == {
        "jobs",
        "courses",
        "match",
        "reconciliation",
        "tailoring",
        "pdi",
        "interview",
    }


def test_resume_invalida_derivados_esperados():
    assert get_all_dependents("resume") == {
        "match",
        "reconciliation",
        "tailoring",
        "pdi",
        "interview",
    }


def test_job_description_invalida_derivados_esperados():
    assert get_all_dependents("job_description") == {
        "match",
        "reconciliation",
        "tailoring",
        "pdi",
        "interview",
    }


def test_match_invalida_derivados_esperados():
    assert get_all_dependents("match") == {
        "reconciliation",
        "tailoring",
        "pdi",
        "interview",
    }


def test_focus_invalida_derivados_esperados():
    assert get_all_dependents("focus") == {
        "reconciliation",
        "tailoring",
        "pdi",
        "interview",
    }


def test_tailoring_invalida_pdi():
    assert get_direct_dependents("tailoring") == {"pdi"}
    assert get_all_dependents("tailoring") == {"pdi"}


def test_unknown_artifact_returns_empty_set():
    assert get_direct_dependents("unknown") == set()
    assert get_all_dependents("unknown") == set()


def test_transitive_dependencies_do_not_duplicate_results():
    dependents = get_all_dependents("resume")

    assert len(dependents) == 5
    assert dependents == get_direct_dependents("resume")
