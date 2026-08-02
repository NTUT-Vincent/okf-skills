#!/usr/bin/env python3
"""Scaffold a conformant starter Open Knowledge Format (OKF) v0.2 bundle.

Creates a root `index.md`, a `log.md`, and one starter concept. This company-safe
variant uses only the Python standard library and performs local file I/O only.

Run: python3 scripts/okf_init.py <target-dir> [--title "..."] [--force]
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

OKF_VERSION = "0.2"
STARTER_CONCEPT = "getting-started.md"
ACTOR = "process:okf_init"


def humanize(name: str) -> str:
    words = name.replace("-", " ").replace("_", " ").strip()
    return words.title() if words else "Untitled"


def yaml_string(value: str) -> str:
    """JSON strings are valid YAML scalars and avoid a YAML runtime dependency."""
    return json.dumps(value, ensure_ascii=False)


def build_index(title: str) -> str:
    return (
        "---\n"
        f"okf_version: {yaml_string(OKF_VERSION)}\n"
        "---\n\n"
        f"# {title}\n\n"
        f"* [Getting started]({STARTER_CONCEPT}) - starting point for this bundle.\n"
    )


def build_log(today: str, title: str) -> str:
    return (
        "# Update Log\n\n"
        f"## {today}\n"
        f"* **Creation**: Scaffolded the {title} bundle with `okf_init.py` — "
        f"see [getting started]({STARTER_CONCEPT}).\n"
    )


def build_concept(title: str, now_iso: str) -> str:
    return (
        "---\n"
        "type: Reference\n"
        f"title: {yaml_string(f'Getting started — {title}')}\n"
        f"description: {yaml_string(f'Starting point for the {title} OKF bundle.')}\n"
        "tags:\n"
        "  - getting-started\n"
        "status: stable\n"
        "generated:\n"
        f"  by: {yaml_string(ACTOR)}\n"
        f"  at: {yaml_string(now_iso)}\n"
        "---\n\n"
        "# Overview\n\n"
        "This is the first concept in a freshly scaffolded OKF bundle. Replace "
        "it with real knowledge — one concept per file, cross-linked with "
        "standard markdown links — and keep `index.md` and `log.md` updated as "
        "you go.\n"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=f"Scaffold a starter OKF v{OKF_VERSION} bundle.")
    parser.add_argument("target", type=Path, help="directory to create the bundle in")
    parser.add_argument("--title", default=None, help="bundle title (default: humanized target dir name)")
    parser.add_argument("--force", action="store_true", help="scaffold even if the target already has .md files")
    args = parser.parse_args()

    if args.target.exists() and not args.target.is_dir():
        print(f"error: {args.target} exists and is not a directory", file=sys.stderr)
        return 2

    existing_md = list(args.target.rglob("*.md")) if args.target.is_dir() else []
    if existing_md and not args.force:
        print(f"refusing: {args.target} already contains .md files (pass --force to scaffold anyway)", file=sys.stderr)
        for path in sorted(existing_md)[:5]:
            print(f"  {path.relative_to(args.target)}", file=sys.stderr)
        return 1

    title = args.title or humanize(args.target.resolve().name)
    today = datetime.now(timezone.utc).date().isoformat()
    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    args.target.mkdir(parents=True, exist_ok=True)
    (args.target / "index.md").write_text(build_index(title), encoding="utf-8")
    (args.target / "log.md").write_text(build_log(today, title), encoding="utf-8")
    (args.target / STARTER_CONCEPT).write_text(build_concept(title, now_iso), encoding="utf-8")

    validator = Path(__file__).resolve().parents[2] / "validate" / "scripts" / "okf_validate.py"
    print(f"created OKF bundle scaffold at {args.target}")
    print(f"hint: validate it — python3 {validator} {args.target} --strict")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
