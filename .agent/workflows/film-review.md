---
description: "Film Review — 影評產生器"
---

# Film Review — 影評產生器

從電影名稱和觀影筆記產出結構化影評。獨立 workflow，不走 topic-to-* 流程。

## 觸發方式
- 指令：`./bin/agent film-review --title "電影名" [--notes "筆記"] [--rating N]`
- 指令：`./bin/agent film-review --title "電影名" --force`
- IDE 內：`/film-review`

## 輸入來源
1. **電影名稱**：`--title` 必填參數
2. **觀影筆記**：`--notes` 選填，提供個人觀點素材
3. **評分**：`--rating` 選填，1-10 分
4. **風格 DNA**：`800_System/references/style-dna/film-review-dna.md`（如存在）
5. **寫作規則**：`canonical/rules/10-writing-style.md`

## 處理邏輯
1. 以電影名稱 + 觀影筆記為素材
2. 讀取 film-review-dna.md（如存在）
3. 讀取寫作風格規則
4. LLM 產出影評：
   - 500-1000 字
   - 結構：一句話短評 → 劇情概述（不劇透）→ 觀點分析 → 推薦指數
   - 語氣：個人化，有洞察
5. 組裝 frontmatter（含評分）+ 內容

## 輸出
- 路徑：`600_Life/film/reviews/YYYY-MM-DD-<slug>.md`
- slug 由電影名稱自動產生
- 存在時：提示覆蓋或使用 --force

## 原則
- 不劇透核心劇情轉折
- 有個人觀點，不只是劇情摘要
- 可以連結到自身經驗或生活感悟
- 有 DNA 時優先遵循 DNA 的具體模式
