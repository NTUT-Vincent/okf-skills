---
name: visualize
description: >-
  Render an Open Knowledge Format (OKF) bundle as a single self-contained,
  interactive HTML graph (viz.html) — concepts as nodes coloured/sized by type,
  markdown links and bundle-internal `sources` as edges, a wiki-style detail panel
  with rendered markdown, v0.2 trust/lifecycle/provenance metadata, and "Links to"
  / "Cited by" backlinks, layout switching, per-type filter and search.
  Use when asked to visualize, graph, preview, or explore an OKF bundle.
user-invocable: true
argument-hint: "[bundle-dir] [-o viz.html]"
allowed-tools: Bash
---

# Visualize an OKF bundle

Generate a fully offline, self-contained HTML graph of the target bundle
(default the project's `.okf/`). No backend, no install on the viewing side, no
remote browser assets, and no data leaves the page.

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/okf_visualize.py" $ARGUMENTS
```

The approved Python environment must already contain PyYAML. This skill never
runs a package manager or downloads dependencies.

The detail panel shows each concept's `status`, `generated`, `verified`,
`stale_after`, and `sources` (with their credibility signals, a `usage_count`
alongside the `usage_window` that frames it); a `sources` entry pointing at
another concept in the bundle also becomes a graph edge. A v0.1 `timestamp` is
read as `generated.at`, so legacy bundles still render fully.

Two badges are **derived**, not read: the §5.3 trust tier
(*unverified* / *machine-confirmed* / *human-reviewed*, keyed off the `human:`
prefix in `verified[].by`) and staleness (`today >= stale_after`). They are
advisory signals — when reporting on a bundle, say which tier a concept is in
rather than treating any of them as a gate.

The output defaults to `<bundle>/viz.html`. Pass `-o <path>` to write elsewhere.
Bundles above 1,000 concepts default to the linear `concentric` layout, while
`--layout cose` and `--layout grid` remain available. `--max-nodes N` refuses
oversized bundles, e.g. for controlled internal use.

The generated file embeds its CSS, graph renderer, markdown renderer, filtering,
search, and detail-panel logic. Opening it does not request CDN assets.
