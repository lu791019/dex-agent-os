
# SDD→BDD→TDD 三層驗證開發流程

## 核心原則

**Spec 是唯一真相來源**。程式碼、測試、行為場景，全部從 spec 導出，最終也回到 spec 驗證。

三層各守一道關：

- **SDD**：程式碼是否忠於規格（防止「測試通過但行為不符」）
- **BDD**：規格是否被完整轉譯為可驗證場景（防止「理解 spec 但忘記測」）
- **TDD**：每行實作是否有測試驅動（防止「寫了就忘測」）

**少了任何一層都有盲區**。TDD 只保證「測試要求的都做了」，但不保證「spec 要求的都被測了」——這是 SDD review 的工作。

## 流程（精簡版）

```
Spec → [SDD提取] → API Contract
                        ↓
               [BDD導出] → Given/When/Then 場景
                                    ↓
                           [TDD] → RED → GREEN → Refactor
                                    ↓
                           [SDD Review] → 比對 spec
                              ├─ 偏差 → 補場景 → 回 TDD
                              └─ 通過 → 完成
```

詳細步驟見 `references/process.md`。

## 三個關鍵判斷原則

### 1. BDD 場景一定會遺漏，Spec Review 是安全網

人工從 spec 導出場景時，「不起眼的端點」和「隱含的驗證規則」最容易被忽略。不要信任 BDD 的完整性——SDD review 才是最後防線。

### 2. Implementer 只做到測試要求的程度

TDD GREEN 天生是「測試驅動」而非「spec 驅動」。如果 BDD 漏了一個場景，implementer 就不會實作那個行為。這不是 implementer 的錯，是流程設計使然。

### 3. BDD 場景必須包含具體的 HTTP 語義

`Then 400` 和 `Then 403` 不是同一件事。BDD 場景裡的預期結果必須精確到 HTTP status code，否則實作者會用語義不正確的 exception（例如把「過期」當成「請求格式錯誤」而非「禁止存取」）。

## 與相關 Skill 的關係

| Skill | 角色 | 本 Skill 的定位 |
|-------|------|----------------|
| `superpowers:test-driven-development` | TDD 單層執行 | 本 skill 的 TDD 步驟可引用它 |
| `superpowers:subagent-driven-development` | 執行機制（誰來做） | 本 skill 是方法論（怎麼做） |
| `superpowers:writing-plans` | 產出 implementation plan | 本 skill 在 plan 執行階段介入 |

## 何時更新這份 Skill

| 情境 | 更新什麼 |
|------|----------|
| 發現新的 BDD 場景遺漏模式 | `references/process.md` 常見遺漏檢查 |
| Spec review 抓到新類型的偏差 | 關鍵判斷原則 |
| 與其他 skill 整合方式改變 | 關係表 |
