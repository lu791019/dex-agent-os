# Topic to Short Video — 主題轉短影音腳本

從 TOPIC.md 產出短影音（Reels / Shorts / TikTok）腳本草稿。

## 觸發方式
- 指令：`./bin/agent topic-to-short-video <topic-slug>`
- 指令：`./bin/agent topic-to-short-video <topic-slug> --force`
- IDE 內：`/topic-to-short-video`

## 輸入來源
1. **主題檔案**：`500_Content/topics/<slug>/TOPIC.md`
2. **寫作規則**：`canonical/rules/10-writing-style.md`

## 處理邏輯
1. 讀取 TOPIC.md 的核心論點和關鍵素材
2. 讀取寫作風格規則
3. LLM 產出短影音腳本：
   - 15-60 秒
   - `[畫面]` 視覺提示標記
   - Hook（前 3 秒）→ 核心內容 → CTA
   - 口語化，適合鏡頭前唸
4. 更新 TOPIC.md 的「已產出」checklist

## 輸出
- 路徑：`500_Content/topics/<slug>/short-video-script.md`
- 存在時：提示覆蓋或使用 --force

## 原則
- 前 3 秒必須有 Hook，抓住注意力
- 每段搭配 `[畫面]` 提示，方便拍攝
- 口語化，不要書面語
- 一個影片只講一個核心觀點
- 結尾明確 CTA（追蹤、留言、分享）
- 無需風格 DNA（短影音風格由拍攝者決定）
