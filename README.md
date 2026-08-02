# OKF Local-Only Skill

這個分支是從原始 `okf-skills` 精簡出的 **純本地版本**，用途是讓 Claude Code 或其他支援 Agent Skill 的工具，直接建立、維護、讀取與人工檢查 Open Knowledge Format (OKF) v0.2 bundle。

`skills/okf/SKILL.md` 以原版內容為基準，保留原本的章節順序、核心措辭、觸發描述、OKF 規則與 produce / maintain / consume 流程；只有涉及執行腳本、安裝套件、外部連線或執行 computation 的段落做必要修改。

## 這個版本保留什麼

- OKF v0.2 的 canonical `SPEC.md`
- 建立、維護、讀取 OKF bundle 的原始 skill 主體內容
- 原版的 trigger 描述與 produce / maintain / consume 結構
- concept、index、log 範本
- provenance、trust、lifecycle、attestation 等 v0.2 撰寫規則
- 不依賴程式執行的本地結構檢查清單

## 這個版本移除什麼

- Python 初始化、驗證與視覺化腳本
- `Bash` tool 權限
- `uv`、`pip`、PyPI 套件安裝
- Claude plugin / marketplace 包裝
- `skills.sh` / `npx` 安裝流程
- GitHub Action、CI workflow、測試、benchmark、demo 與 GitHub Pages
- 會在瀏覽器載入 CDN JavaScript 的視覺化頁面
- 自動執行 Attested Computation、SQL、資料庫或外部 executor 的行為

因此，本分支內的 skill 本身只會要求 Agent 使用本地的 `Read`、`Write`、`Edit`、`Grep`、`Glob` 操作 Markdown 檔案。

## 安裝

把 `skills/okf` 整個資料夾複製到你的專案：

```text
<your-project>/.claude/skills/okf/
```

或放到你使用的 Agent 工具所支援的 skills 目錄。最終需確保以下檔案仍保持相對位置：

```text
okf/
├── SKILL.md
├── reference/
│   ├── SPEC.md
│   └── APACHE-2.0.txt
└── templates/
    ├── concept.md
    ├── index.md
    └── log.md
```

## 使用方式

可直接要求 Agent：

```text
使用 OKF skill，將這個 repo 的系統架構整理到 .okf/。
```

```text
使用 OKF skill，更新 .okf/ 中受到這次程式修改影響的概念。
```

```text
使用 OKF skill，先讀取 .okf/index.md，再回答這個系統為什麼採用目前架構。
```

原版對存在 OKF bundle 的 repository 所描述的觸發情境仍保留，但本地版不具有 Bash、hook、CI 或背景程序，因此不會自行執行腳本或對外連線。

## 網路與外部 API

完整盤點請看 [`EXTERNAL-NETWORK-AUDIT.md`](EXTERNAL-NETWORK-AUDIT.md)。

重點：

- `resource`、`sources[].resource` 可以包含 URL，但在此版本中只當作 metadata 儲存，不會自動開啟或抓取。
- `Attested Computation` 只記錄 contract，不執行 `executor`、SQL、script 或 API。
- 若宿主 Agent 在 skill 之外仍具有 browser、MCP 或 network tool，那是宿主權限；本 skill 不會主動要求使用它們。需要硬隔離時，仍應在宿主工具層停用網路與外部 connector。

## License

本精簡版保留上游專案的 MIT License。Vendored OKF specification 來自 Google Cloud reference repository，保留原始 Apache-2.0 標示與授權文字。
