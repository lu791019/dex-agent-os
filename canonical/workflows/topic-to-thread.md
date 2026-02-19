# Topic to Thread — 主題轉 Threads 草稿

從 TOPIC.md 產出 Threads 草稿，遵循寫作風格規則和風格 DNA。

## 觸發方式
- 指令：`./bin/agent topic-to-thread <topic-slug>`
- 指令：`./bin/agent topic-to-thread <topic-slug> --force`
- IDE 內：`/topic-to-thread`

## 輸入來源
1. **主題檔案**：`520_Topics/<slug>/TOPIC.md`
2. **風格 DNA**：`800_System/references/style-dna/threads-dna.md`（如存在）
3. **寫作規則**：`canonical/rules/10-writing-style.md` 的 Threads 風格區段

## 處理邏輯
1. 讀取 TOPIC.md 的核心論點和關鍵素材
2. 讀取 threads-dna.md（如存在）作為風格參考
3. 讀取寫作風格規則
4. LLM 產出 Threads 草稿：
   - Hook → 核心觀點（條列 3-5 點）→ 收尾金句
   - 150-250 字
   - 語氣：專業但不官腔，有故事感
5. 更新 TOPIC.md 的「已產出」checklist

## 輸出
- 路徑：`530_Channels/threads/<created-date>/<slug>.md`
- 存在時：提示覆蓋或使用 --force

## 原則
- 「開場反差型」優先：「你以為 X，其實 Y」
- 用「你」直接對話，不用「大家」
- 不堆疊 emoji 或 hashtag
- 不雞湯、不空泛開場
- 有 DNA 時優先遵循 DNA 的具體模式
