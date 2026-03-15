
# Consultation Notes — 諮詢紀錄產生器

從諮詢對話逐字稿或筆記產出結構化諮詢紀錄，記錄對象背景、討論方向與建議。

## 觸發方式

- 指令：`./bin/agent consultation-notes --person "對象" --direction "方向" --source <來源>`
- IDE 內：`/consultation-notes`

## 輸入來源

1. **逐字稿檔案**：`--file <path>`
2. **Google Doc**：`--gdoc <doc-id>`
3. **Fireflies 會議**：`--fireflies <meeting-id>`
4. **手動筆記**：`--notes "重點筆記"`
5. **對象資訊**：`--person "名稱"` 必填
6. **諮詢方向**：`--direction "職涯/技術/產品"` 選填

## 處理邏輯

1. 讀取指定來源的諮詢內容
2. 檢查 `200_Work/consultations/` 是否有該對象的歷史紀錄
3. 將原始內容交給 LLM 提煉：
   - 對象背景摘要（首次諮詢時建立，後續更新）
   - 本次諮詢主題與方向
   - 關鍵討論內容（分主題條列）
   - 給出的建議與行動項目
   - 追蹤事項與下次預計討論
4. 組裝 frontmatter + 結構化內容

## 輸出

- 路徑：`200_Work/consultations/YYYY-MM-DD-<person-slug>.md`
- frontmatter：title / date / person / direction / source / type:consultation
- 如果已存在，詢問是否覆蓋或使用 `--force`

## 原則

- **以人為中心**：每次紀錄都要連結對象的完整脈絡
- **可追蹤**：建議事項要具體、可執行
- **隱私**：敏感資訊標記 `[REDACTED]`，不放進 git
- **繁體中文**
