---
topic: 2026-02-09-threads-from-dayflow-l1
channel: threads
status: draft
created: 2026-02-09
source: Dayflow + L1 工作日誌
theme: Meta 的 OAuth 封殺讓我學到的事
---

嘗試了 3 次接 Threads API
http localhost 被擋
https localhost 也被擋
我直接傻眼

Meta 把本機開發的 redirect URI 全封殺了
不管你怎麼繞都不行

最後解法？
放棄正規 OAuth flow
直接用「用戶權杖產生器」手動拿 token

聽起來很 low 對吧

但做產品的人都知道
不是每個問題都值得你花時間硬解
有些牆就是繞過去比較快

花 3 小時跟 Meta 的安全策略搏鬥
不如 10 分鐘換條路把東西做出來

工程師最該練的能力不是死磕
是判斷什麼時候該放手
