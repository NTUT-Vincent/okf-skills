#!/usr/bin/env python3
"""Render an OKF bundle as a single offline interactive HTML graph.

This company-safe visualizer performs local file processing only. It does not
use HTTP clients, remote assets, browser packages, or external script/style
references. The generated HTML contains embedded CSS and vanilla JavaScript.

Large bundles use a directory-cluster layout with a virtual coordinate space,
zoom/pan, fit controls, adaptive labels, search focus, and group filtering.
PyYAML must already be available in the approved Python environment.

Run:
    python3 okf_visualize.py <bundle-dir> [-o viz.html]
        [--layout cluster|grid|concentric|cose] [--max-nodes N]
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
BODY_LIMIT = 8000

HTML_TEMPLATE = r'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>OKF visualization</title>
<style>
:root {
  color-scheme: light dark;
  --bg: #f6f7f9;
  --panel: #ffffff;
  --text: #1f2937;
  --muted: #667085;
  --line: #d0d5dd;
  --accent: #3b6fd8;
  --accent-soft: #e8eefc;
  --group-fill: rgba(59,111,216,.045);
  --group-line: rgba(59,111,216,.30);
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
    --group-fill: rgba(138,180,255,.045);
    --group-line: rgba(138,180,255,.28);
    --danger-soft: #3a2222;
  }
}
* { box-sizing: border-box; }
html, body { margin: 0; height: 100%; overflow: hidden; background: var(--bg); color: var(--text); font: 14px/1.5 system-ui, sans-serif; }
button, input, select { font: inherit; }
.app { height: 100%; display: grid; grid-template-rows: auto minmax(0, 1fr); }
.toolbar {
  display: flex; flex-wrap: wrap; gap: 8px; align-items: end; padding: 10px 12px;
  border-bottom: 1px solid var(--line); background: var(--panel); z-index: 3;
}
.toolbar label { display: grid; gap: 3px; color: var(--muted); font-size: 12px; }
.toolbar input, .toolbar select, .toolbar button {
  min-height: 36px; border: 1px solid var(--line); border-radius: 8px;
  padding: 7px 10px; background: var(--panel); color: var(--text);
}
.toolbar input { width: min(290px, 42vw); }
.toolbar select { max-width: 240px; }
.toolbar button { cursor: pointer; min-width: 38px; }
.toolbar button:hover { border-color: var(--accent); }
.zoom-controls { display: flex; gap: 5px; }
.summary { margin-left: auto; color: var(--muted); white-space: nowrap; align-self: center; }
.workspace { min-height: 0; display: grid; grid-template-columns: minmax(0, 1fr) minmax(310px, 36%); }
.graph-wrap { min-height: 0; overflow: hidden; position: relative; background: var(--bg); }
svg { width: 100%; height: 100%; display: block; touch-action: none; user-select: none; cursor: grab; }
svg.dragging { cursor: grabbing; }
.group-box { fill: var(--group-fill); stroke: var(--group-line); stroke-width: 1.5; vector-effect: non-scaling-stroke; }
.group-label { fill: var(--muted); font-size: 15px; font-weight: 600; cursor: pointer; }
.edge { stroke: var(--line); stroke-width: 1.25; opacity: .70; vector-effect: non-scaling-stroke; }
.node circle { fill: var(--panel); stroke: var(--accent); stroke-width: 2; vector-effect: non-scaling-stroke; cursor: pointer; }
.node text { fill: var(--text); font-size: 11px; pointer-events: none; paint-order: stroke; stroke: var(--bg); stroke-width: 3px; stroke-linejoin: round; }
.node.selected circle { fill: var(--accent-soft); stroke-width: 4; }
.node.related circle { stroke-width: 3; }
.node.dim { opacity: .18; }
.node-label.hidden { display: none; }
.graph-hint {
  position: absolute; left: 12px; bottom: 10px; padding: 5px 8px; border-radius: 7px;
  color: var(--muted); background: color-mix(in srgb, var(--panel) 88%, transparent);
  border: 1px solid var(--line); pointer-events: none; font-size: 12px;
}
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
.body table { border-collapse: collapse; max-width: 100%; display: block; overflow: auto; }
.body th, .body td { border: 1px solid var(--line); padding: 5px 8px; }
.link-list { padding-left: 18px; }
.link-list button { border: 0; padding: 2px 0; background: transparent; color: var(--accent); cursor: pointer; text-align: left; }
.empty { color: var(--muted); padding: 28px; }
@media (max-width: 820px) {
  html, body { overflow: auto; }
  .app { height: auto; min-height: 100%; }
  .workspace { grid-template-columns: 1fr; }
  .graph-wrap { height: 68vh; min-height: 480px; }
  .panel { border-left: 0; border-top: 1px solid var(--line); max-height: none; }
  .summary { width: 100%; margin-left: 0; }
}
</style>
</head>
<body>
<div class="app">
  <div class="toolbar">
    <label>Search<input id="search" type="search" placeholder="Title, type, path, tag"></label>
    <label>Type<select id="type"><option value="">All types</option></select></label>
    <label>Group<select id="group"><option value="">All groups</option></select></label>
    <label>Layout<select id="layout">
      <option value="cluster">Directory clusters</option>
      <option value="grid">Grid</option>
      <option value="concentric">Concentric by type</option>
      <option value="cose">Radial rings</option>
    </select></label>
    <div class="zoom-controls" aria-label="Graph view controls">
      <button id="zoom-out" type="button" title="Zoom out">−</button>
      <button id="zoom-in" type="button" title="Zoom in">+</button>
      <button id="fit" type="button">Fit</button>
      <button id="reset" type="button">Reset</button>
    </div>
    <div class="summary" id="summary" aria-live="polite"></div>
  </div>
  <div class="workspace">
    <div class="graph-wrap" id="graph-wrap">
      <svg id="graph" viewBox="0 0 1000 700" role="img" aria-label="Interactive OKF concept graph">
        <g id="viewport">
          <g id="groups-layer"></g>
          <g id="edges-layer"></g>
          <g id="nodes-layer"></g>
        </g>
      </svg>
      <div class="graph-hint">Wheel/pinch to zoom · drag to pan · double-click to fit</div>
    </div>
    <aside class="panel" id="panel"><div class="empty">Select a concept.</div></aside>
  </div>
</div>
<script>
const DATA = __DATA__;
const SVG_NS = "http:" + "//www.w3.org/2000/svg";
const state = {
  selected: null,
  query: "",
  type: "",
  group: "",
  layout: "__LAYOUT__",
  view: { x: 0, y: 0, k: 1 },
  bounds: { minX: 0, minY: 0, maxX: 1000, maxY: 700 },
  positions: new Map(),
  visibleIds: new Set(),
};
const svg = document.getElementById("graph");
const graphWrap = document.getElementById("graph-wrap");
const viewport = document.getElementById("viewport");
const groupsLayer = document.getElementById("groups-layer");
const edgesLayer = document.getElementById("edges-layer");
const nodesLayer = document.getElementById("nodes-layer");
const panel = document.getElementById("panel");
const search = document.getElementById("search");
const typeSelect = document.getElementById("type");
const groupSelect = document.getElementById("group");
const layoutSelect = document.getElementById("layout");
const summary = document.getElementById("summary");
const nodeElements = new Map();
const labelElements = new Map();
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

function visibleNodes() {
  const q = state.query.trim().toLowerCase();
  return DATA.nodes.filter(node => {
    const matchesType = !state.type || node.type === state.type;
    const matchesGroup = !state.group || node.group === state.group;
    const haystack = [node.id, node.title, node.type, node.group, node.description, ...(node.tags || [])].join(" ").toLowerCase();
    return matchesType && matchesGroup && (!q || haystack.includes(q));
  });
}

function finishLayout(positions, groups = []) {
  if (!positions.size) {
    return { positions, groups, bounds: { minX: 0, minY: 0, maxX: 1000, maxY: 700 } };
  }
  let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
  for (const point of positions.values()) {
    minX = Math.min(minX, point.x - 42);
    minY = Math.min(minY, point.y - 42);
    maxX = Math.max(maxX, point.x + 42);
    maxY = Math.max(maxY, point.y + 58);
  }
  for (const group of groups) {
    minX = Math.min(minX, group.x);
    minY = Math.min(minY, group.y);
    maxX = Math.max(maxX, group.x + group.width);
    maxY = Math.max(maxY, group.y + group.height);
  }
  return { positions, groups, bounds: { minX, minY, maxX, maxY } };
}

function gridLayout(nodes) {
  const positions = new Map();
  const spacingX = 100;
  const spacingY = 88;
  const columns = Math.max(1, Math.ceil(Math.sqrt(nodes.length)));
  nodes.forEach((node, index) => {
    positions.set(node.id, {
      x: 60 + (index % columns) * spacingX,
      y: 60 + Math.floor(index / columns) * spacingY,
    });
  });
  return finishLayout(positions);
}

function clusterLayout(nodes) {
  const byGroup = new Map();
  for (const node of nodes) {
    if (!byGroup.has(node.group)) byGroup.set(node.group, []);
    byGroup.get(node.group).push(node);
  }
  const specs = [...byGroup.entries()].map(([name, members]) => {
    members.sort((a, b) => a.title.localeCompare(b.title));
    const columns = Math.max(1, Math.ceil(Math.sqrt(members.length)));
    const rows = Math.max(1, Math.ceil(members.length / columns));
    return {
      name, members, columns, rows,
      width: Math.max(230, columns * 92 + 70),
      height: Math.max(150, rows * 82 + 90),
    };
  }).sort((a, b) => b.members.length - a.members.length || a.name.localeCompare(b.name));

  const totalArea = specs.reduce((sum, spec) => sum + spec.width * spec.height, 0);
  const targetWidth = Math.max(900, Math.sqrt(totalArea) * 1.30);
  const positions = new Map();
  const groups = [];
  let cursorX = 30;
  let cursorY = 30;
  let rowHeight = 0;

  for (const spec of specs) {
    if (cursorX > 30 && cursorX + spec.width > targetWidth) {
      cursorX = 30;
      cursorY += rowHeight + 34;
      rowHeight = 0;
    }
    groups.push({ name: spec.name, x: cursorX, y: cursorY, width: spec.width, height: spec.height, count: spec.members.length });
    spec.members.forEach((node, index) => {
      positions.set(node.id, {
        x: cursorX + 58 + (index % spec.columns) * 92,
        y: cursorY + 70 + Math.floor(index / spec.columns) * 82,
      });
    });
    cursorX += spec.width + 34;
    rowHeight = Math.max(rowHeight, spec.height);
  }
  return finishLayout(positions, groups);
}

function concentricLayout(nodes) {
  const positions = new Map();
  const byType = new Map();
  for (const node of nodes) {
    if (!byType.has(node.type)) byType.set(node.type, []);
    byType.get(node.type).push(node);
  }
  let previousRadius = 0;
  for (const members of byType.values()) {
    const spacing = 88;
    const radiusForCount = members.length <= 1 ? 0 : (members.length * spacing) / (2 * Math.PI);
    const radius = Math.max(previousRadius + (previousRadius ? 125 : 0), radiusForCount, members.length === 1 ? 0 : 105);
    members.forEach((node, index) => {
      if (members.length === 1 && radius === 0) positions.set(node.id, { x: 0, y: 0 });
      else {
        const angle = (Math.PI * 2 * index / members.length) - Math.PI / 2;
        positions.set(node.id, { x: Math.cos(angle) * radius, y: Math.sin(angle) * radius });
      }
    });
    previousRadius = radius + 70;
  }
  return finishLayout(positions);
}

function radialLayout(nodes) {
  const positions = new Map();
  const ordered = [...nodes].sort((a, b) => a.group.localeCompare(b.group) || a.title.localeCompare(b.title));
  if (ordered.length === 1) {
    positions.set(ordered[0].id, { x: 0, y: 0 });
    return finishLayout(positions);
  }
  const spacing = 86;
  let index = 0;
  let radius = 95;
  while (index < ordered.length) {
    const capacity = Math.max(6, Math.floor((2 * Math.PI * radius) / spacing));
    const count = Math.min(capacity, ordered.length - index);
    for (let ringIndex = 0; ringIndex < count; ringIndex += 1) {
      const angle = (Math.PI * 2 * ringIndex / count) - Math.PI / 2;
      const node = ordered[index + ringIndex];
      positions.set(node.id, { x: Math.cos(angle) * radius, y: Math.sin(angle) * radius });
    }
    index += count;
    radius += spacing;
  }
  return finishLayout(positions);
}

function calculateLayout(nodes) {
  if (state.layout === "grid") return gridLayout(nodes);
  if (state.layout === "concentric") return concentricLayout(nodes);
  if (state.layout === "cose") return radialLayout(nodes);
  return clusterLayout(nodes);
}

function createSvg(tag, attributes = {}) {
  const element = document.createElementNS(SVG_NS, tag);
  for (const [key, value] of Object.entries(attributes)) element.setAttribute(key, String(value));
  return element;
}

function updateTransform() {
  viewport.setAttribute("transform", `translate(${state.view.x} ${state.view.y}) scale(${state.view.k})`);
  updateLabelVisibility();
}

function updateLabelVisibility() {
  const count = state.visibleIds.size;
  const showAll = count <= 220 || state.view.k >= (count > 1800 ? 1.30 : count > 700 ? .85 : .55);
  for (const [id, label] of labelElements) {
    const show = showAll || id === state.selected;
    label.classList.toggle("hidden", !show);
  }
}

function fitBounds(bounds = state.bounds, padding = 65) {
  const rect = svg.getBoundingClientRect();
  if (!rect.width || !rect.height) return;
  const width = Math.max(1, bounds.maxX - bounds.minX);
  const height = Math.max(1, bounds.maxY - bounds.minY);
  const scale = Math.min((1000 - padding * 2) / width, (700 - padding * 2) / height);
  state.view.k = Math.max(.008, Math.min(8, scale));
  state.view.x = 500 - ((bounds.minX + bounds.maxX) / 2) * state.view.k;
  state.view.y = 350 - ((bounds.minY + bounds.maxY) / 2) * state.view.k;
  updateTransform();
}

function resetView() {
  state.view = { x: 0, y: 0, k: 1 };
  updateTransform();
}

function zoomAt(svgPoint, factor) {
  const oldK = state.view.k;
  const newK = Math.max(.008, Math.min(18, oldK * factor));
  const worldX = (svgPoint.x - state.view.x) / oldK;
  const worldY = (svgPoint.y - state.view.y) / oldK;
  state.view.k = newK;
  state.view.x = svgPoint.x - worldX * newK;
  state.view.y = svgPoint.y - worldY * newK;
  updateTransform();
}

function clientToSvg(clientX, clientY) {
  const point = svg.createSVGPoint();
  point.x = clientX;
  point.y = clientY;
  const matrix = svg.getScreenCTM();
  return matrix ? point.matrixTransform(matrix.inverse()) : { x: 500, y: 350 };
}

function focusNode(id, scale = Math.max(1.1, state.view.k)) {
  const point = state.positions.get(id);
  if (!point) return;
  state.view.k = Math.max(.35, Math.min(8, scale));
  state.view.x = 500 - point.x * state.view.k;
  state.view.y = 350 - point.y * state.view.k;
  updateTransform();
}

function renderGraph({ fit = true } = {}) {
  const nodes = visibleNodes();
  const visible = new Set(nodes.map(node => node.id));
  const layoutResult = calculateLayout(nodes);
  state.positions = layoutResult.positions;
  state.bounds = layoutResult.bounds;
  state.visibleIds = visible;
  groupsLayer.replaceChildren();
  edgesLayer.replaceChildren();
  nodesLayer.replaceChildren();
  nodeElements.clear();
  labelElements.clear();

  const groupFragment = document.createDocumentFragment();
  for (const group of layoutResult.groups) {
    const box = createSvg("rect", {
      x: group.x, y: group.y, width: group.width, height: group.height,
      rx: 18, ry: 18, class: "group-box",
    });
    const label = createSvg("text", { x: group.x + 18, y: group.y + 30, class: "group-label" });
    label.textContent = `${group.name} (${group.count})`;
    label.addEventListener("click", event => {
      event.stopPropagation();
      state.group = group.name;
      groupSelect.value = group.name;
      renderGraph({ fit: true });
    });
    groupFragment.append(box, label);
  }
  groupsLayer.appendChild(groupFragment);

  const edgeFragment = document.createDocumentFragment();
  let visibleEdgeCount = 0;
  for (const edge of DATA.edges) {
    if (!visible.has(edge.source) || !visible.has(edge.target)) continue;
    const a = layoutResult.positions.get(edge.source);
    const b = layoutResult.positions.get(edge.target);
    if (!a || !b) continue;
    edgeFragment.appendChild(createSvg("line", {
      x1: a.x, y1: a.y, x2: b.x, y2: b.y, class: "edge",
    }));
    visibleEdgeCount += 1;
  }
  edgesLayer.appendChild(edgeFragment);

  const nodeFragment = document.createDocumentFragment();
  for (const node of nodes) {
    const point = layoutResult.positions.get(node.id);
    const group = createSvg("g", {
      class: "node" + (state.selected === node.id ? " selected" : ""),
      transform: `translate(${point.x} ${point.y})`,
    });
    const radius = Math.max(12, Math.min(25, 13 + (node.degree || 0) * 1.7));
    const circle = createSvg("circle", { r: radius });
    const title = createSvg("title");
    title.textContent = `${node.title}\n${node.id}`;
    const label = createSvg("text", {
      "text-anchor": "middle",
      dy: radius + 19,
      class: "node-label",
    });
    label.textContent = node.title.length > 31 ? node.title.slice(0, 30) + "…" : node.title;
    group.append(circle, title, label);
    group.addEventListener("click", event => {
      event.stopPropagation();
      selectNode(node.id, { focus: false });
    });
    group.addEventListener("dblclick", event => {
      event.stopPropagation();
      selectNode(node.id, { focus: true });
    });
    nodeElements.set(node.id, group);
    labelElements.set(node.id, label);
    nodeFragment.appendChild(group);
  }
  nodesLayer.appendChild(nodeFragment);

  if (state.selected && !visible.has(state.selected)) state.selected = null;
  updateSelectionClasses();
  summary.textContent = `${nodes.length.toLocaleString()} / ${DATA.nodes.length.toLocaleString()} concepts · ${visibleEdgeCount.toLocaleString()} relationships · ${layoutResult.groups.length || DATA.groups.length} groups`;
  if (fit) requestAnimationFrame(() => fitBounds());
  else updateTransform();
}

function updateSelectionClasses() {
  for (const element of nodeElements.values()) element.classList.remove("selected", "related", "dim");
  if (!state.selected || !nodeElements.has(state.selected)) {
    updateLabelVisibility();
    return;
  }
  const selected = DATA.nodeById[state.selected];
  const related = new Set([...(selected.links_to || []), ...(selected.cited_by || [])]);
  for (const [id, element] of nodeElements) {
    if (id === state.selected) element.classList.add("selected");
    else if (related.has(id)) element.classList.add("related");
    else if (related.size) element.classList.add("dim");
  }
  updateLabelVisibility();
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

function selectNode(id, { focus = false } = {}) {
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
      <span class="badge">${escapeHtml(node.group)}</span>
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
  panel.querySelectorAll("[data-open]").forEach(button => button.addEventListener("click", () => {
    const targetId = button.dataset.open;
    if (!state.visibleIds.has(targetId)) {
      state.query = "";
      state.type = "";
      state.group = "";
      search.value = "";
      typeSelect.value = "";
      groupSelect.value = "";
      renderGraph({ fit: false });
    }
    selectNode(targetId, { focus: true });
  }));
  updateSelectionClasses();
  if (focus) focusNode(id);
}

for (const type of DATA.types) {
  const option = document.createElement("option");
  option.value = type;
  option.textContent = type;
  typeSelect.appendChild(option);
}
for (const group of DATA.groups) {
  const option = document.createElement("option");
  option.value = group;
  option.textContent = group;
  groupSelect.appendChild(option);
}

let filterTimer;
function scheduleFilter() {
  clearTimeout(filterTimer);
  filterTimer = setTimeout(() => renderGraph({ fit: true }), 120);
}
search.addEventListener("input", () => { state.query = search.value; scheduleFilter(); });
typeSelect.addEventListener("change", () => { state.type = typeSelect.value; renderGraph({ fit: true }); });
groupSelect.addEventListener("change", () => { state.group = groupSelect.value; renderGraph({ fit: true }); });
layoutSelect.addEventListener("change", () => { state.layout = layoutSelect.value; renderGraph({ fit: true }); });
document.getElementById("fit").addEventListener("click", () => fitBounds());
document.getElementById("reset").addEventListener("click", resetView);
document.getElementById("zoom-in").addEventListener("click", () => zoomAt({ x: 500, y: 350 }, 1.35));
document.getElementById("zoom-out").addEventListener("click", () => zoomAt({ x: 500, y: 350 }, 1 / 1.35));

svg.addEventListener("wheel", event => {
  event.preventDefault();
  zoomAt(clientToSvg(event.clientX, event.clientY), Math.exp(-event.deltaY * .0015));
}, { passive: false });
svg.addEventListener("dblclick", event => {
  if (event.target === svg || event.target === groupsLayer || event.target === edgesLayer) fitBounds();
});
svg.addEventListener("click", event => {
  if (event.target === svg) {
    state.selected = null;
    updateSelectionClasses();
  }
});

const pointers = new Map();
let dragStart = null;
let pinchStart = null;
svg.addEventListener("pointerdown", event => {
  if (event.button !== undefined && event.button !== 0) return;
  const interactive = event.target.closest?.(".node, .group-label");
  if (interactive) return;
  svg.setPointerCapture(event.pointerId);
  const point = clientToSvg(event.clientX, event.clientY);
  pointers.set(event.pointerId, point);
  if (pointers.size === 1) {
    dragStart = { point, x: state.view.x, y: state.view.y };
    svg.classList.add("dragging");
  } else if (pointers.size === 2) {
    const [a, b] = [...pointers.values()];
    pinchStart = {
      distance: Math.hypot(a.x - b.x, a.y - b.y),
      midpoint: { x: (a.x + b.x) / 2, y: (a.y + b.y) / 2 },
      view: { ...state.view },
    };
  }
});
svg.addEventListener("pointermove", event => {
  if (!pointers.has(event.pointerId)) return;
  const point = clientToSvg(event.clientX, event.clientY);
  pointers.set(event.pointerId, point);
  if (pointers.size === 1 && dragStart) {
    state.view.x = dragStart.x + point.x - dragStart.point.x;
    state.view.y = dragStart.y + point.y - dragStart.point.y;
    updateTransform();
  } else if (pointers.size === 2 && pinchStart) {
    const [a, b] = [...pointers.values()];
    const distance = Math.max(1, Math.hypot(a.x - b.x, a.y - b.y));
    const midpoint = { x: (a.x + b.x) / 2, y: (a.y + b.y) / 2 };
    const oldK = pinchStart.view.k;
    const newK = Math.max(.008, Math.min(18, oldK * distance / Math.max(1, pinchStart.distance)));
    const worldX = (pinchStart.midpoint.x - pinchStart.view.x) / oldK;
    const worldY = (pinchStart.midpoint.y - pinchStart.view.y) / oldK;
    state.view.k = newK;
    state.view.x = midpoint.x - worldX * newK;
    state.view.y = midpoint.y - worldY * newK;
    updateTransform();
  }
});
function endPointer(event) {
  pointers.delete(event.pointerId);
  if (!pointers.size) {
    dragStart = null;
    pinchStart = null;
    svg.classList.remove("dragging");
  } else if (pointers.size === 1) {
    const point = [...pointers.values()][0];
    dragStart = { point, x: state.view.x, y: state.view.y };
    pinchStart = null;
  }
}
svg.addEventListener("pointerup", endPointer);
svg.addEventListener("pointercancel", endPointer);

renderGraph({ fit: true });
if (DATA.nodes.length) selectNode(DATA.nodes[0].id, { focus: false });
</script>
</body>
</html>
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
    return "human-reviewed" if any(
        str(item.get("by", "")).startswith("human:")
        for item in entries
        if isinstance(item, dict)
    ) else "machine-confirmed"


def concept_group(concept_id: str) -> str:
    parent = PurePosixPath(concept_id).parent.as_posix()
    return "(root)" if parent in ("", ".") else parent


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
            "group": concept_group(rel),
            "description": str(meta.get("description") or ""),
            "tags": meta.get("tags") if isinstance(meta.get("tags"), list) else [],
            "status": str(meta.get("status") or "stable"),
            "stale_after": str(meta.get("stale_after") or ""),
            "generated": meta.get("generated"),
            "timestamp": meta.get("timestamp"),
            "verified": meta.get("verified"),
            "sources": meta.get("sources") if isinstance(meta.get("sources"), list) else [],
            "body": body[:BODY_LIMIT],
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
        "groups": sorted({record["group"] for record in records}),
        "today": date.today().isoformat(),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Render an OKF bundle as an offline HTML graph.")
    parser.add_argument("bundle", nargs="?", type=Path, default=Path(".okf"))
    parser.add_argument("-o", "--output", type=Path, default=None)
    parser.add_argument("--layout", choices=("cluster", "grid", "concentric", "cose"), default=None)
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
    layout = args.layout or ("cluster" if len(data["nodes"]) > 300 else "cose")
    output = args.output or (bundle / "viz.html")
    payload = json.dumps(data, ensure_ascii=False, default=str).replace("<", "\\u003c")
    document = HTML_TEMPLATE.replace("__DATA__", payload).replace("__LAYOUT__", html.escape(layout))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(document, encoding="utf-8")
    print(
        f"wrote offline OKF visualization to {output} "
        f"({len(data['nodes'])} concepts, {len(data['edges'])} relationships, {len(data['groups'])} groups)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
