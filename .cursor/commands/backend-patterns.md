
# Backend Development Patterns

Backend architecture patterns for scalable Node.js/Express/Next.js applications.

## Core Principles

1. **Separate concerns**: Data access (Repository) → Business logic (Service) → HTTP handling (Controller)
2. **Fail explicitly**: Use typed errors (`ApiError`), centralized error handlers, Zod validation
3. **Cache at the right layer**: Cache-aside pattern with TTL, invalidate on writes
4. **Prevent N+1**: Batch fetch related data, use `Map` for lookups
5. **Select only what you need**: Never `SELECT *` in production queries

## Quick Patterns

### API Route Structure
```typescript
export async function GET(request: Request) {
  try {
    const user = await requireAuth(request)
    const data = await service.getData(user.id)
    return NextResponse.json({ success: true, data })
  } catch (error) {
    return errorHandler(error, request)
  }
}
```

### Repository → Service → Handler
```
Repository (data access) → Service (business logic) → Handler (HTTP)
```

## Reference Files

Load these based on what you're working on:

- **`references/api-design.md`** — RESTful structure, Repository/Service/Middleware patterns, JWT auth, RBAC, rate limiting. Load when designing API endpoints or implementing auth.
- **`references/database.md`** — Query optimization, N+1 prevention, transaction patterns. Load when writing database queries or optimizing performance.
- **`references/architecture.md`** — Caching (Redis), error handling, retry backoff, job queues, structured logging. Load when implementing infrastructure patterns.

## 何時更新這份 Skill

| 情境 | 更新什麼 |
|------|----------|
| 發現新的 API 設計模式或反模式 | 對應的 reference 檔案 |
| 切換框架或 ORM（如 Drizzle → Prisma） | Core Principles + references |
| 效能瓶頸定位到架構層 | `references/architecture.md` |
| 新增微服務或 API gateway 模式 | `references/api-design.md` |
