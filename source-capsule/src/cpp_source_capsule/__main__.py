"""Command-line interface for the CPP source-capsule module."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .adapters import admit_source, inspect_ai, promptfoo
from .core import build_capsule, verify_capsule


def _load_json(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _write_json(value: dict, path: str | None) -> None:
    text = json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if path:
        Path(path).write_text(text, encoding="utf-8")
    else:
        print(text, end="")


def main() -> None:
    parser = argparse.ArgumentParser(prog="cpp-source-capsule")
    sub = parser.add_subparsers(dest="command", required=True)

    importer = sub.add_parser("import", help="build a capsule from an admitted source format")
    importer.add_argument("--format", choices=("inspect-ai-v2", "promptfoo-jsonl"), required=True)
    importer.add_argument("--profile", required=True)
    importer.add_argument("--source", required=True)
    importer.add_argument("--out")

    verifier = sub.add_parser("verify", help="verify capsule and optional source bytes")
    verifier.add_argument("--capsule", required=True)
    verifier.add_argument("--source")
    verifier.add_argument("--current-subject-revision")

    args = parser.parse_args()
    if args.command == "import":
        profile = _load_json(args.profile)
        source_bytes = Path(args.source).read_bytes()
        selector = profile.get("selector", {})
        adapter = inspect_ai if args.format == "inspect-ai-v2" else promptfoo
        selection, measurement, source_binding, mapping_loss = admit_source(
            args.format,
            source_bytes,
            selector,
            adapter_version=adapter.ADAPTER_VERSION,
        )
        capsule = build_capsule(
            profile,
            source_format=args.format,
            source_ref=Path(args.source).name,
            source_bytes=source_bytes,
            adapter_version=adapter.ADAPTER_VERSION,
            selection=selection,
            measurement=measurement,
            source_binding=source_binding,
            mapping_loss=mapping_loss,
        )
        _write_json(capsule, args.out)
        return

    capsule = _load_json(args.capsule)
    source_bytes = Path(args.source).read_bytes() if args.source else None
    result = verify_capsule(
        capsule,
        source_bytes=source_bytes,
        current_subject_revision=args.current_subject_revision,
    )
    _write_json(result, None)
    raise SystemExit(0 if result["valid"] else 1)


if __name__ == "__main__":
    main()
