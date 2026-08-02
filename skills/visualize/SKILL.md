---
name: visualize
description: >-
  Render an Open Knowledge Format (OKF) bundle as a single self-contained,
  interactive offline HTML graph (viz.html) — concepts as nodes, markdown links
  and bundle-internal sources as edges, directory clustering for large bundles,
  zoom/pan/fit controls, adaptive labels, group/type filters, search, and a
  wiki-style detail panel with OKF trust/lifecycle/provenance metadata and
  backlinks. Use when asked to visualize, graph, preview, or explore an OKF bundle.
user-invocable: true
argument-hint: "[bundle-dir] [-o viz.html]"
allowed-tools: Bash
---

# Visualize an OKF bundle

Generate a fully offline, self-contained interactive HTML graph of the target
bundle (default `.okf/`). No backend, remote browser assets, package download,
or network request is used when generating or opening the file.

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/okf_visualize.py" $ARGUMENTS
```

The approved Python environment must already contain PyYAML. This skill never
runs a package manager or downloads dependencies.

The visualizer includes:

- wheel and pinch zoom
- pointer-drag panning
- zoom in/out, Fit, and Reset controls
- directory-cluster, grid, concentric, and radial layouts
- directory-group and type filters
- free-text search over IDs, titles, descriptions, tags, types, and groups
- adaptive labels that appear as the user zooms in
- click-to-inspect and double-click-to-focus behavior
- `Links to` and `Cited by` navigation
- rendered Markdown and OKF lifecycle, trust, provenance, and source metadata

Large bundles default to `cluster`, which places each concept at a distinct
coordinate inside its parent-directory group instead of squeezing everything
into a fixed-size circle. Clicking a group label filters and fits that group.
Use `--layout grid`, `--layout concentric`, or `--layout cose` to override.
`--max-nodes N` refuses oversized bundles when an internal policy needs a cap.

The detail panel shows `status`, `generated`, `verified`, `stale_after`,
`sources`, tags, body content, outgoing links, and backlinks. Trust tier and
staleness are derived advisory signals, not access-control decisions.

The output defaults to `<bundle>/viz.html`; pass `-o <path>` to write elsewhere.
The generated file embeds all CSS and JavaScript. Opening it does not request
CDN assets or send bundle data anywhere.
