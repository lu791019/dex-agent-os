---

```
---
title: Our Learnings From Adopting GraphQL
source: Netflix Technology Blog (https://netflixtechblog.com/our-learnings-from-adopting-graphql-f099de39ae5f)
type: articles
date: 2026-02-18
tags: [GraphQL, Netflix, API-design, backend-architecture, federation]
---
# Our Learnings From Adopting GraphQL

## 一句話摘要
Netflix 從 REST 遷移到 GraphQL 的實戰經驗：解決多資料源聚合、重複請求與規模化挑戰。

## 核心觀點
1. **問題起源**：頁面需要從多個後端服務取資料，原本用 denormalized endpoints 管理困難且浪費頻寬——不是每個頁面都需要所有欄位
2. **GraphQL 作為中間層**：不再為每個頁面建 custom endpoint，改用 GraphQL 當 API 聚合層，前端按需查詢
3. **遷移成本低於預期**：原有 React → NodeJS 的網路請求與資料轉換邏輯可直接搬移，最終刪掉的程式碼比新增的多
4. **Resolver 重複請求是核心挑戰**：多個 resolver 同時請求相同資料，解法是加 caching layer（in-memory）+ 批次聚合（batching），即 DataLoader 模式
5. **未來方向：Schema Stitching → Federation**：透過 schema 組合讓跨服務整合更簡單，後續演進為 DGS Framework 與 federated GraphQL 架構

## 關鍵引述
> reusable abstractions

> "We ended up deleting more code than we added."（遷移後刪掉的程式碼比新增的多）

## 實作筆記
- **DataLoader 模式**：解決 N+1 問題的標準做法——將 resolver 層的重複請求包裝在 caching layer 中，存在 memory 直到所有 resolver 完成，同時聚合多次請求為批次請求
- **GraphQL 中間層架構**：Client → GraphQL Server (Node.js) → 多個 Backend Services，GraphQL 負責聚合與裁剪
- **Netflix DGS Framework**：後續開源的 Spring Boot GraphQL 框架，用 `@DgsData` 注解定義 data fetcher，自動處理 Java 物件映射
- **Federation 規模化策略**：拆解 gateway monolith，讓各 domain team 維護自己的 subgraph，對 client 暴露統一 API
- **效能優化重點**：selective eviction caching（尖峰時段降低 50% 後端負載）、平行執行 query plan、批次合併請求

## 我的想法
<!-- 手動補充 -->

## 可轉化為內容
- **Threads**：「Netflix 遷移 GraphQL 的反直覺發現：刪掉的程式碼比新增的多」— 拆解為什麼減法 > 加法
- **Threads**：「你的 API 也有 N+1 問題嗎？Netflix 用 DataLoader 模式的實戰解法」
- **Blog**：「從 Netflix 的 GraphQL 之路看 API 架構演進：REST → GraphQL → Federation」— 適合寫成技術演進觀點文
- **Newsletter**：大型組織 API 治理策略——從 Netflix DGS 看 GraphQL Federation 如何讓 domain team 各自負責又統一對外
```
