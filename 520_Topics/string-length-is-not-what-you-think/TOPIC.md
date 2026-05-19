---
```markdown
notion_id: 36552f3f-eb91-8116-8f64-edbe220b6d75
---
title: 你的字串長度不是你以為的長度
status: drafting
source: "[[2026-03-29-string-length-is-not-what-you-think]]"
tags: [Python, Unicode, UTF-8, API整合, 踩坑經驗]
created: 2026-03-29
---

# 你的字串長度不是你以為的長度

## 核心論點
每次你用 `len()` 算字串長度，拿到的數字取決於語言和編碼方式——UTF-8 算 bytes、UTF-16 算 code units、grapheme cluster 算人眼看到的字元，三者可以差到三倍以上，而第三方 API 不會告訴你它用哪一種。

## 關鍵素材
1. **Emoji 長度炸彈**：一個 👨‍👩‍👧‍👦（家庭 emoji）在 Python `len()` 是 7（code points），在 JavaScript `.length` 是 11（UTF-16 code units），在 UTF-8 是 25 bytes，但人眼看到的是 1 個字——用這個例子一秒說明三種計算方式的差異
2. **Twitter/Threads API 的字數限制**：社群平台的字數上限用的是 NFC 正規化後的 code point 計算，不是你 console 印出來的 `len()`，中文、emoji、組合字元都會讓你「明明沒超過卻被 API 拒絕」
3. **各語言標準庫的處理方式差異**：Python 的 `len()` 算 code points、JavaScript 的 `.length` 算 UTF-16 code units、Rust 的 `.len()` 算 bytes——同一個字串在三個語言拿到三個不同數字，這不是 bug，是 by design
4. **資料庫截斷的無聲錯誤**：MySQL 的 `VARCHAR(255)` 在 utf8mb4 下是 255 個 code points，但 `TEXT` 欄位的 max length 是 bytes——同一個資料庫裡兩種欄位用不同計算方式，存入時不報錯但靜默截斷
5. **grapheme cluster 才是正確答案**：ICU 的 grapheme cluster 分割才符合「人類直覺的一個字」，Python 可用 `grapheme` 套件、JavaScript 可用 `Intl.Segmenter`——但多數工程師不知道這些工具存在

## 頻道適合度
- ✅ **Threads**：用一個 emoji 展示三種長度的視覺衝擊，天然適合短文踩坑分享，工程師看到數字差異會直接轉發，主文放 emoji 範例 + 一句結論，串文補各語言對照表
- ✅ **Blog**：適合寫成完整技術文章，可以放各語言標準庫比較表、資料庫欄位行為對照、以及「正確做法」的程式碼範例，Blog 格式允許深度展開每個素材點
- ✅ **Facebook**：可以用「你以為 len() 回傳的是字數？」當 hook，適合技術社群轉發討論，但需要把程式碼範例精簡成截圖或短片段，避免排版跑掉
- ❌ **Newsletter**：主題太聚焦單一技術細節，電子報讀者期待的是綜合觀點或趨勢洞察，除非包在「本週踩坑筆記」的專欄框架內，否則單獨發不夠撐一期

## 已產出的格式
- [x] Threads
- [x] Facebook
- [ ] Newsletter
- [ ] Blog
- [ ] ShortVideo
- [ ] Podcast
```

---

寫入檔案時遇到權限問題，請授權後我再寫入 `520_Topics/string-length-is-not-what-you-think/TOPIC.md`，或你可以直接複製上面的內容。