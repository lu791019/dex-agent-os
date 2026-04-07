---
source: "[[string-length-utf8-utf16-grapheme/TOPIC]]"
topic: string-length-utf8-utf16-grapheme
channel: threads
status: draft
created: 2026-03-29
---

你以為 `len()` 回傳的就是字數？

上週串接 Threads API，Python 算出來明明在 500 字限制內，送出去直接吃一個 400 錯誤。

查了半天才搞懂：Threads 用的是 UTF-16 code unit 計算長度。

一個家庭 emoji，你眼睛看到 1 個字。
Python `len()` 告訴你 7。
UTF-16 說它是 11。

你以為還有餘裕，API 說你早就超了。

---

字串長度至少有三種算法，給你三個完全不同的數字：

**UTF-8 byte**——一個中文字佔 3 bytes，英文佔 1。API 用 byte 做限制的話，你的中文內容能塞的量只有英文的三分之一。

**UTF-16 code unit**——JavaScript `.length` 算的是這個，Python `len()` 算的是 code point。同一個字串兩個語言跑出不同數字，跨服務串接最容易爆。

**Grapheme cluster**——人眼看到的「一個字」。Python 要裝 `grapheme`，JavaScript 用 `Intl.Segmenter`。沒踩坑的人根本不知道這層存在。

下次 API 回你字數超限，別急著砍字——先搞清楚它數的到底是哪一種長度。

---

關於檔案寫入：看起來 `520_Topics/` 已經存在這個主題檔了（status 顯示 drafting，Threads 也已勾選完成）。你需要我把這篇草稿寫入 `530_Channels/threads/` 嗎？給我一聲我就存。
