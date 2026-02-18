---
title: Some notes on starting to use Django
source: https://jvns.ca/blog/2026/01/27/some-notes-on-starting-to-use-django/
type: articles
date: 2026-02-18
tags: [django, python, web-framework, sqlite, orm]
---
# Some notes on starting to use Django

## 一句話摘要
資深開發者初學 Django，喜歡其明確性、內建 admin 與 ORM 遷移的務實體驗。

## 核心觀點
1. **明確優於魔法**：Django 比 Rails 更 explicit，放下專案數月後回來仍能快速上手，因為路由、模板引用都能從 5 個主要檔案直接追溯
2. **內建 Admin 省大量工夫**：幾行程式碼就能客製 list_display、search_fields、ordering，免自建後台
3. **ORM 與自動 Migration 是殺手級功能**：`__` 語法簡潔表達多表 JOIN，資料模型變動頻繁時自動產生遷移腳本極為實用
4. **SQLite 生產環境可行**：小流量網站用 SQLite 取代 Postgres，備份只需 `VACUUM INTO` + 複製單一檔案，運維成本極低
5. **Batteries-included 哲學**：CSRF、CSP、Email 都內建，dev/prod 環境切換只需改 settings，降低整合第三方的需求

## 關鍵引述
> "It feels really good when every problem I'm ever going to have has been solved already 1000 times and I can just get stuff done easily."

> "Being able to abandon a project for months or years and then come back to it is really important to me, and Django feels easier to me because things are more explicit."

> "In my small Django project it feels like I just have 5 main files: urls.py, models.py, views.py, admin.py, and tests.py"

> "I definitely could write that query, but writing `product__order__email_hash` is a lot less typing, it feels a lot easier to read."

> "I'm realizing that being able to do migrations easily is important for me right now because I'm changing my data model fairly often as I figure out how I want it to work."

## 實作筆記
- **Django Admin 快速客製**：用 `@admin.register(Model)` 裝飾器 + `list_display`、`search_fields`、`readonly_fields`、`ordering` 屬性即可
- **ORM 多表查詢**：`__` 串接欄位名代表 JOIN，搭配 `ManyToManyField` 定義關聯，Django 自動處理中間表
- **自動 Migration**：修改 `models.py` 後執行 `python manage.py makemigrations` → `migrate`，生成的腳本可直接用
- **SQLite 生產部署**：參考 Django + SQLite in production 指南，適用於每日寫入數百次以下的場景
- **Email 環境切分**：`settings/dev.py` 用 `filebased.EmailBackend` 存檔不寄信；`settings/production.py` 用 SMTP，密碼從環境變數讀取
- **settings.py 風險**：變數名拼錯不會報錯，缺乏 LSP 支援——需額外注意 typo

## 我的想法
<!-- 手動補充 -->

## 可轉化為內容
- **Threads**：「選框架的關鍵不是效能，是你放下三個月後還能不能看懂」— 用 Django vs Rails 的 explicit vs magic 對比，延伸到工具選擇的長期思維
- **Threads**：「SQLite 能上 production 嗎？」— 拆解 jvns 的實戰經驗，破除「SQLite 只能開發用」的迷思
- **Newsletter**：「Old Boring Technology 的魅力」— 從 Django 切入，談選擇成熟技術的 ROI：文件完善、問題都被解過、社群厚實
- **Blog**：「Python 開發者的 Django 入門體驗整理」— 結合本文觀點 + 自己的補充，寫一篇實用導向的入門指南
