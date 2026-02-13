---
title: 多 AI IDE 協作的最佳實踐：canonical 單一真實來源
status: drafting
source: 500_Content/insights/2026-02-07-multi-ide-sync-best-practice.md
tags: [AI IDE, Developer Workflow, Claude Code, Cursor, Windsurf, Best Practice]
created: 2026-02-09
---

# 多 AI IDE 協作的最佳實踐：canonical 單一真實來源

## 核心論點
當你同時使用多個 AI IDE，最大的陷阱不是工具選擇，而是規則散落各處——「canonical 單一真實來源 + sync 腳本」才是讓所有 AI 助手行為一致的唯一正解。

## 關鍵素材
- **痛點場景**：Claude Code 用 `CLAUDE.md`、Cursor 用 `.mdc`（需 YAML frontmatter）、Windsurf / Antigravity 用 `.agent/` 三層結構——格式完全不同，手動維護多份規則必然失同步
- **canonical 架構**：所有規則寫在 `canonical/` 單一目錄，透過 `bin/sync` 腳本自動轉換格式、分發到各 IDE 的設定位置，修改只需改一處
- **sync 腳本實作細節**：需處理 YAML frontmatter 注入、`---` 分隔線誤判（awk 解析陷阱）、三層分級（rules 永遠載入 / workflows 觸發載入 / skills 按需載入）等技術眉角
- **AGENTS.md 公約數策略**：找出所有 IDE 都能讀取的「最大公約數」格式，放核心人格與共用規則，IDE 專屬設定才走各自格式
- **反面教材**：不用 sync 的後果——在 Cursor 改了 coding style 但 Claude Code 不知道，產出的程式碼風格不一致，review 時才發現要返工

## 頻道適合度
- ✅ **Threads**：適合先發觀點引爆討論。用一句話點出「你還在每個 AI IDE 各寫一份規則嗎？」搭配 canonical 架構圖，能快速引起多工具使用者的共鳴，互動潛力高
- ❌ **Facebook**：受眾偏泛，AI IDE 多工具協作的主題太 niche，觸及率和互動都不會好，不建議投放
- ✅ **Newsletter**：適合作為完整教學的發布管道。訂閱者多為開發者，能接受較長篇幅的技術內容，可附上 repo 結構圖和 sync 腳本片段，提供可直接複製的實作價值
- ✅ **Blog**：最適合的主力格式。可以完整比較 Claude Code / Cursor / Windsurf 的規則格式差異，展示 canonical + sync 的目錄結構與腳本實作，搭配前後對比圖，SEO 潛力佳（關鍵字：AI IDE workflow, CLAUDE.md, Cursor rules）

## 已產出的格式
- [x] Threads
- [ ] Facebook
- [ ] Newsletter
- [ ] Blog