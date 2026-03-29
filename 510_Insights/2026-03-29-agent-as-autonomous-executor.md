---
date: 2026-03-29
source: 100_Journal/digest/2026-03-29-digest.md
classification: content
channel_tags: ["Threads", "Blog"]
status: raw
---

# AI Agent 從對話工具演化為自主執行系統

Autoresearch（Karpathy 的自動迭代框架）和 OpenClaw（本地 AI agent）指向同一趨勢：agent 不再只是對話，而是在封閉或開放環境中自主執行。人類的角色從「手動操作」轉為「定義什麼是好的」。

關鍵差異在「能控制什麼」而非「模型多聰明」——本地 agent 能操作滑鼠、鍵盤、硬體；雲端 agent 只能 API call。

Autoresearch 模式特別值得注意：只要產出可量化（binary eval + 3-6 題），就能讓機器跑 50-100 輪你不會手動做的迭代。這個 pattern 遠超 ML——廣告文案、email、技能檔都適用。

## 潛在切入角度
- Threads：用「你還在手動改第 3 版嗎？」開場，帶出 Autoresearch 的 100 輪自動迭代
- Blog：深度比較 Autoresearch vs OpenClaw 的 agent 設計哲學
- 跟 Dex Agent OS 的關聯：自己正在做的技能檔迭代優化就是這個 pattern
