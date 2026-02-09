# Reflections Archive

## 2026-02-05
- 尚未做競品分析，不確定市場上已有方案的深度，可能導致定位不夠差異化
- 缺少真實使用者回饋來驗證功能優先順序，目前的模組排序是基於直覺
- LLM 產生 Airflow DAG 的品質尚未驗證，這是 Phase 2 的技術風險

## 2026-02-07
- Rate limit 反覆觸發：大量對話 + 多 session 導致頻繁撞限，購買 Extra usage 暫時緩解
- bin/sync 的 awk 處理 YAML frontmatter 偏脆弱：markdown 內含 `---` 分隔線會誤判

## 2026-02-08
- Rate limit 三連斷：上午、下午、晚間各觸發一次，三項工作全部中斷
- 多專案並行的代價：同時推進三個專案，資源分散導致沒有一項能完整收尾
- 技術債累積：bin/sync awk 脆弱、LLM 回應清理 heuristic、feature branch 未合併
