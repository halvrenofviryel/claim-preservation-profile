"""Pins the audit basis and its load-bearing narrowing conclusions."""

from __future__ import annotations


def test_cross_project_audit_pins_every_authoritative_source(repo_root):
    text = (repo_root / "research" / "CROSS_PROJECT_CONSISTENCY_AUDIT.md").read_text(
        encoding="utf-8"
    )
    expected = {
        "https://github.com/halvrenofviryel/ai-runtime-evidence-protocol":
            "039dbcb22d4b53bb5714877dce65ff15372c49bd",
        "https://github.com/halvrenofviryel/measurement-axioms":
            "ea672f3918c53ac9ad22ad72d0b0a5d70a9a59ce",
        "https://github.com/halvrenofviryel/phionyx-research":
            "30e7bcf019b580bf2123955acb256e4894df24a2",
    }
    for repository, commit in expected.items():
        assert repository in text
        assert commit in text
    assert "draft/published/01/draft-abak-agent-control-delivery-evidence-01.txt" in text
    assert "Audit date: **2026-09-14**" in text


def test_audit_records_required_classifications_and_corrections(repo_root):
    text = (repo_root / "research" / "CROSS_PROJECT_CONSISTENCY_AUDIT.md").read_text(
        encoding="utf-8"
    )
    assert text.count("**Classification:** `SUPPORTED`.") >= 10
    assert text.count("**Classification:** `SUPPORTED_WITH_NARROWING`.") >= 4
    assert text.count("**Classification:** `UNSUPPORTED`.") == 3
    assert "No claim is classified `NOT_VERIFIED` after correction" in text
    assert "working-group review, adoption, consensus, and endorsement" in text


def test_current_profile_uses_the_narrowed_relationship_language(spec_text):
    assert "draws on four bodies of prior Phionyx work" in spec_text
    assert "generalizes four previously separate" not in spec_text
    assert "individual Informational Internet-Draft" in spec_text
    assert "does not define CPP's observer-validity" in spec_text
