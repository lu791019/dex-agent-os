# Phase 6 P1 Walkthrough — 會議 / 諮詢 / 專案狀態 / Classroom / Fireflies

> 完成日期：2026-02-20
> Branch：`feature/phase6-p1`
> Commits：8 個（e51cd94 → e64c836），已 merge to master

---

## 一、本次新增功能總覽

| 功能 | CLI 指令 | IDE Skill | 輸出位置 |
|------|---------|-----------|----------|
| 會議筆記（4 種輸入來源） | `meeting-notes` | `/meeting-notes` | `200_Work/meetings/` |
| 諮詢紀錄（giving/receiving） | `consultation-notes` | `/consultation-notes` | `200_Work/consultations/` |
| 專案狀態追蹤 | `project-status` | `/project-status` | `400_Projects/*/STATUS.md` |
| Google Classroom 同步 | `classroom-sync` | `/classroom-sync` | `200_Work/meetings/` + `consultations/` |
| Fireflies.ai 同步 | `fireflies-sync` | `/fireflies-sync` | `200_Work/meetings/` |

---

## 二、新增 / 修改檔案清單

### 新增（23 個）

| 類別 | 檔案 |
|------|------|
| 模板 | `800_System/templates/meeting-notes-template.md` |
| | `800_System/templates/project-status-template.md` |
| 測試 | `400_Projects/software/dex-agent-os/STATUS.md` |
| | `tests/fixtures/sample-transcript.txt` |
| | `tests/fixtures/sample-consultation-notes.txt` |
| 共用模組 | `scripts/lib/input_loader.py` |
| | `scripts/lib/fireflies_api.py` |
| Collector | `scripts/collectors/classroom_sync.py` |
| | `scripts/collectors/fireflies_sync.py` |
| Generator | `scripts/generators/meeting_notes.py` |
| | `scripts/generators/consultation_notes.py` |
| | `scripts/generators/project_status.py` |
| Workflow | `canonical/workflows/meeting-notes.md` |
| | `canonical/workflows/consultation-notes.md` |
| | `canonical/workflows/project-status.md` |
| | `canonical/workflows/classroom-sync.md` |
| | `canonical/workflows/fireflies-sync.md` |
| IDE Skill | `.claude/commands/meeting-notes.md` |
| | `.claude/commands/consultation-notes.md` |
| | `.claude/commands/project-status.md` |
| | `.claude/commands/classroom-sync.md` |
| | `.claude/commands/fireflies-sync.md` |
| 文件 | `implementation_plan_phase6.md`、`task_phase6.md` |

### 修改（6 個）

| 檔案 | 變更 |
|------|------|
| `scripts/lib/config.py` | +MEETINGS_DIR / CONSULTATIONS_DIR / PROJECTS_SOFTWARE_DIR / PROJECTS_PRODUCTS_DIR / FIREFLIES_API_KEY |
| `scripts/lib/google_api.py` | +4 Classroom scopes（老師角色）+ `get_classroom_service()` + `read_google_doc(url)` |
| `bin/agent` | +5 子命令 + help text |
| `config/.env.example` | +FIREFLIES_API_KEY |
| `CLAUDE.md` | CLI 速查表加工作類指令 |
| `GUIDE.md` | +6.8 工作管理系統 + 功能狀態更新 |
| `PLAN.md` | Phase 6 P1 完成 + P2 分離 |

---

## 三、架構設計重點

### 共用輸入載入器（input_loader.py）

```
meeting_notes.py ──┐
                   ├── input_loader.load_input(args)
consultation_notes.py ──┘
                          │
            ┌─────────────┼─────────────┐─────────────┐
            ▼             ▼             ▼             ▼
      --transcript   --notes    --google-doc   --fireflies
      (檔案)        (文字)      (Google API)   (Fireflies API)
```

消除 ~60% 重複碼。其他 generator 未來需要多來源輸入時，直接用 `add_input_args()` + `load_input()`。

### Fireflies Graceful Fallback

```python
# 沒有 API key → 印 setup 引導，不 crash
if not FIREFLIES_API_KEY:
    print("[fireflies] 請設定 FIREFLIES_API_KEY...")
    return False
```

### Google Classroom 老師角色

Scopes 用 `.students` 版本（非 `.me`），可存取所有學生的作業和提交：
- `classroom.coursework.students.readonly`
- `classroom.student-submissions.students.readonly`

支援篩選：`--active-only`（活躍課程）、`--student-name NAME`（按學生名搜尋）。

---

## 四、Git 提交記錄

```
e64c836 feat: integrate work outputs (meetings/consultations/projects) into work-log L1
fa430cf docs: add Phase 6 P1 workflows, skills, and update all documentation
be2f7e7 feat: add project status generator (reads STATUS.md + git log → LLM update)
b97897b feat: add input_loader + meeting notes / consultation notes generators
be5d648 feat: add Fireflies.ai collector with graceful fallback (no subscription)
76f3c18 feat: add Google Classroom collector + Google Docs reader (teacher scopes)
e51cd94 feat: add Phase 6 infrastructure — config paths, templates, test fixtures
```

---

## 五、使用注意事項

1. **首次使用 Classroom**：需刪除 `config/google-token.json` 重新授權（加了新 scope）
2. **Fireflies 需訂閱**：目前無訂閱，`--list` 會顯示設定引導。未來訂閱後直接設 `FIREFLIES_API_KEY` 即可
3. **會議轉錄推薦**：Tactiq（免費 10 會/月）或 Scribbl（免費 15 會/月）→ 自動存 Google Docs → 用 `--google-doc URL`
4. **bin/sync 已執行**：workflows 和 skills 已同步到 .agent/ + .cursor/
5. **work-log 整合**：`/work-log` 產出 L1 時會自動掃描當日的會議筆記、諮詢紀錄、專案狀態，加入參考清單

---

## 六、下一步

- **Phase 6 P2**：產品管理 + 訂閱管理（未排期）
- **Phase 7**：職涯 + launchd 排程自動化
