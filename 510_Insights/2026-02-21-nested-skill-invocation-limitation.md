---
date: 2026-02-21
source: 100_Journal/daily/2026-02-21.md
classification: content
channel_tags: ["Threads"]
status: raw
---

# 巢狀 skill 呼叫的限制

IDE skill 不能像函式一樣自由巢狀，這是 agent 架構的根本限制，不是 bug。

## 潛在切入角度
Threads 短文適合用「你以為是 bug，其實是 by design」的反直覺切角，帶出 agent 架構的 composability 議題。
