# External Network / API Audit

Audit scope: upstream fork state at commit `cb5c0a9973c81ea3702f677e0b8852d93b47be80`, compared with the `local-only-okf-skill` branch.

## Summary

The OKF file format itself does not require an external API. The original toolkit adds several execution and distribution surfaces that may access the network. This branch removes those surfaces and keeps only local Markdown/YAML authoring instructions, templates, the normative specification, attribution notices, and license files.

## Original components that may access the network

| Original component | Potential external access | Why | Local-only branch |
|---|---|---|---|
| `skills/okf/SKILL.md` | Package registry; arbitrary executor target | It allows `Bash`, invokes `uv run`, calls the companion validator, and tells the consumer to run a declared Attested Computation. `uv` may resolve/download Python dependencies; an Attested Computation may point to a database, script, cloud service, or API depending on the bundle. | Replaced. No `Bash`; computations are described but never executed. |
| `skills/okf/scripts/okf_init.py` | PyPI through `uv` dependency resolution | The script declares `pyyaml>=6` using PEP 723. The Python code itself only reads/writes local files, but `uv run` may download PyYAML when it is not cached. | Removed. Bundle scaffolding is performed with local file tools. |
| `skills/validate/SKILL.md` | PyPI | It runs `uv run`; its fallback explicitly executes `python3 -m pip install --quiet pyyaml`. | Removed. Replaced by a non-executable file-inspection checklist. |
| `skills/validate/scripts/okf_validate.py` | No direct HTTP/API call after dependencies exist | The validator imports standard-library modules and PyYAML and operates on local files. Its network exposure comes from installing/resolving PyYAML, not from validation logic. `--migrate` also rewrites local files. | Removed. |
| `skills/visualize/SKILL.md` | PyPI | It runs `uv run`; its fallback installs PyYAML with pip. | Removed. |
| `skills/visualize/scripts/okf_visualize.py` | jsDelivr CDN in the generated page; PyPI during execution setup | The generated HTML references Cytoscape, marked, and DOMPurify from `https://cdn.jsdelivr.net`. Opening the page in a browser requests those scripts unless already cached or blocked. The generator also declares `pyyaml>=6`. | Removed. No generated HTML or CDN assets. |
| `action.yml` | GitHub Marketplace/action download; uv/PyPI dependency resolution | It uses `astral-sh/setup-uv@v5` and then runs `uv`. GitHub runners must retrieve the action and potentially dependencies. | Removed. |
| `.github/workflows/ci.yml` | GitHub Actions infrastructure and third-party actions | It uses `actions/checkout@v4`, `astral-sh/setup-uv@v5`, GitHub-hosted runners, and dependency resolution. | Removed. |
| `.claude-plugin/*`, marketplace and `npx skills add` distribution | GitHub, npm/skills service, or plugin marketplace | Installation commands and manifests are distribution mechanisms, not required for the skill's knowledge logic. | Removed. Manual folder copy only. |
| README badges, live demo, GitHub Pages, screenshots | GitHub and linked web hosts when viewed | Browsers can request badge images, demo pages, linked repositories, and other remote assets. | Removed from the minimal README. |
| Benchmark and demo tooling | Depends on how tests/agents are run | The benchmark is not needed for authoring/reading OKF and may invoke agent tooling or hosted services outside the core skill. | Removed. |

## Values that look like URLs but do not automatically call anything

These are data fields or ordinary Markdown links. They are not network calls by themselves:

- concept `resource`
- `sources[].resource`
- `executor.resource` and `attester.resource` inside an Attested Computation
- Markdown links in a concept body
- source URLs written in the vendored specification

They cause external access only when a human, browser, script, or agent actively follows or executes them. The local-only `SKILL.md` explicitly forbids following or executing them while the skill is active.

## Local-only branch network posture

Included files:

```text
README.md
EXTERNAL-NETWORK-AUDIT.md
LICENSE
NOTICE
skills/okf/SKILL.md
skills/okf/reference/SPEC.md
skills/okf/reference/APACHE-2.0.txt
skills/okf/templates/concept.md
skills/okf/templates/index.md
skills/okf/templates/log.md
```

There are no executable scripts, package manifests, shell commands, CI workflows, plugin manifests, generated web applications, or runtime dependencies in this branch.

The skill declares only:

```yaml
allowed-tools: Read Write Edit Grep Glob
```

This means the skill itself does not request a network-capable tool. It is not a sandbox guarantee: a host application may expose browser, MCP, connector, or network tools outside this skill. For strict isolation, disable those capabilities in the host environment as well.
