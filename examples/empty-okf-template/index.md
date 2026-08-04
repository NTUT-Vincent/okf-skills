---
okf_version: "0.2"
---

# Structured OKF Template

This bundle is intentionally empty of real domain knowledge. It demonstrates a multi-directory OKF structure with placeholder concepts and working cross-links.

## Bundle structure

```text
empty-okf-template/
├── index.md
├── log.md
├── tools/
│   ├── index.md
│   └── example-tool.md
├── procedures/
│   ├── index.md
│   └── example-procedure.md
├── metrics/
│   ├── index.md
│   └── example-metric.md
└── references/
    ├── index.md
    └── example-reference.md
```

## Example concepts

- [Example Tool](tools/example-tool.md)
- [Example Procedure](procedures/example-procedure.md)
- [Example Metric](metrics/example-metric.md)
- [Example Reference](references/example-reference.md)

## Usage

1. Copy the relevant example file.
2. Rename it with a stable kebab-case filename.
3. Replace every placeholder and remove unused optional fields.
4. Add authoritative sources for important claims.
5. Connect related concepts with Markdown links.
6. Add a real `verified` record only after review.
7. Update the nearest `index.md` and the root `log.md`.
