# Task Plan: AI 小说转剧本工具 (Novel-to-Script)

## Goal
构建一个 AI 辅助剧本创作工具，用户上传 3 章以上小说文本（txt/epub/粘贴），自动转换为结构化剧本（YAML 格式），并提供原文 vs 剧本并排对照视图，3 天内完成并部署上线。

## Current Phase
Phase 5

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
| PR10.1 | 长文处理中查看已处理章节 + 对照页增量更新 | 1-2 commits | Phase 5 |
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
- [x] PR8: 错误兜底（retry + 人工标记）
- **Status:** complete

### Phase 5: 前端全部页面
- [x] PR9: 上传页
- [x] PR10: 进度页
- [x] PR10.1: 长文处理中查看已处理章节 + 对照页增量更新
- [x] PR11: 对照视图
- **Status:** complete

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
| PR11 Vite dev server failed with `spawn EPERM` | Normal sandbox start of `node node_modules\vite\bin\vite.js --host 127.0.0.1 --port 5173` | Started Vite with approved elevated permission and confirmed `http://127.0.0.1:5173/` returned 200 |
| PR11 browser screenshot automation unavailable | Tried importing `playwright` in the local Node REPL | Module is not installed; used type check, production build, diff check, and local HTTP check for validation |

## Notes

## 2026-06-06 PR9 Execution Plan

- Problem: 当前上传页仍停留在骨架层，能提交但没有把三种输入方式、素材状态和开始转换动作组织成稳定的产品入口。
- User impact: 作者进入产品后应该马上知道“把文本/文件放进来，然后开始转换”，不需要理解后端 provider、Schema 或部署细节。
- Scope:
  - 打磨上传页三种输入方式：粘贴、TXT/EPUB 文件、示例。
  - 提供清晰的素材状态反馈：字数、文件名/类型、示例预览。
  - 把按钮和区块标题抽成可复用组件，并让进度页/对照页使用同一套基础控件。
  - 优化上传页响应式布局、焦点态、禁用态和提交错误提示。
  - 不改后端转换流程，不扩展进度页和对照页的业务行为。
- First-principles framing:
  - 要解决的问题不是“做一个首页”，而是“让用户把素材可靠交给转换系统”。
  - 最直接路径是以输入方式为主控件，页面只保留完成提交所需的信息和动作。
  - 从零设计会先确定 `input mode -> source readiness -> submit` 的交互闭环，再决定视觉布局；说明文字只在能减少误操作时出现。
- Validation target:
  - `npm.cmd run build`。
  - 浏览器手测上传页三种输入模式、禁用态、提交跳转和移动端布局。

## 2026-06-06 PR9 Completion

- Delivered:
  - 上传页改为输入工作台：粘贴、文件、示例三种模式共享同一条素材就绪和提交路径。
  - 增加素材状态反馈：文本字数、文件名/大小、输入预览和下一步提示。
  - 文件模式隐藏原生 input，只暴露“选择文件/更换文件”这一条清晰操作。
  - 提交失败改为可行动中文提示，后端未启动时提示用户确认 API 服务。
  - 新增 `AppButton` 和 `SectionHeader` 基础组件，并让上传页、进度页、对照页使用同一套按钮/标题结构。
  - 调整全局样式的按钮、分段控件、焦点态、面板和响应式布局，上传页不再读成营销首页。
- Validation:
  - `npm.cmd run build`: passed.
  - `git diff --check`: passed; only CRLF normalization warnings.
  - Browser check on `http://127.0.0.1:5173/`: paste/file/sample modes render correctly, file input no longer appears as duplicate control, disabled/enabled submit states work, missing-backend submit error is actionable.
- Merge:
  - PR9 merged into `master` on 2026-06-06.
  - Local `master` fast-forwarded to `origin/master` at `7d9be12`.
  - Next PR: PR10 progress page.

## 2026-06-06 PR10 Execution Plan

- Problem: 当前提交接口会等转换结束才返回任务号，进度页只能显示完成结果，不能承担“等待、确认任务还在推进、按章预览”的产品职责。
- User impact: 作者提交长文本后应该马上进入进度页，看到素材已接收、当前阶段、处理到哪一章，以及完成后清楚进入对照编辑；失败时也要知道下一步是重试还是联系管理员检查服务。
- Scope:
  - 后端最小调整为提交后立即返回任务号，并在本进程后台执行现有转换流程。
  - 章节拆分完成后尽早保存章节标题和摘录，供进度页逐章预览。
  - 扩展状态接口返回任务名、来源类型和章节预览，不改变结果接口和对照页编辑逻辑。
  - 重做进度页布局、阶段反馈、章节列表、完成/失败下一步动作；样式继续对齐 PR9 的按钮、标题、面板和普通中文文案。
  - 不引入 Celery/队列服务，不改 LLM provider、retry、Act 组装或对照页 YAML 编辑。
