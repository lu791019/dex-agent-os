---
description: "Topic to Facebook — 主題轉 Facebook 貼文草稿"
---

# Topic to Facebook — 主題轉 Facebook 貼文草稿

從 TOPIC.md 產出 Facebook 貼文草稿，遵循寫作風格規則和風格 DNA。

## 觸發方式
- 指令：`./bin/agent topic-to-fb <topic-slug>`
- 指令：`./bin/agent topic-to-fb <topic-slug> --force`
- IDE 內：`/topic-to-fb`

## 輸入來源
1. **主題檔案**：`500_Content/topics/<slug>/TOPIC.md`
2. **風格 DNA**：`800_System/references/style-dna/facebook-dna.md`（如存在）
3. **寫作規則**：`canonical/rules/10-writing-style.md`

## 處理邏輯
1. 讀取 TOPIC.md 的核心論點和關鍵素材
2. 讀取 facebook-dna.md（如存在）作為風格參考
3. 讀取寫作風格規則
4. LLM 產出 Facebook 貼文草稿：
   - 開場 Hook → 故事/觀點展開 → 開放式提問收尾
   - 300-500 字
   - 語氣：社群感，像跟朋友分享心得
5. 更新 TOPIC.md 的「已產出」checklist

## 輸出
- 路徑：`500_Content/topics/<slug>/fb-draft.md`
- 存在時：提示覆蓋或使用 --force

## 原則
- 社群感優先，鼓勵互動
- 用「你」直接對話
- 結尾開放式提問，邀請留言
- 不堆疊 emoji 或 hashtag
- 不雞湯、不空泛開場
- 有 DNA 時優先遵循 DNA 的具體模式
