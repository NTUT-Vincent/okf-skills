# OKF Core Skills — Company-Safe Distribution

這個分支將原始 `okf-skills` 精簡成可直接複製到公司環境使用的核心版本，保留：

- `okf`：建立、維護與讀取 OKF bundle
- `validate`：deterministic OKF v0.2 validator 與 v0.1 → v0.2 migration
- `visualize`：產生單檔互動式 `viz.html`
- `okf_init.py`：建立初始 bundle

## 為公司掃描環境調整的地方

原版核心流程與 OKF 規則維持不變，但移除了會造成下載或程式碼掃描疑慮的行為：

- 不從 CDN 載入 JavaScript
- 不執行 `pip install`
- 不透過 `uv run` 自動解析或下載 dependency
- 不包含 browser `fetch`、Python HTTP client、`curl` 或 `wget`
- 不把 OKF metadata 中的 URL 視為自動連線許可
- Attested Computation 必須由使用者或公司核准的 host policy 明確授權後才能執行

新的 `viz.html` 只包含內嵌 CSS 與 vanilla JavaScript。產生與開啟視覺化檔案時，不需要下載 Cytoscape、Marked、DOMPurify 或其他瀏覽器套件。

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

另外保留 `LICENSE`、`NOTICE` 與 `EXTERNAL-NETWORK-AUDIT.md`。

## 執行環境

`okf_init.py` 只使用 Python standard library。

`validate` 與 `visualize` 需要公司核准的 Python 環境已經包含 PyYAML。repo 本身不會安裝套件；請由公司既有的 base image、internal package mirror 或核准的開發環境提供。

## 安裝

將整個 `skills/` 複製到 Agent 工具支援的 skills 目錄，例如：

```text
<your-project>/.claude/skills/
├── okf/
├── validate/
└── visualize/
```

三個資料夾都應保留，因為主 `okf` skill 會使用 initializer 與 companion validator。

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

實際能否通過公司掃描仍取決於公司規則；這個分支已去除已知的 runtime download、CDN script 與直接網路呼叫面。
