"""Project real-tool logs into the reviewed public fixture field allowlist.

Raw logs remain local because framework stack traces and environment metadata can
contain absolute paths.  The normalized files retain every field admitted by the
agent-claim adapters and are therefore independently source-derived by the CLI.
"""

from __future__ import annotations

import argparse
import glob
import json
from pathlib import Path
from typing import Any


INSPECT_METADATA_FIELDS = (
    "case_id",
    "claim",
    "stop_received",
    "pending_send_executed",
    "effect_observer_available",
    "outbox_before",
    "outbox_after",
)
PROMPTFOO_METADATA_FIELDS = (
    "subjectRevision",
    "caseId",
    "claim",
    "stopReceived",
    "pendingSendExecuted",
    "effectObserverAvailable",
    "outboxBefore",
    "outboxAfter",
)


def selected(source: dict[str, Any], names: tuple[str, ...]) -> dict[str, Any]:
    return {name: source.get(name) for name in names}


def first_line(value: Any) -> str:
    return str(value or "").splitlines()[0]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--inspect-dir", required=True, type=Path)
    parser.add_argument("--promptfoo", required=True, type=Path)
    parser.add_argument("--inspect-out", required=True, type=Path)
    parser.add_argument("--promptfoo-out", required=True, type=Path)
    args = parser.parse_args()

    inspect_matches = sorted(glob.glob(str(args.inspect_dir / "*.json")))
    if len(inspect_matches) != 1:
        raise SystemExit("Expected exactly one Inspect JSON log")
    inspect = json.loads(Path(inspect_matches[0]).read_text(encoding="utf-8"))
    inspect_public = {
        "status": inspect.get("status"),
        "eval": {"model": inspect.get("eval", {}).get("model")},
        "samples": [
            {"metadata": selected(sample.get("metadata", {}), INSPECT_METADATA_FIELDS)}
            for sample in inspect.get("samples", [])
            if isinstance(sample, dict) and isinstance(sample.get("metadata"), dict)
        ],
    }
    args.inspect_out.write_text(
        json.dumps(inspect_public, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    rows = [
        json.loads(line)
        for line in args.promptfoo.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    public_rows = []
    for row in rows:
        grading = row.get("gradingResult")
        metadata = row.get("response", {}).get("metadata", {})
        public_rows.append(
            {
                "error": first_line(row.get("error")),
                "gradingResult": {
                    "pass": grading.get("pass") if isinstance(grading, dict) else None,
                    "reason": first_line(grading.get("reason")) if isinstance(grading, dict) else "",
                    "score": grading.get("score") if isinstance(grading, dict) else None,
                },
                "response": {
                    "output": row.get("response", {}).get("output"),
                    "metadata": selected(metadata, PROMPTFOO_METADATA_FIELDS),
                },
                "score": row.get("score"),
                "success": row.get("success"),
            }
        )
    args.promptfoo_out.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in public_rows),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
