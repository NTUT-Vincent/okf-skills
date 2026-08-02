# External Network / API Audit

Audit scope: upstream fork state at commit `cb5c0a9973c81ea3702f677e0b8852d93b47be80`, compared with the core-skill branch.

## Summary

The OKF format itself does not require an external API. This branch keeps the original `okf`, `validate`, and `visualize` skills and their Python scripts unchanged, while removing plugin packaging, CI, benchmark, demos, tests, and other repository-level distribution material.

The retained core has no direct Python HTTP client calls. Network access can still occur indirectly through dependency installation, the generated visualizer page, or an Attested Computation declared by a bundle.

## Retained core components

| Component | Direct API/HTTP call in its Python logic | Possible external access |
|---|---|---|
| `skills/okf/SKILL.md` | N/A — instruction file | Allows `Bash`, invokes `uv run`, calls the companion validator, and instructs an Agent to run a declared Attested Computation when needed. The computation may target a database, cloud service, script, SQL engine, or API depending on the bundle. |
| `skills/okf/scripts/okf_init.py` | No | Declares `pyyaml>=6` through PEP 723. `uv run` may download PyYAML from PyPI or another configured registry when not cached. The script itself only reads and writes local files. |
| `skills/validate/SKILL.md` | N/A — instruction file | Runs `uv run`. Its fallback explicitly runs `python3 -m pip install --quiet pyyaml`, which can contact PyPI or a configured registry. |
| `skills/validate/scripts/okf_validate.py` | No | After PyYAML is available, validation is local file processing. `--migrate` rewrites local bundle files in place. |
| `skills/visualize/SKILL.md` | N/A — instruction file | Runs `uv run`. Its fallback installs PyYAML with pip. |
| `skills/visualize/scripts/okf_visualize.py` | No Python HTTP request | The generated `viz.html` references Cytoscape, marked, and DOMPurify from `https://cdn.jsdelivr.net`. Opening the HTML in a browser causes those CDN requests unless blocked or cached. |

## Removed repository-level network surfaces

| Removed component | Original external access |
|---|---|
| `.claude-plugin/*` and marketplace installation | Claude plugin marketplace, GitHub, or skills distribution service |
| `npx skills add` installation flow | npm/skills service and GitHub |
| `action.yml` | `astral-sh/setup-uv@v5`, GitHub Actions infrastructure, and dependency resolution |
| `.github/workflows/ci.yml` | GitHub-hosted runners, `actions/checkout@v4`, `setup-uv`, and package resolution |
| GitHub Pages, badges, demo GIF, generated documentation | Browser requests to GitHub and linked remote assets |
| Benchmark and test harness | May invoke Agent tooling or hosted model services depending on how the benchmark is executed |

## Attested Computation boundary

An OKF `type: Attested Computation` concept can declare:

- `runtime`
- `parameters`
- `computation`
- `executor`
- `attester`

These fields are metadata until an Agent follows the original skill instruction to run the computation. At that point, external access depends entirely on the referenced executor. Examples include:

- BigQuery or another database
- a local or remote script
- a cloud SDK
- an internal HTTP endpoint
- an external API

The repository cannot guarantee that such an execution is offline. Review each Attested Computation concept before running it.

## URL-shaped fields that are inert by themselves

The following values do not automatically trigger a network request:

- concept `resource`
- `sources[].resource`
- `executor.resource`
- `attester.resource`
- Markdown links in concept bodies
- source URLs written in the vendored specification

They become network activity only when a human, browser, script, or Agent follows them.

## Retained file layout

```text
README.md
EXTERNAL-NETWORK-AUDIT.md
LICENSE
NOTICE
skills/okf/SKILL.md
skills/okf/scripts/okf_init.py
skills/okf/reference/SPEC.md
skills/okf/reference/APACHE-2.0.txt
skills/okf/templates/concept.md
skills/okf/templates/index.md
skills/okf/templates/log.md
skills/validate/SKILL.md
skills/validate/scripts/okf_validate.py
skills/visualize/SKILL.md
skills/visualize/scripts/okf_visualize.py
```

## Practical controls

To reduce unintended network access while keeping the original skills:

1. Preinstall PyYAML in an approved environment so `uv` or pip does not need to download it at runtime.
2. Mirror or vendor the visualizer JavaScript libraries if the generated HTML must work fully offline.
3. Review every Attested Computation before execution and restrict Agent tools or credentials at the host level.
4. Treat `resource` and `sources` URLs as references, not automatic permission to fetch them.
