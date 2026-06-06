# Task Plan: AI 小说转剧本工具 (Novel-to-Script)

## Goal
构建一个 AI 辅助剧本创作工具，用户上传 3 章以上小说文本（txt/epub/粘贴），自动转换为结构化剧本（YAML 格式），并提供原文 vs 剧本并排对照视图，3 天内完成并部署上线。

## Current Phase
Phase 4

## PR 策略

每 PR 只做一件事，小粒度持续提交，`master` 分支始终保持可运行。

| PR# | 功能 | 预估提交量 | 所属阶段 |
|-----|------|-----------|---------|
| PR1 | 项目脚手架：Vue 3 + Vite 前端 + Django 后端 + 目录结构 | 1 commit | Phase 2 |
| PR2 | YAML Schema 定义 + zod/js-yaml 校验模块 | 1 commit | Phase 2 |
| PR3 | 多厂商 LLM 单章转换 pipeline（后端核心） | 2-3 commits | Phase 3 |
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
- [x] 技术选型（Vue 3 + Django + 多厂商 LLM provider）
- [x] 输入方式确认（粘贴/txt/epub）
- [x] Schema 颗粒度确认（Act → Scene → Beat）
- [x] 对照视图交互确认（按场对齐）
- [x] 分块 + 角色提取策略确认
- [x] 部署方案确认（Vercel + Render）
- **Status:** complete

### Phase 2: 项目初始化 + 核心定义
- [x] PR1/P2 合并提交：项目脚手架 + YAML Schema 基线 + 占位转换主链路
- [x] Django models 定义
- [x] Vue Router 页面骨架
- [x] 浏览器手动验收通过
- **Status:** complete

### Phase 3: 后端核心管道
- [x] PR3: 多厂商 LLM 单章转换 pipeline
- [x] PR4: Django API 端点（convert / status / result）已在 Phase 2 骨架中提供占位版
- [x] 单章 → 合规 YAML 端到端跑通
- **Status:** complete

### Phase 4: 后端完整功能
- [x] PR5: 章节拆分 + EPUB 解析
- [x] PR6: 角色提取 + prompt grounding
- [x] PR7: 多章拼装 + Act 合并
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
1. 多厂商 LLM 单次输出完整 Scene YAML 的稳定性能否保证？→ 通过 provider 抽象 + 分块 + 重试兜底
2. EPUB 格式兼容性边界在哪？→ 只支持标准 EPUB2/3，不做复杂容错
3. Render 免费层冷启动 30s 对用户体验影响？→ toast 提示 + 进度页等待
4. 长文本 chunk 之间角色一致性？→ 角色表先行提取策略

## Decisions Made
| Decision | Rationale |
|----------|-----------|
| Vue 3 + Vite + TS 前端 | 用户熟悉，学习成本最低 |
| Django 后端 | 用户熟悉，ORM/admin 省时间 |
| 多厂商 LLM provider | Anthropic/OpenAI/千问可按 key 和部署环境切换，降低单一厂商风险 |
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
| PR5 English heading test only returned 1 chapter | `python manage.py test` after first splitter patch | Replaced newline-consuming `\s*` heading regex whitespace with line-local whitespace so title matches cannot cross line boundaries |

## Notes

## 2026-06-06 PR7 Execution Plan

- Problem: PR5/PR6 now produce reliable chapter inputs and source-grounded per-chapter scenes, but the final YAML still puts every scene under a single `Act 1`.
- User impact: long inputs need a browsable dramatic structure. Authors should see opening / development / resolution sections instead of one flat list.
- Scope:
  - Normalize generated scenes so scene numbers are continuous across the full script.
  - Group scenes into Acts from chapter order using a deterministic backend assembly layer.
  - Keep scene `source_chapter` intact so compare-page source lookup remains stable.
  - Document the Act grouping rule in schema docs.
  - Keep retry and manual-review fallback for PR8.
