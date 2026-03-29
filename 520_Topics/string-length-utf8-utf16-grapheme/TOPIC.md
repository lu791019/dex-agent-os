---

```markdown
---
title: 你的字串長度不是你以為的長度
status: drafting
source: 510_Insights/2026-03-29-string-length-utf8-utf16-grapheme.md
tags: [Python, API, Unicode, 工程踩坑, 字串處理]
created: 2026-03-29
---

# 你的字串長度不是你以為的長度

## 核心論點
每個串接第三方 API 的工程師都會踩到字串長度的坑——因為 UTF-8、UTF-16、grapheme cluster 三種計算方式給你的數字完全不同，而你用的 `len()` 很可能不是 API 要的那個。

## 關鍵素材
1. **Threads API 的 500 字限制**：官方用的是 UTF-16 code unit 計算，一個 emoji（如 👨‍👩‍👧‍👦）在 UTF-16 可能是 11 個 code unit，但使用者眼中只有 1 個字。你以為還有餘裕，API 直接回你 400 錯誤。
2. **Python `len()` vs JavaScript `.length` 的差異**：Python 3 的 `len()` 算的是 Unicode code point，JavaScript 的 `.length` 算的是 UTF-16 code unit。同一個字串在兩個語言拿到不同數字，跨服務溝通時最容易出事。
3. **Emoji 組合序列的長度爆炸**：一個膚色 emoji 🧑🏽 是 2 個 code point、4 個 UTF-16 code unit，但 grapheme cluster 只有 1 個。家庭 emoji 👨‍👩‍👧‍👦 更誇張——7 個 code point，用 ZWJ 串起來。
4. **中日韓文字的 byte 陷阱**：一個中文字在 UTF-8 佔 3 bytes、UTF-16 佔 2 bytes。如果 API 是用 byte 長度做限制（如某些資料庫的 VARCHAR），你的中文內容能塞的量只有英文的三分之一。
5. **各語言的 grapheme cluster 正解**：Python 用 `grapheme` 套件、JavaScript 用 `Intl.Segmenter`、Go 用 `unicode/utf8` + `rivo/uniseg`——知道問題在哪之後，每個語言都有解法，但沒踩過坑的人根本不知道要找。

## 頻道適合度
- ✅ **Threads**：非常適合。用「你以為 len() 就是字數？」當開場就能勾住工程師，搭配一張 emoji 長度對照表截圖，視覺衝擊強。500 字以內講完一個案例剛好。
- ✅ **Blog**：最適合的長文載體。可以展開完整的語言比較表（Python / JavaScript / Go / Rust）、放程式碼片段、附上 API 文件截圖佐證。適合做成「工程踩坑教學」系列文章。
- ❌ **Facebook**：工程細節太硬，FB 受眾偏泛。除非改寫成「你發的 emoji 其實比你想的大 10 倍」這種大眾科普角度，否則互動率會很低。
- ✅ **Newsletter**：適合作為技術電子報的實戰專欄，讀者本身是工程師，可以附程式碼範例和踩坑故事，深度介於 Threads 和 Blog 之間。

## 已產出的格式
- [x] Threads
- [x] Facebook
- [ ] Newsletter
- [ ] Blog
- [ ] ShortVideo
- [ ] Podcast
```

---

檔案寫入遇到權限限制，需要你授權寫入 `520_Topics/` 目錄。要我再試一次寫入嗎？