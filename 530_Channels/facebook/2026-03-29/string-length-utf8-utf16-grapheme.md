---
source: "[[string-length-utf8-utf16-grapheme/TOPIC]]"
topic: string-length-utf8-utf16-grapheme
channel: facebook
status: draft
created: 2026-03-29
---

串接 Threads API 發貼文，字數明明不到 500，API 卻直接回 400 錯誤。

反覆用計算器數了好幾次，480 字，怎麼看都在限制內。

翻了 API 文件才搞懂——Threads 說的「500 字」，算的不是你以為的那種字數。它用的是 UTF-16 code unit。

一個家庭 emoji 👨‍👩‍👧‍👦，你的眼睛看到 1 個字元，UTF-16 算出來是 11 個。你以為還有 20 字的餘裕，實際上早就超標了。

更麻煩的是，同一個字串丟進 Python 和 JavaScript，「長度」竟然不一樣。Python 的 `len()` 算的是 Unicode code point，JavaScript 的 `.length` 算的是 UTF-16 code unit。前後端用不同語言做字數驗證？恭喜，你剛剛製造了一個超難重現的 bug。

中文也逃不掉。一個中文字在 UTF-8 佔 3 bytes，如果資料庫是用 byte 做長度限制，你能存的中文量只有英文的三分之一。那些「明明沒超長卻被截斷」的靈異現象，多半出在這裡。

搞清楚問題之後，其實每個語言都有對應的解法——Python 有 `grapheme` 套件、JavaScript 有 `Intl.Segmenter`、Go 有 `rivo/uniseg`。工具都在，但沒被坑過的人根本不知道要找。

說到底，`len()` 回傳的數字從來不是問題，問題是你以為那個數字代表什麼。

你有踩過類似的字串長度陷阱嗎？是在哪個 API 或資料庫中招的？

---

關於檔案寫入——要的話我可以幫你存到 `530_Channels/facebook/`，你說一聲就寫入。
