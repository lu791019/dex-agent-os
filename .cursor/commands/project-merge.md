
# Project Merge

## Overview

Structured workflow for merging two or more overlapping software projects into a single unified codebase. The core principle: **explore deeply before deciding, decide before coding, verify after every step**.

## When to Use

- Two projects with overlapping functionality need to become one
- A prototype/POC is being integrated into a production project
- Combining separate frontend and backend repos into a monorepo
- Merging a fork back with the original upstream
- Consolidating microservices that grew apart

## Workflow

```
Phase 1: Explore  →  Phase 2: Compare  →  Phase 3: Decide
    ↓                                          ↓
Phase 6: Verify  ←  Phase 5: Execute  ←  Phase 4: Plan
```


## Phase 1: Parallel Exploration

Explore all source projects simultaneously using subagents. For each project, extract:

| Dimension | What to capture |
|-----------|----------------|
| Structure | Directory tree, module organization |
| Tech stack | Languages, frameworks, versions, dependencies |
| Features | What's implemented vs planned vs empty shells |
| Data models | Entities, relationships, schemas |
| Git state | Branches, commit history, uncommitted changes |
| Tests | Coverage, frameworks, passing/failing |
| Config | Environment vars, Docker, CI/CD |
| Docs | README, planning docs, architecture docs |

**Output**: Side-by-side comparison table highlighting overlaps and differences.

Reference: `references/merge-checklist.md` for the full checklist template.


## Phase 2: Comparison & Key Decisions

Present the comparison to the user and ask **one question at a time** (multiple choice preferred) to resolve each decision axis:

### Decision axes (in order)

1. **Framework choice** — When projects use different frameworks for the same layer (e.g., Next.js vs React+Vite), which to keep?
2. **Architecture pattern** — When code organization differs (e.g., modular vs centralized), which structure for the merged project?
3. **Project location** — Where to put the merged project? Existing repo, new repo, or one of the originals?
4. **Feature scope** — What to bring from each project? Only implemented code, or also planned/empty shells?
5. **Data model reconciliation** — When schemas differ, which fields/relationships are canonical?

Only ask questions relevant to the specific projects. Skip if there's an obvious right answer.


## Phase 3: Strategy Selection

Propose 2-3 merge strategies with clear tradeoffs. Common patterns:

### Strategy A: Skeleton + Transplant (most common)

Use one project's architecture as the skeleton, transplant implemented code from the other.

- **Best for**: Projects with complementary strengths (one has better structure, other has more features)
- **Tradeoff**: Medium effort — code needs import path adaptation

### Strategy B: Clean Restart with Reference

Start fresh, use both projects only as reference material.

- **Best for**: Both projects have significant technical debt
- **Tradeoff**: Most work, but cleanest result

### Strategy C: Git History Merge

Use `git merge --allow-unrelated-histories` to combine repos.

- **Best for**: Projects with similar structure and valuable git history
- **Tradeoff**: Merge conflicts can be painful if structures diverge

Present with a clear recommendation and reasoning. Get user approval before proceeding.


## Phase 4: Design & Implementation Plan

### Design document

Write to `docs/plans/YYYY-MM-DD-project-merge-design.md`:

1. **Source mapping table** — For each module in the target, document where it comes from and what import adaptations are needed
2. **Target structure** — Full directory tree of the merged project
3. **What NOT to bring** — Explicitly list what's excluded and why
4. **Verification criteria** — How to know the merge is successful

### Implementation plan

Write to `docs/plans/YYYY-MM-DD-project-merge-plan.md`:

Group related modules into tasks. Each task should:
- List exact source and target file paths
- Document all import path changes needed
- End with a commit checkpoint
- Include verification step

**Practical grouping**: Combine closely related tasks (e.g., auth + profile + portfolio as one task) to reduce overhead. A merge of two medium projects typically needs 5-8 tasks, not 15+.

Reference: `references/strategy-patterns.md` for import adaptation patterns.


## Phase 5: Execution

Execute tasks sequentially using subagents. Each subagent receives:

1. The specific task description with file paths
2. Source project locations
3. Import path mapping table
4. Instruction to read source files, adapt imports, write to target

### Import Path Adaptation

The #1 source of bugs in project merges. When moving files between directory structures, systematically update:

```
Old: from app.core.database import Base
New: from app.database import Base

Old: from app.services.user_service import user_service
New: from app.auth.service import user_service
```

Provide the complete mapping table to each subagent. Do NOT rely on them to figure out import paths.

### Commit cadence

One commit per task group. Message format:
```
feat: migrate [module names] from [source project]
```


## Phase 6: Verification

After all tasks complete, verify in order:

1. **Backend startup** — Server starts without import errors
2. **Tests pass** — All existing + new tests green
3. **Frontend build** — TypeScript compiles, build succeeds
4. **API docs** — Swagger/OpenAPI docs render correctly
5. **End-to-end** — Core user flow works (register -> login -> use feature)

If any verification fails, fix before proceeding to next check.

### Post-merge cleanup

- Update planning docs to reflect actual merged state
- Note which features came from which source
- Mark old projects for deletion (user confirms manually)


## Principles

- **Explore before deciding** — Never propose a merge strategy without first reading both codebases
- **One question at a time** — Don't overwhelm with decisions; resolve sequentially
- **Import paths are the #1 risk** — Provide explicit mapping tables, don't hope they'll be figured out
- **Verify incrementally** — Each task should leave the project in a runnable state
- **Preserve, don't recreate** — Transplant working code rather than rewriting it
- **Document what's excluded** — Explicitly stating what you don't bring prevents confusion later

## References

- `references/merge-checklist.md` — Project comparison checklist template
- `references/strategy-patterns.md` — Common merge strategies and import adaptation patterns
