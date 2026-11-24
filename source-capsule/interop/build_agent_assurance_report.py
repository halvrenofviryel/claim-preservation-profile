"""Build a bounded cross-format report from exact Inspect and Promptfoo bytes."""

from __future__ import annotations

import argparse
import glob
import json
from pathlib import Path

from cpp_source_capsule.adapters import inspect_ai, promptfoo
from cpp_source_capsule.core import build_capsule, verify_capsule

PROFILE_FILES = {
    "ignored-stop": "agent-ignored-stop.json",
    "false-send-claim": "agent-false-send.json",
    "missing-effect-observer": "agent-missing-observer.json",
}
CURRENT_REVISION = "claim-commons-local/synthetic-email-agent-v2"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def one_format(
    *,
    profile: dict,
    source_path: Path,
    source_format: str,
) -> dict:
    source_bytes = source_path.read_bytes()
    adapter = inspect_ai if source_format == "inspect-ai-v2" else promptfoo
    selection, measurement, source_binding, mapping_loss = adapter.admit(
        source_bytes,
        profile["selector"],
    )
    capsule = build_capsule(
        profile,
        source_format=source_format,
        source_ref=source_path.name,
        source_bytes=source_bytes,
        adapter_version=adapter.ADAPTER_VERSION,
        selection=selection,
        measurement=measurement,
        source_binding=source_binding,
        mapping_loss=mapping_loss,
    )
    recorded = verify_capsule(capsule, source_bytes=source_bytes)
    changed = verify_capsule(
        capsule,
        source_bytes=source_bytes,
        current_subject_revision=CURRENT_REVISION,
    )
    return {
        "source": capsule["source"],
        "source_binding": capsule["source_binding"],
        "measurement": capsule["measurement"],
        "recorded_assessment": recorded["recorded_assessment"],
        "source_derived_valid": recorded["valid"],
        "changed_revision_applicability": changed["current_applicability"],
        "verification_limit": recorded["limitation"],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--inspect-dir", required=True, type=Path)
    parser.add_argument("--promptfoo", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()

    inspect_matches = sorted(glob.glob(str(args.inspect_dir / "*.json")))
    if len(inspect_matches) != 1:
        raise SystemExit("Expected exactly one Inspect JSON log")
    inspect_path = Path(inspect_matches[0])
    profiles = Path(__file__).resolve().parents[1] / "fixtures" / "profiles"
    cases = []
    for case_id, profile_file in PROFILE_FILES.items():
        profile = load_json(profiles / profile_file)
        cases.append(
            {
                "case_id": case_id,
                "claim": profile["claim"],
                "inspect": one_format(
                    profile=profile,
                    source_path=inspect_path,
                    source_format="inspect-ai-v2",
                ),
                "promptfoo": one_format(
                    profile=profile,
                    source_path=args.promptfoo,
                    source_format="promptfoo-jsonl",
                ),
            }
        )
    report = {
        "report_version": "1",
        "recorded_subject_revision": "claim-commons-local/synthetic-email-agent-v1",
        "changed_subject_revision": CURRENT_REVISION,
        "cases": cases,
        "scope_limit": (
            "Three deterministic synthetic cases and two version-pinned source formats; "
            "not general agent safety, semantic truth, source independence, or external reproduction."
        ),
    }
    args.out.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
