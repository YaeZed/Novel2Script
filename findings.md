# Findings & Decisions

## Requirements
- 上传小说文本（3 章以上），自动转换为结构化剧本（YAML 格式）
- 支持三种输入方式：直接粘贴 / .txt 上传 / .epub 上传
- Schema: Act(幕) → Scene(场) → Beat(节拍) 三层结构
- Beat 包含：type(dialogue/action/direction) / character / content / parenthetical
- 原文 vs 剧本并排对照视图，按场(Scene)对齐
- 右侧剧本支持内联编辑
- 深浅护眼模式切换
- 3 天开发周期，持续 PR 提交
- 免费部署（Vercel + Render）
- main 分支始终保持可运行状态

## Research Findings
- `ebooklib` Python 库可解析标准 EPUB2/3 文件，按章节提取纯文本
- `js-yaml` Node.js 端 YAML 解析，`zod` schema 校验可检测缺失字段
- `anthropic` Python SDK 支持结构化输出（tool use / JSON mode），可用于约束 YAML 格式
- Render 免费层 Web Service 15 分钟无请求自动休眠，首次唤醒需 ~30s
- Vercel 免费层 100GB 带宽/月，函数执行超时 10s（前端静态资源不影响）
- 三章小说约 2-5 万中文字符 → Claude 3.5 Sonnet 128K 上下文可一次容纳，但分块输出更稳定
- EPUB 内部是 XHTML/HTML 文件集合 + container.xml 导航 + toc.ncx 目录，`ebooklib` 可直接按 spine 顺序读取

## Technical Decisions
| Decision | Rationale |
|----------|-----------|
| Vue 3 + Vite + TS 前端 | 用户最熟悉的技术栈 |
| Django (DRF) 后端 | 用户熟悉，ORM/admin 减省代码量 |
| anthropic Python SDK (Claude API) | 长上下文 + 结构化输出稳定，单次可处理整章 |
| js-yaml + zod | YAML 解析 + schema 校验，错误自动检测 |
| 逐章处理 + 拼装 | 避免长文本导致 LLM 输出丢字段漏章节 |
| 角色表先行提取 | 跨章角色命名一致性，角色表也是产品价值 |
| 异步轮询方案 | Render 不支持长连接 SSE risk，轮询稳妥 |
| 按场对齐对照视图 | 小说→剧本非 1:1，逐句对齐勉强且费工 |
| Vercel + Render 免费部署 | 零成本，demo 足够 |
| 14 个独立 PR | 满足持续交付要求，每 PR 单一功能 |

## Issues Encountered
| Issue | Resolution |
|-------|------------|
|       |            |

## Resources
- ebooklib docs: https://pypi.org/project/ebooklib/
- anthropic Python SDK: https://github.com/anthropics/anthropic-sdk-python
- js-yaml: https://github.com/nodeca/js-yaml
- zod: https://github.com/colinhacks/zod
- Vercel free tier: https://vercel.com/docs/limits
- Render free tier: https://render.com/docs/free
- django-cors-headers: https://github.com/adamchainz/django-cors-headers

## Visual/Browser Findings
-

---
*Update this file after every 2 view/browser/search operations*
*This prevents visual information from being lost*