- First-principles framing:
  - 要解决的问题不是“显示百分比”，而是“让用户等待时有确定感，并知道任务是否还活着”。
  - 最直接路径是把提交、处理、状态读取拆开：`submit -> task id -> polling -> compare`。
  - 从零设计会把章节作为进度页的主要反馈单位，因为小说转换天然按章推进，百分比只是辅助。
- Validation target:
  - 后端测试覆盖提交后返回 pending/processing、后台失败会写入脱敏错误、状态接口返回章节预览。
  - `python -m compileall backend`, `python manage.py check`, `python manage.py test`, `npm.cmd run build`, `git diff --check`。

## 2026-06-06 PR10 Completion

- Delivered:
  - 提交接口改为创建任务后立即返回 `task_id`，后台线程继续执行现有转换流程。
  - 后台执行失败时继续写入脱敏中文错误，并把任务标记为失败。
  - 章节拆分完成后立即保存章节标题和摘录，状态接口返回任务名、来源类型、章节进度和预览，不返回整章原文。
  - 进度页改为双栏工作台：主进度、来源/章节/处理方式、下一步提示、异常提示和逐章预览列表。
  - 轮询失败提示改为可行动中文，完成后进入对照，失败后返回重新提交。
  - 样式与 PR9 对齐：共享按钮/标题、8px 面板、低饱和绿灰主色、移动端单列。
- Validation:
  - `python -m compileall backend`: passed.
  - `python manage.py check`: passed.
  - `python manage.py test`: passed, 33 tests.
  - `node node_modules\vue-tsc\bin\vue-tsc.js --noEmit`: passed.
  - `node node_modules\vite\bin\vite.js build`: passed.
  - `git diff --check`: passed; only CRLF normalization warnings.
  - Django client smoke test with temporary `LLM_PROVIDER=placeholder`: `POST /api/convert` returned immediately, status progressed to `completed`, status chapter payload only contained `index/title/excerpt`, result returned script content.

## 2026-06-06 PR10.1 Planned Follow-Up

- Problem: 长文章转换时间较长时，进度页只能等待，用户无法先查看已经处理完成的章节，也无法在等待期间开始对照检查。
- User impact: 作者应该能在任务还没完全完成时进入对照页查看已完成草稿；后续章节完成后自动补进来，但不能打断用户当前阅读、选中场景或正在编辑的剧本文本。
- Scope:
  - 进度页在“刷新”右侧增加“查看已处理”入口；只要已有可查看草稿就允许进入对照页。
  - 后端每完成一个处理段就保存一次当前可用的剧本草稿和角色表，让结果接口在处理中也能返回已处理章节。
  - 对照页顶部显示处理进度条和当前状态。
  - 对照页轮询状态和结果，发现新增场景时以最小干扰方式更新：用户未改动草稿时自动替换；用户有未校验/未保存编辑时只提示有新内容，不覆盖编辑区。
  - 不在本次引入多人协作、编辑保存接口、差异合并器或队列系统。
- First-principles framing:
  - 要解决的问题不是“多一个页面入口”，而是“长任务期间已经产生的价值不应该被锁在等待页里”。
  - 最直接路径是让 pipeline 按章节持久化 partial script，让 compare 页消费同一个 result/status 契约。
  - 从零设计会把转换产物视为可增长草稿：`processed scenes -> partial script -> editor`，新增内容只能在不破坏用户当前编辑上下文的前提下进入。

## 2026-06-07 PR11 Execution Plan

