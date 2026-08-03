---
okf_version: "0.2"
---

# Team Tool OKF Template

This is a small, fictional OKF bundle for team training. It demonstrates how to document a **Tool**, its operating **Procedure**, a related **Metric**, and the **Reference** used as evidence.

The bundle uses `Tool` as the team term for equipment or systems.

## How to use this template

1. Copy this directory into your project.
2. Replace the fictional examples with your own domain knowledge.
3. Keep one clear knowledge unit in each concept file.
4. Add each new concept to the nearest `index.md`.
5. Record meaningful changes in `log.md`.
6. Validate before review:

```bash
uv run skills/validate/scripts/okf_validate.py examples/team-tool-template --strict
```

7. Optionally render the bundle as a graph:

```bash
uv run skills/visualize/scripts/okf_visualize.py examples/team-tool-template
```

## Concepts

### Tools

- [Inspection Tool A01](tools/inspection-tool-a01.md) — fictional production inspection tool.

### Procedures

- [Weekly Inspection](procedures/weekly-inspection.md) — weekly operating and maintenance check.

### Metrics

- [Tool Availability](metrics/tool-availability.md) — availability calculation and interpretation.

### References

- [Inspection Tool A01 Manual](references/inspection-tool-a01-manual.md) — fictional source document used by the examples.

### Reusable template

- [Concept Template](templates/concept-template.md) — copy this file when creating a new concept.
