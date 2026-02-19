
# SDD→BDD→TDD 三層驗證開發流程

## 核心概念

三層方法論各解決不同問題，缺一不可：

| 層級 | 全稱 | 解決什麼 | 沒有它的風險 |
|------|------|----------|-------------|
| **SDD** | Spec-Driven Development | 程式碼是否符合規格 | 測試通過但行為不符 spec |
| **BDD** | Behavior-Driven Development | 規格是否轉為可驗證場景 | Spec 太抽象，實作偏離 |
| **TDD** | Test-Driven Development | 每行程式碼是否有測試驅動 | 重構後回歸，無紅燈證明 |

## 執行流程

```
Design Doc (Spec, Source of Truth)
    │
    ▼
[SDD] 提取 API Contract：endpoints, request/response, 驗證規則, 錯誤條件
    │
    ▼
[BDD] 導出 Given/When/Then 場景（每個端點至少覆蓋：happy path + 驗證失敗 + 權限拒絕）
    │
    ▼
[TDD] 逐場景執行：
    1. 寫測試 → 跑測試 → 確認 FAIL（紅燈）
    2. 寫最小實作 → 跑測試 → 確認 PASS（綠燈）
    3. 重構（可選）
    │
    ▼
[SDD] Spec Review：比對實作 vs 設計文件
    ├─ 找到偏差 → 補 BDD 場景 → 重回 TDD
    └─ 全部符合 → 完成
```

## 各步驟詳解

### Step 1: SDD — 提取規格

從設計文件中提取結構化的 API Contract：

```markdown
| # | Method | Path | Request | Response | 驗證規則 |
|---|--------|------|---------|----------|----------|
| 1 | POST | /resource | {field1, field2} | ResourceResponse | field1 必填 |
```

同時列出跨端點共通規則（auth、ownership、error codes）。

### Step 2: BDD — 導出行為場景

每個端點至少 3 個場景：
1. **Happy path**：正常使用
2. **Validation failure**：違反驗證規則
3. **Access control**：未認證或無權限

場景格式：
```gherkin
Scenario: [描述]
Given [前置條件]
When  [動作]
Then  [預期結果，含具體 HTTP status code]
```

**常見遺漏檢查**：
- 每個 spec 中列出的端點都有對應場景嗎？
- 每個驗證規則都有對應的失敗場景嗎？
- HTTP status code 語義正確嗎？（400=請求格式錯 / 403=無權限 / 404=不存在）

### Step 3: TDD — 紅綠重構

嚴格執行紅→綠循環：

1. **紅燈**：將 BDD 場景寫成 pytest 測試，跑測試確認 FAIL
2. **綠燈**：寫最小實作讓測試 PASS
3. **重構**：在綠燈狀態下改善程式碼品質

**紅燈的價值**：證明測試真的在測東西。如果新寫的測試直接 PASS，代表測試沒有新增價值。

### Step 4: SDD Spec Review — 最關鍵的一步

在 TDD GREEN 之後，必須比對實作 vs 設計文件：

1. 每個 spec 端點都有實作嗎？（缺失端點）
2. 每個驗證規則都有實作嗎？（遺漏驗證）
3. 有沒有 spec 沒要求但實作了的？（YAGNI 違規）
4. HTTP status code 語義正確嗎？

如果發現偏差：補 BDD 場景（新紅燈）→ 修實作（新綠燈）→ 再驗 spec。

## 與 Subagent-Driven Development 的結合

SDD→BDD→TDD 是「方法論」，subagent-driven-development 是「執行機制」：

```
Orchestrator (我)
    │
    ├─ [SDD] 提取 spec → 自己做
    ├─ [BDD] 寫場景 + 測試 → 自己做
    ├─ [TDD RED] 確認測試 FAIL → 自己做
    ├─ [TDD GREEN] dispatch implementer subagent → 寫實作
    ├─ [SDD Review] dispatch spec reviewer subagent → 驗 spec 合規
    └─ [Quality] dispatch code reviewer subagent → 驗程式碼品質
```

## 實證教訓

來自 job-hunter-v2 Phase 5 驗證：

1. **BDD 場景一定會遺漏**：人工從 spec 導場景容易忽略「不起眼」的端點。Spec review 是安全網。
2. **Implementer 只滿足測試**：TDD GREEN 天生只做到測試要求的程度。沒有 spec review，測試漏掉的行為就不會被實作。
3. **HTTP 語義要寫進 BDD**：BDD 場景必須明確寫出預期的 HTTP status code（如 403 not 400），否則實作者會用語義不正確的 exception。
4. **Spec review 順序**：先 spec compliance → 再 code quality。如果 spec 不合規，程式碼品質再好也沒意義。

## 何時更新這份 Skill

| 情境 | 更新什麼 |
|------|----------|
| 發現新的 BDD 場景遺漏模式 | 常見遺漏檢查清單 |
| Spec review 抓到新類型的偏差 | 實證教訓 |
| 與其他 skill 整合方式改變 | 與 Subagent 結合章節 |
