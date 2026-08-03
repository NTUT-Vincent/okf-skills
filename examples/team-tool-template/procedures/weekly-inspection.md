---
type: Procedure
title: Weekly Inspection
description: Fictional weekly inspection procedure for Inspection Tool A01.
tags:
  - inspection
  - maintenance
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

# Purpose

Confirm that [Inspection Tool A01](../tools/inspection-tool-a01.md) is safe and ready for production use.

# Preconditions

- The Tool is in standby mode.
- No unit is inside the inspection chamber.
- The operator has access to the current Tool manual.

# Steps

1. Review the active alarm list.
2. Inspect the sensor area for contamination.
3. Run the built-in self-test.
4. Record the result in the maintenance log.
5. Escalate any failed critical check before returning the Tool to production.[^tool-manual]

# Completion Criteria

The procedure is complete when the self-test passes and no unresolved critical alarm remains.

# Related Knowledge

- [Inspection Tool A01](../tools/inspection-tool-a01.md)
- [Tool Availability](../metrics/tool-availability.md)

[^tool-manual]: Inspection Tool A01 Manual