- First-principles framing:
  - The problem is not "make the model understand the whole book" yet; it is "turn already converted chapters into an editable script structure."
  - The direct path is deterministic assembly after per-chapter conversion, because it is testable and does not add another external model dependency.
  - From zero, the pipeline boundary would be `chapters -> scenes -> acts -> script YAML`; PR7 implements the missing `scenes -> acts` step.
- Validation target:
  - Backend unit tests for multi-act grouping, continuous scene numbering, and pipeline persistence.
  - `python -m compileall backend`, `python manage.py check`, `python manage.py test`, and frontend build.

## 2026-06-06 PR7 Completion

- Delivered:
  - Added deterministic script assembly after per-chapter Scene conversion.
  - Scene `number` is now normalized to full-script sequence order.
  - `source_chapter` remains unchanged for compare-page original text lookup.
  - Scripts with fewer than 3 scenes stay in `第一幕：全篇`; scripts with 3+ scenes split into `第一幕：开端` / `第二幕：展开` / `第三幕：收束`.
  - Updated schema docs, README, and PR7 project rules.
- Validation:
  - `python -m compileall backend`: passed.
  - `python manage.py check`: passed.
  - `python manage.py test`: passed, 27 tests.
  - `npm.cmd run build`: passed.
  - `git diff --check`: passed; only CRLF normalization warnings.

## 2026-06-05 PR6 Execution Plan

- Problem: PR5 made chapter and EPUB input cleaner, but the role context is still weak because the pipeline only recognizes simple `Name: dialogue` lines.
- User impact: better character extraction should reduce invented names, make dialogue beats easier to edit, and give authors a clearer first draft without asking them to manually prepare a cast list.
- Scope:
  - Create a local, evidence-aware character extractor from full source text.
  - Use dialogue labels, quoted dialogue attribution, and narration action hints while filtering obvious metadata labels.
  - Feed the extracted character table into scene prompts with stricter grounding rules.
  - Keep Act grouping, retry, and manual-review fallback for PR7/PR8.
- Validation target:
  - Backend unit tests for extraction, prompt grounding, and pipeline persistence.
  - `python -m compileall backend`, `python manage.py check`, `python manage.py test`, and frontend build.

## 2026-06-05 PR5 Execution Plan

- 范围：增强后端章节拆分和 EPUB 解析，让粘贴文本、TXT、EPUB 都能得到稳定的章节列表，再交给现有逐章转换 pipeline。
- 不做：全文角色提取、角色名统一、多章 Act 划分、retry/人工处理标记，这些仍分别属于 PR6-PR8。
- 第一性原理：
  - 要解决的问题：用户给的是“长篇小说材料”，系统需要先理解章节边界；没有可靠章节，进度页、失败定位、后续角色表都会失真。
  - 最直接路径：把输入清洗、章节标题识别、章节兜底分块、EPUB spine 文本抽取做成后端纯函数，并用测试覆盖边界。
  - 从零设计：会先产出 `Chapter` 结构（title/content/order/source），pipeline 只消费结构化章节，不关心输入来自粘贴、TXT 还是 EPUB。
- 用户影响：上传后进度能按真实章节推进；章节标题保留下来；没有明显章节标题的长文本也不会整本塞给模型导致失败。

## 2026-06-05 PR5 Completion

- Delivered:
  - 更宽的章节标题识别：中文章节、序章/楔子/番外、英文 `Chapter N`、数字标题。
  - 无标题长文本/超长章节按段落自动分块，避免整本一次性进入 LLM。
  - EPUB 按 spine 阅读顺序抽取正文，跳过短目录/封面/版权页。
  - 多文档 EPUB 没有明确章名时自动生成可拆分章节标题。
  - EPUB `<title>` 用作章节名，不重复混进正文。
- Validation:
  - `python -m compileall backend`: passed.
  - `python manage.py check`: passed.
  - `python manage.py test`: passed, 16 tests.
  - `npm run build`: passed.

