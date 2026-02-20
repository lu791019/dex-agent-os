---
topic: storage-abstraction-worth-it-for-small-projects
channel: threads
status: draft
created: 2026-02-19
---

草稿已產出，等你授權寫入。以下是貼文內容：

---

你以為抽象層是大專案的事？其實 50 行 Python 就能讓小專案脫胎換骨。

一個 StorageBackend Protocol，定義 read / write / list / delete 四個方法，30 分鐘寫完。換來的是：

- 測試不用再 mock S3 client、處理 credential、清理測試檔案。注入 in-memory backend，瞬間跑完，零副作用
- 開發用 local file、上線切 S3，業務邏輯一行不改。環境切換成本趨近於零
- 重構時不用怕牽一髮動全身，因為 storage 的邊界已經畫好了
- YAGNI 原則的經典反例——storage backend 幾乎一定會變，這是少數「一開始就該抽」的介面

以前我也覺得小專案硬寫 file path 就好，直到真的要換環境時才發現改到懷疑人生。加了抽象層之後，重構成本從「砍掉重練」變成「換一行 injection」。

50 行程式碼，換來的是你未來每一次部署的自由度。這筆帳怎麼算都划算。

---

存檔路徑：`530_Channels/threads/2026-02-19/storage-abstraction-worth-it-for-small-projects.md`

請授權寫入，我同時會更新 TOPIC.md 的 Threads checkbox。
