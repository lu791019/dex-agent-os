---
type: dashboard
tags: [system]
---

# 知識庫儀表板

## 最近洞察
```dataview
TABLE date AS "日期", channel_tags AS "頻道", source AS "來源"
FROM "510_Insights"
SORT date DESC
LIMIT 15
```

## 主題進度
```dataview
TABLE status AS "狀態", source AS "來源洞察"
FROM "520_Topics"
WHERE file.name = "TOPIC"
SORT file.cday DESC
```

## 今日學習輸入
> 今天匯入的閱讀、文章、影片 — 自動從日期比對

```dataview
TABLE category AS "分類"
FROM "000_Inbox/readings" OR "300_Learning"
WHERE file.day = date(today)
SORT file.name ASC
```

## 最近學習消化
```dataview
TABLE date AS "日期", count AS "篇數", source AS "日記"
FROM "100_Journal/digest"
SORT date DESC
LIMIT 7
```

## 孤兒筆記
> 沒有任何連結的內容

```dataview
LIST
FROM "510_Insights" OR "520_Topics" OR "530_Channels"
WHERE length(file.inlinks) = 0 AND length(file.outlinks) = 0
LIMIT 15
```

## 書籍筆記
```dataview
LIST
FROM "300_Learning/input/books"
WHERE file.size > 100
SORT file.name ASC
```

## DayDreamDex CXO
```dataview
LIST
FROM "daydreamdex-kb"
WHERE file.name != "_CXO-MAP"
SORT file.folder ASC
```
