---
name: okf
description: >-
  Locally author, maintain, consume, and structurally check Open Knowledge Format
  (OKF) v0.2 knowledge bundles made of Markdown plus YAML frontmatter. Use only
  when the user explicitly asks to create, update, read, organize, convert, or
  check an OKF bundle. This local-only variant must not run commands, install
  packages, browse the web, call MCP tools, execute computations, or contact
  external APIs.
user-invocable: true
argument-hint: "[produce|maintain|consume|check] [bundle-path]"
allowed-tools: Read Write Edit Grep Glob
---

# Open Knowledge Format — local-only skill

Use this skill to work with OKF bundles using local file operations only. OKF is
Markdown with YAML frontmatter; it has no required runtime, SDK, service, or API.

Before non-trivial work, read [`reference/SPEC.md`](reference/SPEC.md). It is the
canonical OKF v0.2 specification and overrides summaries or remembered rules.

## Hard execution boundary

While this skill is active:

- Do not use shell commands, package managers, Git commands, browser tools, web
  search, MCP, database clients, cloud SDKs, HTTP clients, or external APIs.
- Do not run Python, JavaScript, SQL, executors, attesters, validators, migration
  scripts, or visualizers.
- Treat `resource` and `sources[].resource` values as metadata. Record and display
  them, but do not follow URLs or fetch their contents unless the user separately
  requests external research outside this skill.
- For `type: Attested Computation`, document the declared contract only. Never run
  its computation, `executor`, `attester`, referenced script, query, or endpoint.
- Do not create commits, branches, pull requests, CI files, hooks, or scheduled
  jobs.
- Do not update a bundle merely because `.okf/` exists. Only modify it when the
  user explicitly requests OKF creation or maintenance.

## The only hard conformance rule

A bundle is conformant under §11 when every non-reserved `.md` file:

1. starts with a parseable YAML frontmatter block; and
2. has a non-empty string `type` field.

Everything else is optional guidance. Do not reject unknown concept types,
unknown frontmatter keys, or broken links. Report broken links as warnings only.

## Bundle conventions

- One concept equals one `.md` file.
- The concept ID is its bundle-relative path without `.md`.
- `index.md` and `log.md` are reserved and are not ordinary concepts.
- The root `index.md` may carry only `okf_version` frontmatter; directory indexes
  normally have no frontmatter.
- Prefer `.okf/` at the repository root unless the project already uses another
  bundle location.
- Organize directories by domain, not by arbitrary file size: for example
  `services/`, `datasets/`, `decisions/`, `runbooks/`, and `metrics/`.
- Express relationships with standard Markdown links. Put the relationship meaning
  in surrounding prose rather than inventing a fixed edge taxonomy.

## Frontmatter guidance

`type` is the only always-required field. Add these when supported by information
actually available in local files or provided by the user:

- `title`: human-readable name.
- `description`: one-sentence summary.
- `resource`: canonical URI or local asset reference; omit for abstract concepts.
- `tags`: cross-cutting labels.
- `status`: `draft`, `stable`, or `deprecated`; absence means stable.
- `stale_after`: absolute `YYYY-MM-DD` date.
- `generated: { by, at }`: who produced the current content and when.
- `verified`: confirmation events. Never invent verification.
- `sources`: materials actually used to derive the concept.

Actor values follow §7:

- agent or producer: `<producer>/<version>`
- person: `human:<id>`
- automated process: `process:<id>`

For newly generated documents, use `okf-local/1.0` as `generated.by` unless the
user supplies a different actor. Use the current ISO 8601 timestamp available in
the conversation context. Do not add `verified` unless the user explicitly says a
person or process verified the content.

For provenance:

- Record only sources actually read locally or explicitly supplied by the user.
- Every `sources` entry needs `resource`.
- Use stable `sources[].id` values when claims need footnote attribution.
- Attribute a specific claim with `[^source-id]` and a matching footnote.
- A URL in `resource` is still only a recorded string in this local-only mode.

## Modes

### `produce` — create or extend a bundle

1. Read `reference/SPEC.md` and inspect the local source files relevant to the
   requested knowledge.
2. If starting a bundle, manually create:
   - root `index.md` with `okf_version: "0.2"`;
   - root `log.md`;
   - one or more concepts based on `templates/concept.md`.
3. Derive concepts from code, local documentation, configuration, schemas, or
   facts supplied by the user. Do not infer unsupported implementation details.
4. Create one concept per durable unit of knowledge. Prefer knowledge explaining
   purpose, constraints, decisions, ownership, failure modes, and operational
   behavior rather than merely restating source code.
5. Add or refresh directory indexes and append a dated log entry.
6. Run the local structural check described below using file inspection only.

### `maintain` — update a bundle after local changes

1. Find affected concepts by local path, `resource`, title, tags, links, or topic.
2. Update every affected concept in one pass.
3. Preserve unknown frontmatter fields.
4. Update `generated.at`; retain or update `generated.by` truthfully.
5. Do not preserve stale verification as though it reviewed the new content. If an
   edit invalidates a prior verification, explain the uncertainty and remove only
   the affected verification entry when justified.
6. Mark removed assets `status: deprecated` and document the replacement or reason
   instead of silently deleting useful history.
7. Update indexes and append a dated `log.md` entry.
8. When touching v0.1 content, migrate `timestamp` to `generated.at` and body
   `# Citations` to `sources` only when the mapping is supported by the existing
   text. Do not invent missing actors or per-claim attribution.

### `consume` — use an existing bundle as local context

1. Read the root `index.md` first.
2. Follow only bundle links relevant to the current task.
3. Weigh trust and lifecycle signals:
   - `status: draft` or `deprecated` requires caution;
   - expired `stale_after` requires local confirmation;
   - no `verified` means unverified, not invalid.
4. Treat broken links as missing knowledge, not conformance failures.
5. Never execute an Attested Computation in this local-only variant. Explain what
   it declares and which external execution would be required.
6. Do not write changes unless the user explicitly asks to maintain the bundle.

### `check` — local structural review without scripts

Inspect all bundle `.md` files and report findings in two groups: `ERROR` and
`WARNING`.

Errors:

- A non-reserved `.md` file has no complete YAML frontmatter block.
- Its frontmatter is visibly malformed or not a mapping.
- `type` is missing, empty, or not a string.

Warnings:

- Recommended `title`, `description`, or `tags` is absent.
- `generated.by` does not follow an actor shape.
- `generated.at` or `verified[].at` is not ISO 8601.
- `stale_after` is not `YYYY-MM-DD`.
- `status` is outside `draft|stable|deprecated`.
- A `sources` entry lacks `resource`.
- A claim footnote has no matching `sources[].id`.
- Root `index.md` lacks `okf_version: "0.2"`.
- An index omits an existing concept or subdirectory.
- A local Markdown link target does not exist.
- A concept still uses v0.1 `timestamp` or `# Citations`.

State clearly that this is a file-inspection review, not the removed deterministic
Python validator. Never install a parser or run a command to strengthen the check.

## Templates

Use these local templates as starting points:

- [`templates/concept.md`](templates/concept.md)
- [`templates/index.md`](templates/index.md)
- [`templates/log.md`](templates/log.md)

Adapt them to the available facts. Remove placeholder fields that are unsupported;
do not leave angle-bracket placeholders in completed concepts.
