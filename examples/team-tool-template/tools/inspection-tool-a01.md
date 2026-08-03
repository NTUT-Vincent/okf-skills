---
type: Tool
title: Inspection Tool A01
description: Fictional production Tool used to inspect finished units before release.
resource: tool://inspection/A01
tags:
  - inspection
  - production
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

# Overview

Inspection Tool A01 is a fictional Tool used in this teaching bundle. It checks finished units and records whether each unit passes the release criteria.

# Operating Rules

- Run the startup check before the first inspection of each shift.
- Do not release a unit when the Tool reports an unresolved critical alarm.
- Perform the weekly inspection every seven days.[^tool-manual]

# Related Knowledge

- Follow the [Weekly Inspection](../procedures/weekly-inspection.md).
- Track performance with [Tool Availability](../metrics/tool-availability.md).

# Notes

The identifiers, reviewer, dates, and process names in this file are fictional examples. Replace them before using the template in a real project.

[^tool-manual]: Inspection Tool A01 Manual
