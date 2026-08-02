# External Network / API Audit

Audit scope: the `local-only-okf-skill` branch prepared for company repository scanning.

## Result

The retained runtime does not contain an intentional external network client or browser dependency loader.

- no CDN script or stylesheet reference
- no browser `fetch`
- no Python HTTP client
- no `curl` or `wget`
- no `pip install` command in the skills
- no `uv run` command in the skills
- no automatic execution of a remote Attested Computation without host approval

## Retained components

| Component | Network behavior |
|---|---|
| `skills/okf/scripts/okf_init.py` | Python standard library only; local file creation. |
| `skills/validate/scripts/okf_validate.py` | Local bundle parsing and optional local migration. It imports PyYAML but does not install it or contact a registry. |
| `skills/visualize/scripts/okf_visualize.py` | Local bundle parsing and local HTML generation. The generated file embeds CSS and vanilla JavaScript and does not load remote browser assets. |
| `skills/okf/SKILL.md` | Requires explicit authorization before following an Attested Computation executor that could access a database, service, or API. |
| `skills/validate/SKILL.md` | Invokes the checker with the approved local Python interpreter only. |
| `skills/visualize/SKILL.md` | Invokes the offline visualizer with the approved local Python interpreter only. |

## Dependency boundary

`validate` and `visualize` require PyYAML to already exist in the approved Python environment. This repository does not include an installation command, package-lock workflow, or runtime dependency download.

Provision PyYAML through one of the company's approved mechanisms, such as a maintained base image or internal package mirror. That provisioning happens outside this repository and outside the skills.

## URL-shaped OKF metadata

The following fields can contain URL-shaped strings because they are part of the OKF data model:

- concept `resource`
- `sources[].resource`
- `executor.resource`
- `attester.resource`
- Markdown link targets

The included scripts treat these values as text, paths, metadata, or graph labels. They do not retrieve their targets. An Attested Computation may access an external system only after separate authorization by the user or the host environment.

## Visualizer implementation

The original visualizer depended on remote browser libraries. The company-safe variant replaces that browser layer with embedded native functionality:

- SVG graph rendering in a virtual coordinate space
- directory-cluster layout for large bundles
- grid, concentric, and radial compatibility layouts
- wheel and pinch zoom
- pointer-drag panning
- zoom in/out, Fit, and Reset controls
- adaptive labels based on zoom level
- search, type filters, and directory-group filters
- click-to-inspect and double-click-to-focus behavior
- concept detail panel
- trust and staleness badges
- Markdown headings, lists, tables, code blocks, and inline formatting
- bundle links and backlinks

Each visible concept receives its own layout coordinate. Large bundles are grouped by parent directory instead of being compressed into one fixed-radius circle.

No third-party JavaScript files are vendored into the repository, which avoids both CDN access and large minified dependency blobs that can also trigger source scanning.

## Verification performed

- Python syntax compilation completed for the rewritten validator and visualizer.
- A sample OKF v0.1 bundle was migrated to v0.2.
- The migrated bundle was validated successfully without hard errors.
- An interactive HTML file was generated from the sample bundle.
- A synthetic 4,601-concept bundle was rendered with distinct clustered coordinates.
- The complete `NTUT-Vincent/TWFoodMCP` `main/knowledge` bundle was rendered successfully: 4,601 concepts, 58 directory groups, and 0 source-defined graph relationships.
- The generated TWFoodMCP HTML contained no external script source, external stylesheet, browser `fetch`, CDN, jsDelivr, or unpkg reference.
- The generated HTML's embedded JavaScript passed Node.js syntax validation.

## Scanner limitation

This audit covers intentional runtime behavior and obvious static network surfaces. A company scanner may enforce additional policies, such as blocking particular licenses, dependency names, executable scripts, encoded content, or URL-shaped strings in specifications. A failed scan should be reviewed against the scanner's exact rule identifier rather than worked around blindly.
