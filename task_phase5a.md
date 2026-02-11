# Phase 5a — Task Checklist

## Section A：基礎設施
- [x] A1. 建立目錄結構 `300_Learning/{podcasts/{episodes,weekly,transcripts},youtube}` + `500_Content/presentations`
- [x] A2. 新增模板：podcast-episode / youtube-note / podcast-digest / podcast-pptx
- [x] A3. 更新 `config.py` 新增路徑常數
- [x] A4. 更新 `.gitignore` 加入 `transcripts/`
- [x] A5. 設定 MCP servers 在 `.mcp.json`

## Section B：YouTube 線
- [x] B1. 寫 `scripts/collectors/youtube_transcript.py`
- [x] B2. 更新 `bin/agent` 新增 `youtube-add` 子命令
- [x] B3. 測試 `./bin/agent youtube-add "URL"` ✅ 端到端通過
- [x] B4. 寫 `.claude/commands/youtube-add.md` skill

## Section C：Podcast 線
- [x] C1. 寫 `scripts/collectors/podcast_transcript.py` 骨架 + LLM 結構化
- [x] C2. 實作模式 P4：手動文字稿
- [x] C3. 實作模式 P3：Apple Podcast TTML 快取
- [x] C4. 更新 `bin/agent` 新增 `podcast-add` 子命令
- [x] C5. 測試 `./bin/agent podcast-add --transcript test.txt --title "Test"` ✅ 端到端通過
- [x] C6. 測試 `./bin/agent podcast-add --apple` ✅ 目錄不存在時正確提示

## Section D：週度消化報告
- [x] D1. 寫 `scripts/generators/podcast_digest.py`
- [x] D2. 更新 `bin/agent` 新增 `podcast-digest` 子命令
- [x] D3. 測試 `./bin/agent podcast-digest` ✅ 端到端通過

## Section E：簡報產出
- [x] E1. 在 `podcast_digest.py` 加入 `--pptx` 功能
- [x] E2. 測試 `./bin/agent podcast-digest --pptx` ✅ 端到端通過

## Section F：Skill + 整合收尾
- [x] F1. 寫 `canonical/workflows/podcast-weekly.md`
- [x] F2. 寫 `.claude/commands/podcast-weekly.md`
- [x] F3. 寫 `.claude/commands/podcast-add.md`
- [x] F4. 跑 `bin/sync` ✅ 3 個新 skill 已同步
- [x] F5. 更新 GUIDE.md + PLAN.md
- [ ] F6. 全流程測試 + commit
