---
type: Metric
title: Tool Availability
description: Percentage of scheduled production time that a Tool is available for use.
tags:
  - availability
  - operations
  - teaching-example
sources:
  - id: tool-manual
    resource: ../references/inspection-tool-a01-manual.md
    title: Inspection Tool A01 Manual
    author: team:equipment
    last_modified: 2026-08-01
generated:
  by: process:okf-teaching-template
  at: 2026-08-03T09:00:00Z
verified:
  - by: human:example-reviewer
    at: 2026-08-03T09:30:00Z
status: stable
stale_after: 2027-02-03
---

# Definition

Tool Availability measures how much scheduled production time a Tool can actually be used.

# Formula

```text
Tool Availability = Available Time / Scheduled Time × 100%
```

# Interpretation

- A higher value means the Tool spent more scheduled time ready for production.
- Planned maintenance should be classified consistently before comparing periods.
- The metric should not be used without checking the underlying downtime reasons.

# Example

If [Inspection Tool A01](../tools/inspection-tool-a01.md) is available for 152 hours during 160 scheduled hours, its availability is 95%.

# Related Knowledge

- [Inspection Tool A01](../tools/inspection-tool-a01.md)
- [Weekly Inspection](../procedures/weekly-inspection.md)

[^tool-manual]: Inspection Tool A01 Manual
