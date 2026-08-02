#!/usr/bin/env python3
"""Deterministic conformance checker for Open Knowledge Format (OKF) v0.2.

The checker performs local file I/O only. PyYAML must already be present in the
approved Python environment. It never installs packages or opens network
connections.

Run:
    python3 okf_validate.py <bundle-dir>
        [--strict | --max-warnings N] [--migrate] [--json]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path, PurePosixPath

try:
    import yaml
except ImportError:
    print(
        "error: PyYAML is required but is not installed in this Python environment. "
        "Use an internally approved environment or package source.",
        file=sys.stderr,
    )
    raise SystemExit(2)

OKF_VERSION = "0.2"
RESERVED = {"index.md", "log.md"}
RECOMMENDED = ("title", "description", "tags")
STATUS_VALUES = {"draft", "stable", "deprecated"}
ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
RFC3339 = re.compile(
    r"^\d{4}-\d{2}-\d{2}"
    r"(?:[Tt ]\d{2}:\d{2}(?::\d{2}(?:\.\d+)?)?(?:[Zz]|[+-]\d{2}:?\d{2})?)?$"
)
ACTOR_SHAPE = re.compile(r"^(?:[^\s:/]+:\S+|\S+/\S+)$")
ACTOR_HUMANISH = re.compile(r"^(?:human|process)(?![A-Za-z0-9_])", re.I)
LINK = re.compile(r"(?<!\!)\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
MD_LINK = re.compile(r"(?<!\!)\[([^\]]+)\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
FOOTNOTE = re.compile(r"\[\^([^\]\s]+)\]")
CITATIONS_HEADING = re.compile(r"^#{1,6}[ \t]+Citations[ \t]*$", re.M)
HEADING = re.compile(r"^#{1,6}[ \t]")
LOG_DATE = re.compile(r"^##[ \t]+(\d{4}-\d{2}-\d{2})[ \t]*$")
OKF_01_LINE = re.compile(r"^(okf_version:[ \t]*)[\"']?0\.1[\"']?[ \t]*$", re.M)
MIGRATE_ACTOR = "process:okf-migrate"


@dataclass
class Report:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    concepts: int = 0
    indexes: int = 0
    logs: int = 0

    def err(self, rel: str, message: str) -> None:
        self.errors.append(f"{rel}: {message}")

    def warn(self, rel: str, message: str) -> None:
        self.warnings.append(f"{rel}: {message}")


def read_text(path: Path, rel: str, report: Report) -> str | None:
    try:
        return path.read_text(encoding="utf-8").lstrip("\ufeff")
    except (UnicodeDecodeError, OSError) as exc:
        report.err(rel, f"cannot read file: {exc}")
        return None


def split_frontmatter(text: str) -> tuple[str | None, str]:
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        return None, text
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            return "".join(lines[1:index]), "".join(lines[index + 1 :])
    return None, text


def parse_meta(raw: str, rel: str, report: Report) -> dict | None:
    try:
        value = yaml.safe_load(raw)
    except yaml.YAMLError as exc:
        report.err(rel, f"§11.1 frontmatter is not valid YAML: {str(exc).replace(chr(10), ' ')}")
        return None
    if not isinstance(value, dict):
        report.err(rel, "§11.1 frontmatter must be a YAML mapping")
        return None
    return value


def check_actor(value, where: str, rel: str, report: Report) -> None:
    actor = str(value or "").strip()
    if not actor:
        return
    if ACTOR_HUMANISH.match(actor) and not actor.startswith(("human:", "process:")):
        report.warn(rel, f"§7 `{where}` `{actor}` is a near-miss of `human:`/`process:`; trust tiers depend on the exact lowercase prefix")
    elif not ACTOR_SHAPE.match(actor):
        report.warn(rel, f"§7 `{where}` `{actor}` matches no actor shape (`human:<id>`, `process:<id>`, or `<producer>/<version>`)")


def check_instant(value, where: str, rel: str, report: Report) -> None:
    if value is not None and not RFC3339.match(str(value).strip()):
        report.warn(rel, f"§5.2 `{where}` `{value}` is not an RFC 3339 timestamp")


def check_trust(meta: dict, rel: str, report: Report) -> None:
    generated = meta.get("generated")
    if generated is None:
        if "timestamp" in meta:
            report.warn(rel, "legacy v0.1 `timestamp`: v0.2 uses `generated: {by, at}` (§13.1)")
        else:
            report.warn(rel, "recommended field `generated` is absent (§5.2)")
    elif not isinstance(generated, dict):
        report.warn(rel, "§5.2 `generated` must be a mapping with `by` and `at`")
    elif not str(generated.get("by", "")).strip():
        report.warn(rel, "§5.2 `generated.by` is required within `generated`")
    else:
        check_actor(generated.get("by"), "generated.by", rel, report)
        check_instant(generated.get("at"), "generated.at", rel, report)

    verified = meta.get("verified")
    if verified is None:
        return
    entries = [verified] if isinstance(verified, dict) else verified
    if not isinstance(entries, list):
        report.warn(rel, "§5.2 `verified` must be a mapping or list of mappings")
        return
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict) or not str(entry.get("by", "")).strip():
            report.warn(rel, "§5.2 every `verified` entry needs a `by` actor")
            continue
        check_actor(entry.get("by"), f"verified[{index}].by", rel, report)
        check_instant(entry.get("at"), f"verified[{index}].at", rel, report)


def check_lifecycle(meta: dict, rel: str, report: Report) -> None:
    status = meta.get("status")
    if status is not None and status not in STATUS_VALUES:
        report.warn(rel, f"§5.4 unknown `status` `{status}`")
    stale_after = meta.get("stale_after")
    if stale_after is not None and not ISO_DATE.match(str(stale_after)):
        report.warn(rel, f"§5.5 `stale_after` `{stale_after}` is not YYYY-MM-DD")


def check_usage_window(window, where: str, rel: str, report: Report) -> None:
    if window is None:
        return
    if not isinstance(window, dict):
        report.warn(rel, f"§5.1 `{where}.usage_window` must be a mapping")
        return
    for bound in ("from", "to"):
        value = window.get(bound)
        if value is None:
            report.warn(rel, f"§5.1 `{where}.usage_window` is missing `{bound}`")
        elif not ISO_DATE.match(str(value)):
            report.warn(rel, f"§5.1 `{where}.usage_window.{bound}` is not YYYY-MM-DD")


def check_sources(meta: dict, body: str, rel: str, report: Report) -> None:
    if CITATIONS_HEADING.search(body):
        report.warn(rel, "legacy v0.1 `# Citations` section; v0.2 uses `sources` (§13.1)")
    sources = meta.get("sources")
    if sources is None:
        return
    if not isinstance(sources, list):
        report.warn(rel, "§5.1 `sources` must be a list")
        return

    ids: set[str] = set()
    for index, source in enumerate(sources):
        where = f"sources[{index}]"
        if not isinstance(source, dict):
            report.warn(rel, f"§5.1 `{where}` must be a mapping")
            continue
        source_id = str(source.get("id", "")).strip()
        resource = str(source.get("resource", "")).strip()
        if not source_id:
            report.warn(rel, f"§5.1 `{where}.id` is required")
        elif source_id in ids:
            report.warn(rel, f"§5.1 duplicate source id `{source_id}`")
        else:
            ids.add(source_id)
        if not resource:
            report.warn(rel, f"§5.1 `{where}.resource` is required")
        if source.get("author") is not None:
            check_actor(source.get("author"), f"{where}.author", rel, report)
        if source.get("usage_count") is not None:
            value = source.get("usage_count")
            if not isinstance(value, int) or value < 0:
                report.warn(rel, f"§5.1 `{where}.usage_count` must be a non-negative integer")
        check_usage_window(source.get("usage_window"), where, rel, report)

    for label in sorted(set(FOOTNOTE.findall(body))):
        if label not in ids:
            report.warn(rel, f"§5.1 footnote `^{label}` has no matching `sources[].id`")


def normalize_bundle_target(source_rel: str, target: str) -> str | None:
    target = target.split("#", 1)[0].split("?", 1)[0].strip()
    if not target or not target.endswith(".md"):
        return None
    source_parent = PurePosixPath(source_rel).parent
    candidate = PurePosixPath(target.lstrip("/")) if target.startswith("/") else source_parent / target
    parts: list[str] = []
    for part in candidate.parts:
        if part in ("", "."):
            continue
        if part == "..":
            if parts:
                parts.pop()
            continue
        parts.append(part)
    return PurePosixPath(*parts).as_posix()


def check_links(body: str, rel: str, known_files: set[str], report: Report) -> None:
    for target in LINK.findall(body):
        normalized = normalize_bundle_target(rel, target)
        if normalized and normalized not in known_files:
            report.warn(rel, f"§6.1 broken bundle link `{target}`")


def check_path_reference(value, where: str, path: Path, bundle: Path, rel: str, report: Report) -> None:
    if value is None:
        return
    target = str(value).strip()
    if not target or "://" in target or target.startswith("mailto:"):
        return
    candidate = bundle / target.lstrip("/") if target.startswith("/") else path.parent / target
    try:
        inside = candidate.resolve().is_relative_to(bundle.resolve())
    except OSError:
        inside = False
    if inside and not candidate.exists():
        report.warn(rel, f"§6.2 `{where}` points at `{target}`, which does not exist")


def check_computation(meta: dict, path: Path, bundle: Path, rel: str, report: Report) -> None:
    if not str(meta.get("runtime", "")).strip():
        report.warn(rel, "§10.2 an Attested Computation concept requires `runtime`")
    check_path_reference(meta.get("computation"), "computation", path, bundle, rel, report)
    for key in ("executor", "attester"):
        block = meta.get(key)
        if isinstance(block, dict):
            check_path_reference(block.get("resource"), f"{key}.resource", path, bundle, rel, report)


def check_concept(path: Path, rel: str, bundle: Path, known_files: set[str], report: Report) -> None:
    report.concepts += 1
    text = read_text(path, rel, report)
    if text is None:
        return
    raw, body = split_frontmatter(text)
    if raw is None:
        report.err(rel, "§11.1 no parseable YAML frontmatter block")
        return
    meta = parse_meta(raw, rel, report)
    if meta is None:
        return
    concept_type = meta.get("type")
    if not isinstance(concept_type, str) or not concept_type.strip():
        report.err(rel, "§11.2 missing or empty required `type` field")
    for key in RECOMMENDED:
        if key not in meta:
            report.warn(rel, f"recommended field `{key}` is absent (§4.1)")
    check_trust(meta, rel, report)
    check_lifecycle(meta, rel, report)
    check_sources(meta, body, rel, report)
    check_links(body, rel, known_files, report)
    if isinstance(concept_type, str) and concept_type.strip() == "Attested Computation":
        check_computation(meta, path, bundle, rel, report)


def check_index(path: Path, rel: str, is_root: bool, report: Report) -> None:
    report.indexes += 1
    text = read_text(path, rel, report)
    if text is None:
        return
    raw, body = split_frontmatter(text)
    if is_root:
        if raw is None:
            report.warn(rel, "§8.2 root index should declare `okf_version`")
        else:
            meta = parse_meta(raw, rel, report)
            if meta is None:
                return
            extra = sorted(set(meta) - {"okf_version"})
            if extra:
                report.warn(rel, f"§8.2 root index frontmatter contains extra keys: {', '.join(extra)}")
            if str(meta.get("okf_version", "")) != OKF_VERSION:
                report.warn(rel, f"§8.2 root index should declare okf_version {OKF_VERSION}")
    elif raw is not None:
        report.warn(rel, "§8.1 non-root index should not have frontmatter")
    if not any(HEADING.match(line) for line in body.splitlines()):
        report.warn(rel, "§8 index has no markdown heading")


def check_log(path: Path, rel: str, report: Report) -> None:
    report.logs += 1
    text = read_text(path, rel, report)
    if text is None:
        return
    raw, body = split_frontmatter(text)
    if raw is not None:
        report.warn(rel, "§9 log.md should not have frontmatter")
    dates: list[str] = []
    for line in body.splitlines():
        if line.startswith("##"):
            match = LOG_DATE.match(line)
            if not match:
                report.warn(rel, f"§9 log heading is not an ISO date: `{line.strip()}`")
            else:
                dates.append(match.group(1))
    if dates and dates != sorted(dates, reverse=True):
        report.warn(rel, "§9 log dates should be newest first")


def citations_section(text: str) -> tuple[str, list[dict]]:
    match = CITATIONS_HEADING.search(text)
    if not match:
        return text, []
    section_start = match.start()
    tail = text[match.end():]
    next_heading = re.search(r"^#{1,6}[ \t]+", tail, re.M)
    section_end = match.end() + (next_heading.start() if next_heading else len(tail))
    section = text[match.end():section_end]
    sources: list[dict] = []
    used_ids: set[str] = set()
    for index, link_match in enumerate(MD_LINK.finditer(section), start=1):
        title, resource = link_match.groups()
        base = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-") or f"source-{index}"
        source_id = base
        suffix = 2
        while source_id in used_ids:
            source_id = f"{base}-{suffix}"
            suffix += 1
        used_ids.add(source_id)
        sources.append({"id": source_id, "resource": resource, "title": title})
    if not sources:
        return text, []
    replacement = text[:section_start].rstrip() + "\n\n" + text[section_end:].lstrip()
    return replacement, sources


def migrate_file(path: Path, is_root_index: bool = False) -> bool:
    text = path.read_text(encoding="utf-8").lstrip("\ufeff")
    changed = False
    if is_root_index:
        updated = OKF_01_LINE.sub(rf'\g<1>"{OKF_VERSION}"', text)
        if updated != text:
            text = updated
            changed = True
        path.write_text(text, encoding="utf-8")
        return changed

    raw, body = split_frontmatter(text)
    if raw is None:
        return False
    meta = yaml.safe_load(raw) or {}
    if not isinstance(meta, dict):
        return False

    if "timestamp" in meta and "generated" not in meta:
        timestamp = meta.pop("timestamp")
        meta["generated"] = {"by": MIGRATE_ACTOR, "at": timestamp}
        changed = True

    new_body, migrated_sources = citations_section(body)
    if migrated_sources:
        existing = meta.get("sources")
        if not isinstance(existing, list):
            existing = []
        existing_ids = {str(item.get("id")) for item in existing if isinstance(item, dict)}
        for source in migrated_sources:
            if source["id"] not in existing_ids:
                existing.append(source)
        meta["sources"] = existing
        body = new_body
        changed = True

    if changed:
        rendered = yaml.safe_dump(meta, sort_keys=False, allow_unicode=True)
        path.write_text(f"---\n{rendered}---\n{body}", encoding="utf-8")
    return changed


def migrate_bundle(bundle: Path) -> list[str]:
    changed: list[str] = []
    for path in sorted(bundle.rglob("*.md")):
        rel = path.relative_to(bundle).as_posix()
        if migrate_file(path, is_root_index=(rel == "index.md")):
            changed.append(rel)
    return changed


def validate_bundle(bundle: Path) -> Report:
    report = Report()
    paths = sorted(bundle.rglob("*.md"))
    known_files = {path.relative_to(bundle).as_posix() for path in paths}
    for path in paths:
        rel = path.relative_to(bundle).as_posix()
        if path.name == "index.md":
            check_index(path, rel, rel == "index.md", report)
        elif path.name == "log.md":
            check_log(path, rel, report)
        else:
            check_concept(path, rel, bundle, known_files, report)
    if not paths:
        report.warn(".", "bundle contains no markdown files")
    return report


def print_report(report: Report, as_json: bool, migrated: list[str]) -> None:
    if as_json:
        payload = asdict(report)
        payload["migrated"] = migrated
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return
    for message in report.errors:
        print(f"ERROR {message}")
    for message in report.warnings:
        print(f"warn  {message}")
    if migrated:
        print(f"migrated {len(migrated)} file(s): {', '.join(migrated)}")
    print(f"checked {report.concepts} concept(s), {report.indexes} index(es), {report.logs} log(s): {len(report.errors)} error(s), {len(report.warnings)} warning(s)")


def main() -> int:
    parser = argparse.ArgumentParser(description=f"Validate an OKF v{OKF_VERSION} bundle.")
    parser.add_argument("bundle", nargs="?", type=Path, default=Path(".okf"))
    gate = parser.add_mutually_exclusive_group()
    gate.add_argument("--strict", action="store_true", help="fail when any warning is present")
    gate.add_argument("--max-warnings", type=int, default=None, metavar="N")
    parser.add_argument("--migrate", action="store_true", help="rewrite supported v0.1 constructs before validation")
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    args = parser.parse_args()

    bundle = args.bundle.resolve()
    if not bundle.is_dir():
        print(f"error: bundle directory does not exist: {bundle}", file=sys.stderr)
        return 2
    if args.max_warnings is not None and args.max_warnings < 0:
        print("error: --max-warnings must be non-negative", file=sys.stderr)
        return 2

    migrated = migrate_bundle(bundle) if args.migrate else []
    report = validate_bundle(bundle)
    print_report(report, args.json, migrated)

    if report.errors:
        return 1
    allowed = 0 if args.strict else args.max_warnings
    if allowed is not None and len(report.warnings) > allowed:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
