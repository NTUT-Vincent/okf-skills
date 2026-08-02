# OKF Core Skills

這個分支將原始 `okf-skills` 精簡成可直接複製使用的核心版本。

核心功能維持原版，不再把 `validate` 與 `visualize` 視為可移除的周邊：

- `okf`：建立、維護與讀取 OKF bundle
- `validate`：以 deterministic Python checker 驗證 OKF v0.2，並支援 v0.1 → v0.2 migration
- `visualize`：將 bundle 產生為互動式 `viz.html`
- `okf_init.py`：建立初始 bundle

上述三份 `SKILL.md` 與三支 Python script 直接使用原始專案內容，沒有重新撰寫或改變原本流程。

## 保留的檔案

```text
skills/
├── okf/
│   ├── SKILL.md
│   ├── scripts/okf_init.py
│   ├── reference/
│   │   ├── SPEC.md
│   │   └── APACHE-2.0.txt
│   └── templates/
│       ├── concept.md
│       ├── index.md
│       └── log.md
├── validate/
│   ├── SKILL.md
│   └── scripts/okf_validate.py
└── visualize/
    ├── SKILL.md
    └── scripts/okf_visualize.py
```

另外保留：

- `LICENSE`
- `NOTICE`
- `EXTERNAL-NETWORK-AUDIT.md`

## 移除的周邊

這個分支移除不影響三個核心 skill 使用的發行與展示內容：

- Claude plugin / marketplace manifests
- GitHub Action 與 CI workflow
- benchmark 與測試資料
- GitHub Pages、demo、預先產生的 HTML 與圖片
- sample bundle
- repo 自身的 `.okf/` dogfooding 文件
- changelog、Makefile 與自動 upkeep snippet

## 安裝

將整個 `skills/` 複製到 Agent 工具支援的 skills 目錄。例如 Claude Code 專案：

```text
<your-project>/.claude/skills/
├── okf/
├── validate/
└── visualize/
```

三個資料夾都應保留，因為主 `okf` skill 會呼叫 companion `validate` skill，並使用自己的 `okf_init.py`。

## 使用

```text
使用 OKF skill，將這個 repo 的架構整理到 .okf/。
```

```text
/validate .okf --strict
```

```text
/visualize .okf
```

實際 slash command 名稱會依宿主工具的 skill namespace 而異；原專案的 Claude plugin 使用 `/okf:okf`、`/okf:validate`、`/okf:visualize`。

## 執行需求與網路注意事項

Python scripts 使用 PyYAML。原版建議透過 `uv run` 執行，也提供 `pip install pyyaml` fallback。

核心 Python 邏輯本身不會直接呼叫 HTTP API，但以下情況可能對外連線：

- `uv` 或 `pip` 在本機沒有 PyYAML 時，可能連到 PyPI 或設定的 package registry。
- 開啟 visualizer 產生的 `viz.html` 時，瀏覽器會向 jsDelivr 載入 Cytoscape、marked 與 DOMPurify。
- OKF concept 宣告的 Attested Computation 可能指向資料庫、SQL executor、script 或外部 API；是否執行取決於 Agent 與 bundle 內容。

完整盤點請見 [`EXTERNAL-NETWORK-AUDIT.md`](EXTERNAL-NETWORK-AUDIT.md)。

## License

本精簡版本保留上游專案的 MIT License。Vendored OKF specification 來自 Google Cloud reference repository，並保留原始 Apache-2.0 授權與 NOTICE。
