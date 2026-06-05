# Task Plan: AI 小说转剧本工具 (Novel-to-Script)

## Goal
构建一个 AI 辅助剧本创作工具，用户上传 3 章以上小说文本（txt/epub/粘贴），自动转换为结构化剧本（YAML 格式），并提供原文 vs 剧本并排对照视图，3 天内完成并部署上线。

## Current Phase
Phase 1

## PR 策略

每 PR 只做一件事，小粒度持续提交，main 分支始终保持可运行。

| PR# | 功能 | 预估提交量 | 所属阶段 |
|-----|------|-----------|---------|
| PR1 | 项目脚手架：Vue 3 + Vite 前端 + Django 后端 + 目录结构 | 1 commit | Phase 2 |
| PR2 | YAML Schema 定义 + zod/js-yaml 校验模块 | 1 commit | Phase 2 |
| PR3 | Claude API 单章转换 pipeline（后端核心） | 2-3 commits | Phase 3 |
| PR4 | Django API 端点：convert / status / result | 1 commit | Phase 3 |
| PR5 | 分块策略：章节拆分 + EPUB 解析 | 2 commits | Phase 4 |
| PR6 | 角色提取：全文角色表 + prompt 约束 | 2 commits | Phase 4 |
| PR7 | 多章拼装 + Act 划分合并 | 2 commits | Phase 4 |
| PR8 | 错误兜底：解析 → 重试 → 标记人工处理 | 2 commits | Phase 4 |
| PR9 | 前端上传页（三种输入方式） | 2 commits | Phase 5 |
| PR10 | 前端进度页（轮询 + 逐章预览） | 2 commits | Phase 5 |
| PR11 | 前端对照视图（按场对齐 + 内联编辑） | 2-3 commits | Phase 5 |
| PR12 | 深浅护眼模式 + 阅读体验打磨 | 1-2 commits | Phase 6 |
| PR13 | 剧本 YAML Schema 文档 | 1 commit | Phase 6 |
| PR14 | 部署配置 + README | 1 commit | Phase 6 |

## Phases

### Phase 1: 需求确认
- [x] 技术选型（Vue 3 + Django + Claude API）
- [x] 输入方式确认（粘贴/txt/epub）
- [x] Schema 颗粒度确认（Act → Scene → Beat）
- [x] 对照视图交互确认（按场对齐）
- [x] 分块 + 角色提取策略确认
- [x] 部署方案确认（Vercel + Render）
- **Status:** complete

### Phase 2: 项目初始化 + 核心定义
- [ ] PR1: 项目脚手架搭建
- [ ] PR2: YAML Schema 定义 + 校验模块
- [ ] Django models 定义
- [ ] Vue Router 页面骨架
- **Status:** pending

### Phase 3: 后端核心管道
- [ ] PR3: Claude API 单章转换 pipeline
- [ ] PR4: Django API 端点（convert / status / result）
- [ ] 单章 → 合规 YAML 端到端跑通
- **Status:** pending

### Phase 4: 后端完整功能
- [ ] PR5: 章节拆分 + EPUB 解析
- [ ] PR6: 角色提取 + prompt grounding
- [ ] PR7: 多章拼装 + Act 合并
- [ ] PR8: 错误兜底（retry + 人工标记）
- **Status:** pending

### Phase 5: 前端全部页面
- [ ] PR9: 上传页
- [ ] PR10: 进度页
- [ ] PR11: 对照视图
- **Status:** pending

### Phase 6: 打磨 + 部署 + 文档
- [ ] PR12: 深浅模式 + 阅读体验
- [ ] PR13: Schema 文档
- [ ] PR14: 部署 + README
- **Status:** pending

## Key Questions
1. Claude API 单次输出完整 Scene YAML 的稳定性能否保证？→ 通过分块 + 重试兜底
2. EPUB 格式兼容性边界在哪？→ 只支持标准 EPUB2/3，不做复杂容错
3. Render 免费层冷启动 30s 对用户体验影响？→ toast 提示 + 进度页等待
4. 长文本 chunk 之间角色一致性？→ 角色表先行提取策略

## Decisions Made
| Decision | Rationale |
|----------|-----------|
| Vue 3 + Vite + TS 前端 | 用户熟悉，学习成本最低 |
| Django 后端 | 用户熟悉，ORM/admin 省时间 |
| Claude API (anthropic SDK) | 长上下文 + 结构化输出稳定性 |
| js-yaml + zod 校验 | YAML 解析 + schema 兜底修复 |
| Vercel + Render 免费部署 | 零成本，demo 项目足够 |
| Act → Scene → Beat 三层 Schema | 深于竞品，能表达戏剧节奏 |
| 逐章处理 + 拼装 | 稳定性优于一次性全量输出 |
| 角色表先行提取 | 解决跨章角色命名一致性 |
| 按场(Scene)对齐对照 | 小说→剧本非 1:1 映射，逐句对齐不可行 |
| 异步 + 轮询 | Render 不支持 SSE 长连接，轮询稳妥 |

## Errors Encountered
| Error | Attempt | Resolution |
|-------|---------|------------|
|       |         |            |

## Notes
- 每天结束时 main 分支必须可运行
- 每个 PR 合并后验证 `python manage.py runserver` 不报错
- README 需列明所有第三方依赖及原创功能说明
