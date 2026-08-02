#!/usr/bin/env python3
"""Render an OKF bundle as a single offline HTML graph.

This company-safe variant performs local file processing only. It does not use
HTTP clients, fetch remote assets, import browser packages, or generate external
script/style references. The resulting HTML uses only embedded CSS and vanilla
JavaScript.

PyYAML must already be available in the approved Python environment.

Run:
    python3 okf_visualize.py <bundle-dir> [-o viz.html]
        [--layout cose|concentric|grid] [--max-nodes N]
"""
from __future__ import annotations

import argparse
import html
import json
import re
import sys
from datetime import date
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

RESERVED = {"index.md", "log.md"}
LINK_RE = re.compile(r"(?<!\!)\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
HTML_TEMPLATE = r'''<style>
:root {
  color-scheme: light dark;
  --bg: #f6f7f9;
  --panel: #ffffff;
  --text: #1f2937;
  --muted: #667085;
  --line: #d0d5dd;
  --accent: #3b6fd8;
  --accent-soft: #e8eefc;
  --danger-soft: #fbe9e7;
}
@media (prefers-color-scheme: dark) {
  :root {
    --bg: #111318;
    --panel: #191c23;
    --text: #e5e7eb;
    --muted: #9aa4b2;
    --line: #303642;
    --accent: #8ab4ff;
    --accent-soft: #202d49;
    --danger-soft: #3a2222;
  }
}
* { box-sizing: border-box; }
html, body { margin: 0; height: 100%; background: var(--bg); color: var(--text); font: 14px/1.5 system-ui, sans-serif; }
.app { min-height: 100%; display: grid; grid-template-rows: auto 1fr; }
.toolbar { display: flex; flex-wrap: wrap; gap: 10px; align-items: end; padding: 12px; border-bottom: 1px solid var(--line); background: var(--panel); }
.toolbar label { display: grid; gap: 4px; color: var(--muted); font-size: 12px; }
.toolbar input, .toolbar select { min-width: 160px; border: 1px solid var(--line); border-radius: 8px; padding: 8px 10px; background: var(--panel); color: var(--text); }
.summary { margin-left: auto; color: var(--muted); }
.workspace { min-height: 0; display: grid; grid-template-columns: minmax(0, 1fr) minmax(300px, 38%); }
.graph-wrap { min-height: 640px; overflow: hidden; position: relative; }
svg { width: 100%; height: 100%; min-height: 640px; display: block; }
.edge { stroke: var(--line); stroke-width: 1.2; opacity: .8; }
.node circle { fill: var(--panel); stroke: var(--accent); stroke-width: 2; cursor: pointer; }
.node text { fill: var(--text); font-size: 11px; pointer-events: none; }
.node.selected circle { fill: var(--accent-soft); stroke-width: 4; }
.panel { overflow: auto; border-left: 1px solid var(--line); background: var(--panel); padding: 18px; }
.panel h1 { margin: 0 0 6px; font-size: 22px; }
.panel h2 { margin-top: 22px; font-size: 16px; }
.meta { display: grid; grid-template-columns: max-content 1fr; gap: 5px 12px; margin: 14px 0; }
.meta dt { color: var(--muted); }
.meta dd { margin: 0; overflow-wrap: anywhere; }
.badges { display: flex; flex-wrap: wrap; gap: 6px; margin: 10px 0; }
.badge { border: 1px solid var(--line); border-radius: 999px; padding: 2px 8px; font-size: 12px; }
.badge.accent { border-color: var(--accent); background: var(--accent-soft); }
.badge.stale { background: var(--danger-soft); }
.body { overflow-wrap: anywhere; }
.body pre { overflow: auto; border: 1px solid var(--line); border-radius: 8px; padding: 10px; background: var(--bg); }
.body code { background: var(--bg); border-radius: 4px; padding: 1px 4px; }
.body table { border-collapse: collapse; max-width: 100%; }
.body th, .body td { border: 1px solid var(--line); padding: 5px 8px; }
.link-list { padding-left: 18px; }
.empty { color: var(--muted); padding: 28px; }
@media (max-width: 800px) {
  .workspace { grid-template-columns: 1fr; }
  .panel { border-left: 0; border-top: 1px solid var(--line); }
  .summary { width: 100%; margin-left: 0; }
}
</style>
<div class="app">
  <div class="toolbar">
    <label>Search<input id="search" type="search" placeholder="Title, type, path"></label>
    <label>Type<select id="type"><option value="">All types</option></select></label>
    <label>Layout<select id="layout"><option value="cose">Radial</option><option value="concentric">Concentric</option><option value="grid">Grid</option></select></label>
    <div class="summary" id="summary"></div>
  </div>
  <div class="workspace">
    <div class="graph-wrap"><svg id="graph" viewBox="0 0 1000 700" role="img" aria-label="OKF concept graph"></svg></div>
    <aside class="panel" id="panel"><div class="empty">Select a concept.</div></aside>
  </div>
</div>
<script>
const DATA = __DATA__;
const state = { selected: null, query: "", type: "", layout: "__LAYOUT__" };
const svg = document.getElementById("graph");
const panel = document.getElementById("panel");
const search = document.getElementById("search");
const typeSelect = document.getElementById("type");
const layoutSelect = document.getElementById("layout");
const summary = document.getElementById("summary");
layoutSelect.value = state.layout;

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function inlineMarkdown(text) {
  let out = escapeHtml(text);
  out = out.replace(/`([^`]+)`/g, "<code>$1</code>");
  out = out.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
  out = out.replace(/\*([^*]+)\*/g, "<em>$1</em>");
  out = out.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<span title="$2">$1</span>');
  return out;
}

function renderMarkdown(markdown) {
  const lines = String(markdown || "").split(/\r?\n/);
  const output = [];
  let inCode = false;
  let code = [];
  let inList = false;
  let inTable = false;
  for (const raw of lines) {
    const line = raw.replace(/\s+$/, "");
    if (/^(```|~~~)/.test(line)) {
      if (inCode) {
        output.push("<pre><code>" + escapeHtml(code.join("\n")) + "</code></pre>");
        code = [];
      }
      inCode = !inCode;
      continue;
    }
    if (inCode) { code.push(raw); continue; }
    if (/^\s*[-*]\s+/.test(line)) {
      if (!inList) { output.push("<ul>"); inList = true; }
      output.push("<li>" + inlineMarkdown(line.replace(/^\s*[-*]\s+/, "")) + "</li>");
      continue;
    }
    if (inList) { output.push("</ul>"); inList = false; }
    if (/^\|.*\|$/.test(line)) {
      const cells = line.slice(1, -1).split("|").map(c => c.trim());
      if (cells.every(c => /^:?-{3,}:?$/.test(c))) continue;
      if (!inTable) { output.push("<table>"); inTable = true; }
      output.push("<tr>" + cells.map(c => "<td>" + inlineMarkdown(c) + "</td>").join("") + "</tr>");
      continue;
    }
    if (inTable) { output.push("</table>"); inTable = false; }
    const heading = line.match(/^(#{1,6})\s+(.*)$/);
    if (heading) {
      const level = heading[1].length;
      output.push("<h" + level + ">" + inlineMarkdown(heading[2]) + "</h" + level + ">");
    } else if (!line.trim()) {
      output.push("");
    } else {
      output.push("<p>" + inlineMarkdown(line) + "</p>");
    }
  }
  if (inList) output.push("</ul>");
  if (inTable) output.push("</table>");
  if (inCode) output.push("<pre><code>" + escapeHtml(code.join("\n")) + "</code></pre>");
  return output.join("\n");
}

function positions(nodes, layout) {
  const map = new Map();
  const count = Math.max(nodes.length, 1);
  if (layout === "grid") {
    const columns = Math.ceil(Math.sqrt(count));
    const rows = Math.ceil(count / columns);
    nodes.forEach((node, index) => {
      const col = index % columns;
      const row = Math.floor(index / columns);
      map.set(node.id, { x: 100 + col * (800 / Math.max(columns - 1, 1)), y: 90 + row * (520 / Math.max(rows - 1, 1)) });
    });
    return map;
  }
  const byType = new Map();
  for (const node of nodes) {
    if (!byType.has(node.type)) byType.set(node.type, []);
    byType.get(node.type).push(node);
  }
  if (layout === "concentric") {
    const groups = [...byType.values()];
    groups.forEach((group, ringIndex) => {
      const radius = 100 + ringIndex * Math.min(95, 360 / Math.max(groups.length, 1));
      group.forEach((node, index) => {
        const angle = (Math.PI * 2 * index / Math.max(group.length, 1)) - Math.PI / 2;
        map.set(node.id, { x: 500 + Math.cos(angle) * radius, y: 350 + Math.sin(angle) * radius });
      });
    });
    return map;
  }
  nodes.forEach((node, index) => {
    const angle = (Math.PI * 2 * index / count) - Math.PI / 2;
    const radius = Math.min(285, 150 + count * 3);
    map.set(node.id, { x: 500 + Math.cos(angle) * radius, y: 350 + Math.sin(angle) * radius });
  });
  return map;
}

function visibleNodes() {
  const q = state.query.trim().toLowerCase();
  return DATA.nodes.filter(node => {
    const matchesType = !state.type || node.type === state.type;
    const haystack = [node.id, node.title, node.type, node.description, ...(node.tags || [])].join(" ").toLowerCase();
    return matchesType && (!q || haystack.includes(q));
  });
}

function renderGraph() {
  const nodes = visibleNodes();
  const visible = new Set(nodes.map(n => n.id));
  const pos = positions(nodes, state.layout);
  svg.replaceChildren();
  for (const edge of DATA.edges) {
    if (!visible.has(edge.source) || !visible.has(edge.target)) continue;
    const a = pos.get(edge.source);
    const b = pos.get(edge.target);
    const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
    line.setAttribute("x1", a.x);
    line.setAttribute("y1", a.y);
    line.setAttribute("x2", b.x);
    line.setAttribute("y2", b.y);
    line.setAttribute("class", "edge");
    svg.appendChild(line);
  }
  for (const node of nodes) {
    const p = pos.get(node.id);
    const group = document.createElementNS("http://www.w3.org/2000/svg", "g");
    group.setAttribute("class", "node" + (state.selected === node.id ? " selected" : ""));
    group.setAttribute("transform", `translate(${p.x} ${p.y})`);
    const circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
    circle.setAttribute("r", Math.max(18, Math.min(32, 18 + (node.degree || 0) * 1.5)));
    const label = document.createElementNS("http://www.w3.org/2000/svg", "text");
    label.setAttribute("text-anchor", "middle");
    label.setAttribute("dy", "45");
    label.textContent = node.title.length > 28 ? node.title.slice(0, 27) + "…" : node.title;
    group.append(circle, label);
    group.addEventListener("click", () => selectNode(node.id));
    svg.appendChild(group);
  }
  summary.textContent = `${nodes.length} / ${DATA.nodes.length} concepts · ${DATA.edges.length} relationships`;
}

function trustTier(node) {
  const entries = Array.isArray(node.verified) ? node.verified : (node.verified ? [node.verified] : []);
  if (!entries.length) return "unverified";
  return entries.some(item => String(item?.by || "").startsWith("human:")) ? "human-reviewed" : "machine-confirmed";
}
function stale(node) { return Boolean(node.stale_after && node.stale_after <= DATA.today); }
function listLinks(ids) {
  if (!ids.length) return '<span class="empty">None</span>';
  return '<ul class="link-list">' + ids.map(id => {
    const target = DATA.nodeById[id];
    return `<li><button type="button" data-open="${escapeHtml(id)}">${escapeHtml(target?.title || id)}</button></li>`;
  }).join("") + "</ul>";
}
function selectNode(id) {
  state.selected = id;
  const node = DATA.nodeById[id];
  if (!node) return;
  const tier = trustTier(node);
  const isStale = stale(node);
  panel.innerHTML = `
    <h1>${escapeHtml(node.title)}</h1>
    <div>${escapeHtml(node.id)}</div>
    <div class="badges">
      <span class="badge accent">${escapeHtml(node.type)}</span>
      <span class="badge">${escapeHtml(node.status || "stable")}</span>
      <span class="badge">${escapeHtml(tier)}</span>
      ${isStale ? '<span class="badge stale">stale</span>' : ""}
    </div>
    <p>${escapeHtml(node.description || "")}</p>
    <dl class="meta">
      <dt>Generated</dt><dd>${escapeHtml(JSON.stringify(node.generated || node.timestamp || ""))}</dd>
      <dt>Verified</dt><dd>${escapeHtml(JSON.stringify(node.verified || ""))}</dd>
      <dt>Stale after</dt><dd>${escapeHtml(node.stale_after || "")}</dd>
      <dt>Tags</dt><dd>${escapeHtml((node.tags || []).join(", "))}</dd>
      <dt>Sources</dt><dd>${escapeHtml(JSON.stringify(node.sources || []))}</dd>
    </dl>
    <h2>Links to</h2>${listLinks(node.links_to || [])}
    <h2>Cited by</h2>${listLinks(node.cited_by || [])}
    <h2>Content</h2>
    <div class="body">${renderMarkdown(node.body)}</div>`;
  panel.querySelectorAll("[data-open]").forEach(button => button.addEventListener("click", () => selectNode(button.dataset.open)));
  renderGraph();
}
for (const type of DATA.types) {
  const option = document.createElement("option");
  option.value = type;
  option.textContent = type;
  typeSelect.appendChild(option);
}
search.addEventListener("input", () => { state.query = search.value; renderGraph(); });
typeSelect.addEventListener("change", () => { state.type = typeSelect.value; renderGraph(); });
layoutSelect.addEventListener("change", () => { state.layout = layoutSelect.value; renderGraph(); });
renderGraph();
if (DATA.nodes.length) selectNode(DATA.nodes[0].id);
</script>
'''


def split_frontmatter(text: str) -> tuple[dict, str]:
    if not text.startswith("---"):
        return {}, text
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        return {}, text
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            raw = "".join(lines[1:index])
            body = "".join(lines[index + 1 :])
            try:
                meta = yaml.safe_load(raw) or {}
            except yaml.YAMLError:
                return {}, body
            return meta if isinstance(meta, dict) else {}, body
    return {}, text


def normalize_target(source_id: str, target: str, known: set[str]) -> str | None:
    target = target.split("#", 1)[0].split("?", 1)[0].strip()
    if not target or not target.endswith(".md"):
        return None
    source_parent = PurePosixPath(source_id).parent
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
    normalized = PurePosixPath(*parts).as_posix()
    return normalized if normalized in known else None


def trust_tier(verified) -> str:
    entries = verified if isinstance(verified, list) else ([verified] if isinstance(verified, dict) else [])
    if not entries:
        return "unverified"
    return "human-reviewed" if any(str(item.get("by", "")).startswith("human:") for item in entries if isinstance(item, dict)) else "machine-confirmed"


def load_bundle(bundle: Path, max_nodes: int | None) -> dict:
    records: list[dict] = []
    for path in sorted(bundle.rglob("*.md")):
        if path.name in RESERVED:
            continue
        rel = path.relative_to(bundle).as_posix()
        try:
            text = path.read_text(encoding="utf-8").lstrip("\ufeff")
        except (OSError, UnicodeDecodeError) as exc:
            print(f"warning: skipping {rel}: {exc}", file=sys.stderr)
            continue
        meta, body = split_frontmatter(text)
        records.append({
            "id": rel,
            "title": str(meta.get("title") or path.stem.replace("-", " ").replace("_", " ").title()),
            "type": str(meta.get("type") or "Unknown"),
            "description": str(meta.get("description") or ""),
            "tags": meta.get("tags") if isinstance(meta.get("tags"), list) else [],
            "status": str(meta.get("status") or "stable"),
            "stale_after": str(meta.get("stale_after") or ""),
            "generated": meta.get("generated"),
            "timestamp": meta.get("timestamp"),
            "verified": meta.get("verified"),
            "sources": meta.get("sources") if isinstance(meta.get("sources"), list) else [],
            "body": body,
            "_raw_links": LINK_RE.findall(body),
        })
    if max_nodes is not None and len(records) > max_nodes:
        raise ValueError(f"bundle contains {len(records)} concepts, above --max-nodes {max_nodes}")
    known = {record["id"] for record in records}
    edges: set[tuple[str, str, str]] = set()
    for record in records:
        for target in record.pop("_raw_links"):
            normalized = normalize_target(record["id"], target, known)
            if normalized:
                edges.add((record["id"], normalized, "link"))
        for source in record["sources"]:
            if isinstance(source, dict):
                normalized = normalize_target(record["id"], str(source.get("resource") or ""), known)
                if normalized:
                    edges.add((record["id"], normalized, "source"))
    outgoing: dict[str, set[str]] = {node_id: set() for node_id in known}
    incoming: dict[str, set[str]] = {node_id: set() for node_id in known}
    for source, target, _kind in edges:
        outgoing[source].add(target)
        incoming[target].add(source)
    for record in records:
        record["links_to"] = sorted(outgoing[record["id"]])
        record["cited_by"] = sorted(incoming[record["id"]])
        record["degree"] = len(outgoing[record["id"]]) + len(incoming[record["id"]])
        record["trust_tier"] = trust_tier(record["verified"])
    return {
        "nodes": records,
        "edges": [{"source": s, "target": t, "kind": k} for s, t, k in sorted(edges)],
        "nodeById": {record["id"]: record for record in records},
        "types": sorted({record["type"] for record in records}),
        "today": date.today().isoformat(),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Render an OKF bundle as an offline HTML graph.")
    parser.add_argument("bundle", nargs="?", type=Path, default=Path(".okf"))
    parser.add_argument("-o", "--output", type=Path, default=None)
    parser.add_argument("--layout", choices=("cose", "concentric", "grid"), default=None)
    parser.add_argument("--max-nodes", type=int, default=None)
    args = parser.parse_args()
    bundle = args.bundle.resolve()
    if not bundle.is_dir():
        print(f"error: bundle directory does not exist: {bundle}", file=sys.stderr)
        return 2
    try:
        data = load_bundle(bundle, args.max_nodes)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    layout = args.layout or ("concentric" if len(data["nodes"]) > 1000 else "cose")
    output = args.output or (bundle / "viz.html")
    payload = json.dumps(data, ensure_ascii=False, default=str).replace("</", "<\\/")
    document = HTML_TEMPLATE.replace("__DATA__", payload).replace("__LAYOUT__", html.escape(layout))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(document, encoding="utf-8")
    print(f"wrote offline OKF visualization to {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
