
# Python Development Patterns

Idiomatic Python patterns and best practices for robust, efficient, and maintainable applications.

## Core Principles

1. **Readability counts**: Code should be obvious — clear names, simple structure, no cleverness
2. **Explicit over implicit**: No magic; be clear about what code does and why
3. **EAFP**: Easier to Ask Forgiveness than Permission — prefer `try/except` over condition checks
4. **Use the right tool**: Comprehensions for simple transforms, generators for large data, dataclasses for data containers
5. **Type everything**: Annotate function signatures; use `Protocol` for duck typing

## Quick Pattern

```python
@dataclass
class User:
    id: str
    name: str
    email: str
    is_active: bool = True

def get_active_users(users: list[User]) -> list[User]:
    return [u for u in users if u.is_active]
```

## Reference Files

Load these based on what you're working on:

- **`references/idioms.md`** — Core principles, comprehensions, generators, dataclasses, decorators, anti-patterns, quick reference table. Load when writing general Python code.
- **`references/type-hints-errors.md`** — Type annotations (basic/modern/Protocol), error handling (specific exceptions, chaining, custom hierarchy), context managers. Load when adding types or designing error handling.
- **`references/concurrency-performance.md`** — Threading, multiprocessing, async/await, `__slots__`, memory optimization. Load when writing concurrent or performance-sensitive code.
- **`references/project-tooling.md`** — Project layout, import conventions, `__init__.py` exports, pyproject.toml config, black/ruff/mypy/pytest commands. Load when setting up or configuring a Python project.

## 何時更新這份 Skill

| 情境 | 更新什麼 |
|------|----------|
| Python 版本升級帶來新語法（如 match/case） | `references/idioms.md` |
| 新增或替換 tooling（如 ruff 取代 pylint） | `references/project-tooling.md` |
| 發現新的 async 模式或效能技巧 | `references/concurrency-performance.md` |
| 專案採用新型別系統特性（如 TypedDict） | `references/type-hints-errors.md` |
