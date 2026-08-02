---
name: okf
description: >-
  Author, maintain, and consume Open Knowledge Format (OKF) knowledge bundles —
  portable markdown + YAML frontmatter that both humans and agents read. Use when
  capturing project knowledge (services, APIs, schemas, metrics, runbooks,
  decisions) into an OKF bundle, when updating one after code or docs change, or
  when a repository contains an `.okf/` (or other OKF) bundle that should inform
  the task. Triggers on: "document this in OKF", "update the knowledge bundle",
  "capture this as a concept", or any work in a repo that has an OKF bundle.
user-invocable: true
argument-hint: "[produce|maintain|consume] [path]"
allowed-tools: Read Write Edit Grep Glob
---

# Open Knowledge Format (OKF) skill

OKF represents knowledge as a directory of markdown files with YAML frontmatter.
It is minimal by design: no schema registry, no runtime, no SDK. Your job is to
produce, maintain, and consume OKF bundles **conformant with the spec**, not your
memory of it.

**Always read the canonical spec before non-trivial work:**
[reference/SPEC.md](reference/SPEC.md). It is the verbatim OKF v0.2 specification
and the source of truth for every rule below.

## Local-only constraint

This fork omits the executable helper layer. Use only local file tools: do not run
shell commands, install packages, browse or fetch URLs, call external APIs or MCP
tools, or execute an Attested Computation's query, executor, or attester. URL-like
`resource` values remain metadata unless the user separately requests research.

## The one hard rule

A bundle is conformant (§11) iff: every non-reserved `.md` file has a parseable
YAML frontmatter block, and every such block has a **non-empty `type`** field.
Everything else is soft guidance. Consumers MUST tolerate missing optional
fields, unknown types, and broken links — never reject a bundle over them.

## Conventions to apply

- **One concept = one file.** The file path (minus `.md`) is the concept ID.
- **Frontmatter:** `type` is required. Add `title`, `description`, `tags` when
  they aid consumption; add `resource` (a canonical URI) only for concepts bound
  to a real asset — omit it for abstract concepts.
- **Body:** prefer structural markdown (headings, tables, lists, fenced code).
  Conventional headings: `# Schema`, `# Examples`, `# Computation`.
- **Cross-links:** standard markdown links; prefer absolute bundle-relative
  form (`/services/auth-api.md`). A link asserts a relationship; its *kind* lives
  in the surrounding prose, not the link.
- **Reserved files:** `index.md` (directory listing, no frontmatter — except the
  bundle-root index may carry only `okf_version`) and `log.md` (ISO-dated change
  history, newest first). Never use these names for concepts.

## The v0.2 families (all optional, all worth filling)

- **Trust (§5.2):** `generated: { by, at }` — who produced the current content
  and when. `verified: [{ by, at }]` — who confirmed it since (a bare mapping is
  one entry). Write `by` in the **actor convention** (§7): `<producer>/<version>`
  for an agent, `human:<id>` for a person, `process:<id>` for an automated job.
  Use `human:` whenever a person authored or signed off — consumers key trust
  tiers off that prefix.
- **Lifecycle (§5.4–5.5):** `status: draft|stable|deprecated` (absent means
  stable) and `stale_after: YYYY-MM-DD`, an absolute date, not a TTL.
- **Provenance (§5.1):** `sources: [{ id, resource, title, author,
  usage_count, last_modified }]` — the materials the concept derives from.
  `resource` is required per entry and may be a URL, a bundle path, or a scope
  descriptor. Attribute a specific claim with a markdown footnote whose label is
  the source's `id`: `…sharded daily.[^ga4-schema]` plus a `[^ga4-schema]: …`
  definition. The label is the join key — it must match a `sources[].id`.
- **Attestation (§10):** a sanctioned computation is its own concept,
  `type: Attested Computation`, carrying `runtime` (required), `parameters`,
  `executor`, `attester`, and the computation itself under `# Computation` (or a
  `computation:` path). Concepts that need the value link to it. Never inline a
  number's SQL into the concept that narrates it. In this local-only fork, record
  and inspect the contract but do not execute it.

**Reading a v0.1 bundle?** Two constructs were superseded (§13.1): `timestamp`
is now `generated.at`, and a body `# Citations` list is now `sources`. Read both,
write v0.2 — and when you touch a legacy concept in **maintain** mode, migrate
its frontmatter as part of the edit. Treat both superseded constructs as warnings.

Templates to copy: [concept](templates/concept.md), [index](templates/index.md),
[log](templates/log.md).

## Default bundle location

Use `.okf/` at the repository root unless the project already uses another
location. Commit it alongside the code it describes — knowledge as code.

## Modes

### produce — create or extend a bundle

**Starting a brand-new bundle?** Create a conformant `index.md`, `log.md`, and a
`getting-started.md` concept with full recommended frontmatter using the local
templates. Do not run the removed init script. Then extend it:

1. Read [reference/SPEC.md](reference/SPEC.md).
2. Pick the source(s): **code** (derive concepts from source, READMEs,
   docstrings, config), **docs/wiki** (distill pages into concepts, record the
   originals in `sources`), **manual** (decisions, playbooks, metrics).
3. Choose a directory layout by domain (e.g. `services/`, `datasets/`,
   `decisions/`). One concept per file.
4. Write each concept from [templates/concept.md](templates/concept.md): set a
   descriptive `type`, fill recommended fields, record `generated` and the
   `sources` you actually read, cross-link related concepts.
5. Add/refresh `index.md` per directory (and `okf_version: "0.2"` in the root
   index). Append a dated entry to `log.md`.
6. Check conformance (see below). Fix every error before finishing.

### maintain — keep a bundle in sync with reality
1. Identify which concepts the change affects (search by `resource`, path, or
   topic). This bookkeeping is exactly what agents are good at — touch every
   affected file in one pass.
2. Update the body and `generated.at` (with your own actor in `generated.by`);
   fix or add cross-links; create new concepts for new assets; mark removed
   assets `status: deprecated` and note the deprecation in `log.md` rather than
   silently deleting context. Facing a whole v0.1 bundle rather than a stray
   field? Migrate the superseded fields as part of the local edit; do not run the
   removed validator's `--migrate` mode.
3. Update the relevant `index.md` files and append a dated `log.md` entry
   describing what changed.
4. Check conformance.

### consume — use a bundle as context
1. Read the bundle-root `index.md` first for progressive disclosure, then follow
   links only into the concepts relevant to the task.
2. Weigh what you read: `status: draft`/`deprecated`, a `stale_after` already
   past, or no `verified` entry all mean "check before relying on this". Treat
   broken links as not-yet-written knowledge, not errors.
3. Need a number an `Attested Computation` covers? Inspect its computation and
   bind reasoning to the declared `parameters` — never write your own query and
   never execute the declared computation in this local-only fork.
4. If you learn something durable while working, switch to **maintain** and
   write it back.

## Validation (do this before declaring done)

This local-only fork does not ship or run the deterministic Python checker.
Inspect every non-reserved `.md` file with local file tools and apply the same
§11 boundary: a missing or unparseable YAML frontmatter block, or a missing/empty
`type`, is an `ERROR`. Missing recommended fields, malformed optional v0.2
families, broken links, and superseded v0.1 constructs are warnings.

Resolve every `ERROR` (hard §11 failures). Warnings are soft; fix them when cheap,
but they never block.
