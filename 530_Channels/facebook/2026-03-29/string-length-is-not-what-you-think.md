---
source: "[[string-length-is-not-what-you-think/TOPIC]]"
topic: string-length-is-not-what-you-think
channel: facebook
status: draft
created: 2026-03-29
---

`len("👨‍👩‍👧‍👦")` 回傳多少？

如果你直覺回答 1，恭喜，你跟大多數工程師一樣——答錯了。

這個家庭 emoji，在 Python 裡 `len()` 告訴你是 7，在 JavaScript `.length` 說是 11，換成 UTF-8 bytes 算是 25。但你眼睛看到的，就是一個圖案。

這不是 bug，是 by design。

我最近在串接社群 API 的時候被這件事狠狠教訓了一次。明明在本地算字數沒超過限制，送出去就被 API 打回來。查了才發現，平台用的是 NFC 正規化後的 code point 計算，跟我在 Python console 印出來的 `len()` 根本是兩回事。中文、emoji、組合字元，每一種都是坑。

更陰的是資料庫。MySQL 的 `VARCHAR(255)` 在 utf8mb4 下算的是 code points，但 `TEXT` 欄位的上限算的是 bytes——同一個資料庫裡，兩種欄位用不同的尺。存進去不會報錯，只會靜默截斷你的資料。等你發現的時候，通常是用戶來抱怨了。

問題的根源在於：大多數語言的標準庫用最方便實作的方式算「長度」，不是用人類直覺的方式。Python 算 code points、JavaScript 算 UTF-16 code units、Rust 算 bytes。同一個字串，三個語言三個數字。

真正符合「人眼看到的一個字」的答案是 grapheme cluster。Python 有 `grapheme` 套件，JavaScript 有 `Intl.Segmenter`，但多數人根本不知道這些東西存在，直到踩坑之後。

你在工作中被字串長度坑過嗎？是哪個場景？