## 2026-06-05 Phase 2 Merge Summary

- Phase 2 is complete and merged to GitHub `master` through PR #1.
- Merged branch: `codex/phase-2-scaffold`.
- Merge commit on remote master: `14ca2bf`.
- Feature commit: `8407950 Build phase 2 project scaffold`.
- Delivered:
  - `CODEX.md` project rules
  - Django/DRF backend scaffold, model, migration, API routes
  - Vue/Vite frontend scaffold with upload, progress, compare pages
  - Python JSON Schema, YAML dump, frontend zod schema
  - Placeholder conversion path for local end-to-end testing
- Verification:
  - `python manage.py test`
  - `python manage.py check`
  - `npm run build`
  - Browser manual test of sample conversion and compare page YAML validation
- Next step:
  - Sync local `master` with `origin/master`.
  - Create a new Phase 3 branch from latest `master`.
  - Implement multi-provider LLM single-chapter conversion as its own PR.

## 2026-06-05 P2 Acceptance

- User tested Phase 2 and reported no issues.
- One UX fix was made during testing: the YAML validation toolbar icon now uses a check icon instead of a save icon.
- Phase 2 commit after amend: `8407950 Build phase 2 project scaffold`.
- Phase 2 PR was merged on GitHub.
- 每天结束时 `master` 分支必须可运行
- 每个 PR 合并后验证 `python manage.py runserver` 不报错
- README 需列明所有第三方依赖及原创功能说明

## 2026-06-05 P3 Execution Plan

- 范围：只实现多厂商 LLM 单章转换为 Scene JSON，再组装进既有 Act → Scene → Beat YAML Schema。
- 不做：全文角色提取、多章拼装策略、retry/人工标记，这些保留给 Phase 4，避免 PR3 扩散。
- 用户影响：配置 Anthropic/OpenAI/千问任一 key 时得到真实剧本草稿；没有 key 时继续走占位转换，保证演示和前端验收不断。
- 技术路径：新增 provider-agnostic scene converter 抽象，pipeline 根据 `LLM_PROVIDER` 和 API key 选择 Anthropic、OpenAI、千问或 placeholder；LLM 输出必须经 JSON 解析、字段归一化、最终 schema 校验。

## 2026-06-05 P3 Completion

- Delivered:
  - 多厂商 provider 配置：`auto` / `anthropic` / `openai` / `qwen` / `placeholder`
  - Anthropic adapter + OpenAI-compatible adapter（OpenAI 和千问共用）
  - LLM Scene JSON 解析、字段归一化、Beat type 校验、Schema 兜底
  - 无 key 时 placeholder fallback，保证 demo 主链路不被外部服务阻断
  - `.env.example` / `README.md` / `CODEX.md` / `docs/schema.md` 同步配置说明
- Validation:
  - `python -m compileall backend`
  - `python manage.py check`
  - `python manage.py test`
  - `python -m pip install -r requirements.txt`
  - `python -c "import openai; print(openai.__version__)"`
  - `npm run build`
- Note:
  - 未使用真实厂商 key 调用外部 LLM；provider 分支通过 fake client 和 pipeline 配置测试覆盖。

## 2026-06-05 P3 Merge And Handoff

- PR3 was committed as `5274491 Add multi-provider LLM pipeline`.
- PR3 branch `codex/phase-3-claude-pipeline` was pushed and merged through GitHub PR #2.
- `master` is now at merge commit `18457d4`.
- User completed manual regression testing after merge:
  - default `placeholder` demo mode
  - explicit provider with blank key failure path
  - Compare page invalid YAML validation path
- Next phase is Phase 4. Keep PR5-PR8 focused on backend completeness:
  - stronger chapter/EPUB handling
  - fuller character extraction
  - multi-chapter assembly and Act grouping
  - retry and manual-review fallback
