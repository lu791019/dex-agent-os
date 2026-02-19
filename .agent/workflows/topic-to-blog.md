---
description: "Topic to Blog — 主題轉部落格文章草稿"
---

# Topic to Blog — 主題轉部落格文章草稿

從 TOPIC.md 產出部落格文章草稿，遵循寫作風格規則和風格 DNA。

## 觸發方式
- 指令：`./bin/agent topic-to-blog <topic-slug>`
- 指令：`./bin/agent topic-to-blog <topic-slug> --force`
- IDE 內：`/topic-to-blog`

## 輸入來源
1. **主題檔案**：`520_Topics/<slug>/TOPIC.md`
2. **風格 DNA**：`800_System/references/style-dna/blog-dna.md`（如存在）
3. **寫作規則**：`canonical/rules/10-writing-style.md`

## 處理邏輯
1. 讀取 TOPIC.md 的核心論點和關鍵素材
2. 讀取 blog-dna.md（如存在）作為風格參考
3. 讀取寫作風格規則
4. LLM 產出部落格文章草稿：
   - SEO 友善標題
   - H2/H3 結構化段落
   - 800-1500 字
   - 適當穿插程式碼區塊（如主題相關）
   - 語氣：專業、有深度、有故事感
5. 更新 TOPIC.md 的「已產出」checklist

## 輸出
- 路徑：`530_Channels/blog/<created-date>/<slug>.md`
- 存在時：提示覆蓋或使用 --force

## 原則
- SEO 優先：標題含關鍵字，有 meta description
- 結構清晰：H2/H3 層次分明
- 程式碼區塊標註語言（如 `python`、`bash`）
- 每段有明確觀點，不灌水
- 有 DNA 時優先遵循 DNA 的具體模式
