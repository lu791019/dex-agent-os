---
date: 2026-03-29
source: "[[2026-03-29]]"
classification: content
channel_tags: ["Threads", "Blog"]
status: raw
---

# 你的字串長度不是你以為的長度

UTF-8 / UTF-16 / grapheme cluster 三種計算方式，在不同 API 會咬你一口。這是每個串接第三方 API 的工程師都會踩的坑。

## 潛在切入角度
可以寫成工程踩坑教學，用實際案例（如 Threads API 字數限制、emoji 長度計算）展示三種長度的差異；Blog 版可加上各語言的處理方式比較表