- Problem: 当前对照页能显示原文和剧本文件，但信息层级仍像技术调试页；作者缺少“这一场讲什么、来自哪里、要检查哪些节拍、格式是否可继续”的工作台反馈。
- User impact: 作者进入对照页后应该直接按场检查，不需要在全文剧本文本里找位置；场景切换要同步原文依据和编辑区，格式问题要给出可行动提示。
- Scope:
  - 重构对照页布局层级：顶部处理状态保持轻量，主工作区聚焦场景导航、原文依据和剧本草稿。
  - 抽取真实复用组件：场景导航列表、剧本格式提示/操作区，继续复用 `AppButton`、`SectionHeader`、`StatusPill`。
  - 增加当前场景摘要、来源、节拍数量和角色提示，让作者先理解场景再编辑。
  - 保留 PR10.1 增量更新规则：用户未编辑时自动载入，已有本地编辑时只提示手动载入。
  - 不改后端 API、LLM provider、retry、Act 组装、保存接口或复杂合并逻辑。
- First-principles framing:
  - 要解决的问题不是“展示 YAML”，而是“让作者快速判断这一场是否忠于原文并能改成可用剧本”。
  - 最直接路径是围绕 `select scene -> inspect source -> edit draft -> validate/download` 的闭环重排页面。
  - 从零设计会把场景作为主导航单位，因为小说到剧本不是逐句映射；编辑区可以仍保留全文剧本文件，避免引入未设计好的局部保存语义。
- Validation target:
  - `node node_modules\vue-tsc\bin\vue-tsc.js --noEmit`
  - `node node_modules\vite\bin\vite.js build`
  - `git diff --check`

## 2026-06-07 PR11 Completion

- Delivered:
  - 新增 `SceneNavigator.vue`，把场景列表、刷新动作、来源和节拍摘要从页面模板中抽出。
  - 新增 `ScriptValidationPanel.vue`，复用标题区和按钮，承接格式检查、下载动作和校验提示。
  - 对照页主区重排为场景工作台：左侧选场，中间显示原文依据、场景摘要、来源、节拍数和角色，右侧保留完整剧本草稿编辑。
  - 保留 PR10.1 的增量更新保护：本地有编辑时只提示载入新内容，不覆盖草稿。
  - 样式对齐 PR9/PR10 的 8px 面板、按钮、焦点态、进度条和低饱和绿灰体系，并补移动端单列布局。
- Validation:
  - `node node_modules\vue-tsc\bin\vue-tsc.js --noEmit`: passed.
  - `node node_modules\vite\bin\vite.js build`: passed.
  - `git diff --check`: passed; only CRLF normalization warnings.
  - Local Vite server: `http://127.0.0.1:5173/` returned 200 after elevated start.

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

## 2026-06-06 PR8 Execution Plan

- Problem: the current pipeline treats one bad LLM chapter response as a full task failure, so the author cannot open the compare view or salvage already converted chapters.
- User impact: long conversions should keep usable work. If a single chapter cannot be parsed after retry, the author should still receive a YAML draft with a clear manual-processing marker at the affected chapter.
- Scope:
  - Add chapter-level retry around model scene conversion.
  - Keep provider configuration and authentication errors as hard failures with the existing sanitized message.
  - After retry exhaustion, create a schema-valid manual-review scene for that chapter.
  - Surface a concise warning through `error_message` while keeping task status `completed` when fallback scenes exist.
  - Document the retry/manual-review rule.
  - Keep Act grouping and character extraction unchanged.
- First-principles framing:
  - The product problem is not "make every model response perfect"; it is "avoid trapping the author outside the editor."
  - The direct path is to isolate failure at the smallest useful unit: a chapter scene.
  - From zero, the conversion contract should be `chapter -> scene or explicit manual-review placeholder`; the full script should still assemble if each chapter has a scene-shaped result.
- Validation target:
  - Backend tests for retry success, retry exhaustion fallback, and hard provider config/auth failure.
  - `python -m compileall backend`, `python manage.py check`, `python manage.py test`, frontend build, and `git diff --check`.

## 2026-06-06 PR8 Completion

- Delivered:
  - Added chapter-level retry around scene conversion with `LLM_SCENE_MAX_ATTEMPTS`.
  - Kept auth/config/provider errors as hard failures so users get actionable setup guidance instead of misleading placeholders.
  - Added schema-valid manual-review scenes after retry exhaustion, preserving `source_chapter` for compare-page original text lookup.
  - Completed tasks with manual-review scenes now carry a warning in `error_message`, and the progress page shows “已完成，部分章节待处理”.
  - Documented retry/manual-review behavior in README, CODEX, `.env.example`, and schema docs.
- Validation:
  - `python -m compileall backend`: passed.
  - `python manage.py check`: passed.
  - `python manage.py test`: passed, 30 tests.
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
