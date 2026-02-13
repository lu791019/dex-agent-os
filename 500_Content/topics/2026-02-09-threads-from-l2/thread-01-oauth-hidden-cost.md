---
topic: 2026-02-09-threads-from-l2
channel: threads
status: draft
created: 2026-02-09
source: L2 精煉日記
theme: OAuth 是獨立開發者的隱形成本
---

Meta 的 OAuth 流程設計，根本不把個人開發者當人看。

我花了 20 分鐘試了 3 種 redirect URI 方案，localhost 全部被封殺。

大廠的 OAuth 假設你有公開 domain、有正式環境、有一整個 infra team 幫你搞。

但我只是想抓自己的 Threads 貼文欸。

最後解法？直接用 Dashboard 的用戶權杖產生器，30 秒搞定。

這不是我技術不行，是平台的流程根本不是為你設計的。

下次遇到 OAuth 卡關，先別硬幹。
先去查平台限制文件，確認它有沒有幫個人開發者留一條路。

沒有的話，繞過它，省下來的時間拿去做真正重要的事。

你有被 OAuth 搞到懷疑人生過嗎？
