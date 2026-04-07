---
source: "[[string-length-is-not-what-you-think/TOPIC]]"
topic: string-length-is-not-what-you-think
channel: threads
status: draft
created: 2026-03-29
---

【主文】

你以為 len() 回傳的是字數？

一個家庭 emoji（👨‍👩‍👧‍👦），人眼看是 1 個字。
Python 說 7，JavaScript 說 11，UTF-8 說 25。

三個答案全部都對。因為它們量的根本不是同一個東西。

而你串的那個 API，不會告訴你它用哪一種。

【串文】

社群平台的字數上限用 NFC 正規化的 code points，不是你 console 的 len()——中文加 emoji，「明明沒超過」卻被 API 打回來。

MySQL 的 VARCHAR 算 code points，TEXT 算 bytes。同一個資料庫兩套規則，存入不報錯，靜默截斷。

真正符合人類直覺的算法叫 grapheme cluster，Python 有 grapheme 套件、JS 有 Intl.Segmenter。但多數工程師不知道它存在。

下次 debug「字串長度不對」，先問自己：你量的到底是什麼。
