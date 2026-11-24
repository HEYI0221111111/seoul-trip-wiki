# 首爾旅遊攻略 Wiki

給台灣旅客的首爾通用攻略：美食、購物逛街、傳統文化與市場、韓國必買。
參考 Andrej Karpathy 的 LLM Wiki 做法，由 AI 從網路資料與使用者提供的文章持續整理成互相連結的 Markdown 攻略，再自動產生網站。

## 怎麼看

- 網頁：雙擊 `docs/index.html`（或 GitHub Pages 網址）。
- 原始攻略：`wiki/` 資料夾，入口是 `wiki/overview.md` 與 `wiki/index.md`。

## 怎麼讓 AI 繼續擴充

在本資料夾開啟 Claude Code（或其他 AI agent），它會先讀 `CLAUDE.md`。常用指令：

| 說 | AI 會做 |
|----|---------|
| `蒐集 益善洞餐廳` | 上網找 3 個以上來源，摘要存進 `raw/web/`，再整理進攻略 |
| `ingest raw/articles/某篇文章.md` | 收錄你丟進來的文章 |
| `弘大半天怎麼逛？` | 用攻略回答，好的回答可以存成新頁面 |
| `lint` | 檢查過期資料、矛盾、單一來源、斷鏈 |
| `build` | 重新產生網站 |

## 資料夾

- `raw/`：原始資料。`raw/web/` 是 AI 蒐集的摘要（只有網址與重點）；`raw/articles/` 是你丟進來的文章，不上傳 GitHub。
- `wiki/`：AI 整理的攻略頁面。
- `templates/`：各類頁面範本。
- `web/`：網站產生器，規則見 `web/CLAUDE.md`。
- `docs/`：產生出來的網站。
- `tools/lint.py`：連結檢查。

## 版權說明

網站上的文字都是 AI 讀過多份資料後，用自己的話重新整理的內容，並附出處連結；不轉載原文、不使用網路圖片。
