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
- `master` 分支始终保持可运行状态

## Research Findings
- `ebooklib` Python 库可解析标准 EPUB2/3 文件，按章节提取纯文本
- `js-yaml` Node.js 端 YAML 解析，`zod` schema 校验可检测缺失字段
- LLM 输出统一要求 JSON Scene，再由后端归一化并生成 YAML；这样各厂商差异不会泄露到前端和用户编辑层。
- Render 免费层 Web Service 15 分钟无请求自动休眠，首次唤醒需 ~30s
- Vercel 免费层 100GB 带宽/月，函数执行超时 10s（前端静态资源不影响）
- 三章小说约 2-5 万中文字符 → Claude 3.5 Sonnet 128K 上下文可一次容纳，但分块输出更稳定
- EPUB 内部是 XHTML/HTML 文件集合 + container.xml 导航 + toc.ncx 目录，`ebooklib` 可直接按 spine 顺序读取

## Technical Decisions
| Decision | Rationale |
|----------|-----------|
| Vue 3 + Vite + TS 前端 | 用户最熟悉的技术栈 |
| Django (DRF) 后端 | 用户熟悉，ORM/admin 减省代码量 |
| 多厂商 LLM provider | Anthropic/OpenAI/千问可按环境切换，单章输出统一收敛到 Scene JSON |
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

## 2026-06-06 PR9 Upload Page Findings

### First-principles framing
- 上传页的核心任务是收集素材并启动转换，不是展示产品卖点。首屏应直接呈现输入控件和主操作。
- 三种输入方式本质上是同一个提交合同：最终向 `/api/convert` 提供 `text` 或 `file`。前端应该围绕“素材是否就绪”组织状态，而不是把三种模式拆成三套视觉系统。
- 用户不需要在上传页理解模型 provider、Act/Scene/Beat 细节或 YAML 校验；这些信息会在进度页和对照页承担。

### Scope decisions
- PR9 保留粘贴、文件、示例三种入口。示例入口有价值，因为无素材时也能完成端到端验收。
- 上传页只显示与当前动作有关的短反馈：文本字数、文件名/类型、示例章节数量、提交错误。
- 可复用组件只抽基础按钮和标题区。现在抽表单框架或复杂布局会过早泛化，因为 PR10/PR11 还会继续暴露真实复用点。
- 进度页/对照页可以切到新基础组件，但不在 PR9 深改它们的业务体验。
- 用户界面和用户可见错误提示不能直接暴露“前端、后端、API、provider、Schema、YAML、Act、Scene、Beat”等技术词。普通作者只需要知道当前页面、处理服务、剧本格式、处理方式和下一步动作。

### Current implementation findings
- 当前分支已有草稿：`AppButton.vue`、`SectionHeader.vue`，以及进度页/对照页的局部组件替换。
- `ConvertView` 接受 `text` 或 `file`，EPUB 通过文件名后缀识别；非 EPUB 文件按 UTF-8 文本读取。
- 前端 `createConversion` 使用 `FormData`，因此上传页只需要确保同一时间提交一种有效输入。
- 当前上传页文案和布局过薄，缺少素材状态反馈；右侧 YAML 预览是静态装饰，应该改成更有任务感的结果摘要。

### Environment findings
- `rg` 在此 Windows 沙箱继续被拒绝执行；源码搜索使用 `Get-ChildItem` + `Select-String`。
- 标准嵌套分支名 `codex/phase-5-pr9-upload-page` 无法创建 ref 目录；已使用 `codex-phase-5-pr9-upload-page`。

## 2026-06-06 PR7 Multi-Chapter Assembly Findings

### First-principles framing
- The current missing product value is structure, not another generation pass. Once chapters already become scenes, the user needs a script-shaped outline that can be scanned and edited.
- The shortest reliable path is deterministic assembly after scene generation: preserve chapter order, renumber scenes globally, then split scenes into Acts.
- A model-generated act outline is deferred. It could be richer, but it adds cost, latency, and failure modes before retry/manual-review fallback exists.

### Scope decisions
- PR7 should keep `source_chapter` stable. The compare page uses that field to find the original chapter text, so Act grouping must not change it.
- Scene `number` should become a global script number, not a per-chapter number. This makes the scene rail easier to scan and avoids repeated `1` values if later a chapter creates multiple scenes.
- Inputs with fewer than 3 scenes should stay in a single Act. Three or more scenes use a simple three-act split: opening, development, resolution.
- PR7 does not add retry, partial failure state, or manual processing markers. Those belong to PR8.

### Environment findings
- Creating branch `codex/phase4-pr7` failed because Git could not create the nested ref path.
- Creating `codex-phase4-pr7` first failed on `.git/refs` permission, then succeeded with elevated `git switch`.
- `rg` is not executable in this sandbox (`Access denied`), so source search uses PowerShell `Get-ChildItem` + `Select-String`.
- A broad `Select-String` over `backend` accidentally searched `db.sqlite3` and produced noisy binary output. Future searches should include only source extensions and exclude SQLite files.

## 2026-06-06 PR8 Retry And Manual Review Findings

### Current implementation findings
- `run_conversion_task` currently builds the scene converter once, then calls `convert_chapter` once per chapter. Any exception bubbles to `ConvertView`, which marks the whole task `failed`.
- `format_conversion_error` already sanitizes provider/auth/config failures. PR8 should preserve that hard-failure path instead of hiding bad keys behind fallback scenes.
- The existing script schema permits a normal Scene with a direction beat, so a manual-review placeholder can stay schema-valid without expanding frontend zod validation.
- The frontend already shows `error_message` on the progress page and allows opening compare only for `completed` tasks. A partial fallback should therefore remain `completed` with a warning message, not introduce a new terminal status.

### Scope decisions
- Retry belongs at chapter conversion, not around the whole task. A whole-task retry would repeat successful chapters and increase cost/latency.
- Provider configuration errors before conversion, and authentication errors during conversion, stay non-recoverable. User action is to fix `.env`, not edit a placeholder script.
- Retry exhaustion produces a scene titled with the original chapter title plus a manual-processing marker, `source_chapter` stays unchanged, and the first beat tells the author what to do next.

### Implementation findings
- A manual-review scene can stay within the current schema by using normal `title`, `summary`, and `direction`/`action` beats. This avoids frontend validation churn.
- Unknown Scene fields are not needed for the marker. Keeping the marker in visible standard fields makes the scene rail, YAML editor, and downloaded YAML all self-explanatory.
- The progress page should treat `completed + error_message` as a warning state, not a red failure state, because the next user action is “open compare and edit marked scenes.”

## 2026-06-05 Demo Deployment Model Decision

- Demo 版只支持部署管理员通过环境变量切换模型，不在用户界面开放 API key 设置。
- 选择这个边界的原因：
  - 用户目标是快速看到“小说转剧本”的核心效果，而不是先理解模型厂商、key、base URL、费用和错误排查。
  - API key 属于安全和计费边界。把 key 输入框暴露给普通用户，会把账号体系、密钥加密、删除、脱敏、额度、审计一起引入。
  - 演示部署只需要一个可信管理员维护 `LLM_PROVIDER`、`OPENAI_API_KEY`、`QWEN_API_KEY` 和模型名，复杂度最低。
- 对用户体验的影响：
  - 普通用户只上传和查看结果，路径更短。
  - 模型切换由部署方完成，适合 demo 和课程展示。
  - 未来若要商业化或多人使用，再设计 BYOK（Bring Your Own Key）设置页，而不是现在提前暴露。

## 2026-06-05 Post-PR3 Documentation Sync Findings

- PR3 已合并到 `master` 后，文档需要从“正在做 Phase 3”切换到“Phase 3 已完成，准备 Phase 4”。
- `agents.md` 不能把未来目标流程写成当前事实。当前实现是轻量角色表、逐章 Scene 转换、统一 YAML 组装；LLM 角色提取、多章 Act 拼装、retry 和人工标记仍属于 Phase 4。
- Superseded on 2026-06-06: PR6/PR7 已把当前实现推进到全文来源证据角色表、逐章 Scene 转换、多章 Act 拼装；剩余 Phase 4 目标是 retry 和人工处理标记。
- 分支约定必须跟仓库实际一致：当前主分支是 `master`，不是 `main`。
- README 需要明确 demo 版模型切换属于部署管理员边界，用户界面不开放 API key 设置。
- 下一阶段文档写法原则：先写“当前实现”，再写“后续目标”，避免后续 agent 或评委把 roadmap 当成已交付能力。

## 2026-06-05 PR5 Chapter And EPUB Findings

### First-principles framing
- 要解决的问题不是“支持更多格式”本身，而是让后端拿到可转换、可追踪、可定位失败的章节结构。
- 最直接路径：统一三种输入来源，先做文本清洗，再识别章节标题；无法识别时按长度兜底分块，避免长文本一次性进入 LLM。
- 从零设计会把章节拆分作为纯数据边界：`input -> chapters[] -> scene conversion`。这样后续 PR6 角色提取、PR7 Act 合并、PR8 retry 都能复用同一章节列表。

### PR5 scope decisions
- PR5 只保证章节/EPUB 进入 pipeline 的结构质量，不改变 LLM provider 抽象。
- EPUB 只支持标准 EPUB2/3 的 spine 顺序文本抽取；复杂目录修复、PDF/Word 清洗不进入本 PR。
- 章节标题要尽量保留，因为它会影响进度页展示、结果中的 source chapter，以及后续按章定位错误。
- 没有章节标题的长文本需要自动 chunk。用户影响：系统会继续转换，而不是要求用户先手动分章。

### Current implementation findings
- `chapter_splitter.py` 目前只识别中文 `第X章/节/回/卷/部` 标题；无标题长文本会成为单个“全文”章节。
- `epub_parser.py` 目前按 `book.get_items_of_type(ITEM_DOCUMENT)` 返回顺序拼接文本，不保证遵循 EPUB spine 阅读顺序。
- `pipeline.py` 已经消费 `Chapter` dataclass，因此 PR5 可以集中增强 splitter/parser，不需要改 LLM provider 代码。

### PR5 implementation findings
- 正则标题识别不能使用裸 `\s*` 作为行尾/行首空白，因为 Python `\s` 会匹配换行，导致章节标题跨行误吞正文。
- 多文档 EPUB 的天然边界是 spine 文档顺序。即使文档内部没有“第 X 章”标题，也应生成可拆分标题，用户才能在进度页看到真实章节推进。
- EPUB `<head><title>` 适合做章节名，但不应该进入正文；否则对照视图会重复显示技术性标题。
- 目录/封面/版权页只做轻量跳过：文件名或标题明显为 nav/toc/cover/copyright 且内容较短时排除，避免误删真实章节。

---
*Update this file after every 2 view/browser/search operations*
*This prevents visual information from being lost*

## 2026-06-07 PR11 Compare View Findings

### First-principles framing
- 对照页的本质是作者校对工作台，不是结果文件查看器。核心任务链路是：选中一场、读原文依据、理解剧本节拍、修改草稿、确认格式可继续。
- 场景是最稳定的对齐单位；逐句对齐会制造虚假的精确感，也会让小说改编场景的合并/删减变得难解释。
- 右侧编辑区继续编辑完整剧本文件，而不是只编辑当前场景。原因是当前没有保存接口和局部合并语义，全文编辑能保持下载结果完整，场景跳转只负责定位。

### Scope decisions
- PR11 聚焦前端对照页体验，不改后端 API，也不引入保存、差异合并或多人协作。
- 可抽组件的真实重复点是“场景导航”和“格式提示/操作区”；页面级轮询、YAML 定位和增量更新仍留在 `ComparePage.vue`，避免把业务流程藏进通用组件。
- 样式继续沿用 PR9/PR10 的 8px 面板、低饱和绿灰、共享按钮和标题区；对照页要更像工作台，减少大段说明文字。

## 2026-06-06 PR10.1 Incremental Compare Findings

### First-principles framing
- 长文等待体验的核心不是更频繁刷新，而是让已经完成的转换价值尽早可用。
- 用户进入对照页后的首要任务是阅读和编辑，后台新增内容只能补充，不能覆盖正在编辑的文本、跳转当前场景或打乱滚动位置。
- 最小可行边界是：后端保存 partial script，进度页提供入口，对照页顶部显示进度并轮询新增结果。

### Scope decisions
- PR10.1 should remain an extension of PR10 progress behavior, not the full PR11 compare-page redesign.
- The compare page can auto-apply new result data only when the editor has no local dirty changes. If the user has edited YAML, the page should show a quiet “有新内容” action instead of replacing `yamlText`.
- Do not introduce a merge editor or save API yet. That belongs to a later editing persistence pass if needed.

## 2026-06-05 Build Findings

### Product path
- 第一版采用同步占位转换，不先引入后台队列。原因：当前最重要的是验证上传、状态、结果、对照编辑这条用户主链路；LLM provider 和重试策略可以在同一 Schema 上替换实现。
- 上传入口保留三种方式：粘贴、文件、示例。示例输入用于无素材时立即体验端到端流程。
- 对照页按 Scene 组织，左侧场景列表，主区域原文与 YAML 并排。原因：小说到剧本不是逐句映射，Scene 是更稳定的编辑单位。

### Implementation decisions
- 新增 `CODEX.md` 作为项目执行规则，补齐“新项目先建规则”的约束。
- 后端使用 `ConversionTask` 持久化输入、状态、角色表、章节和 YAML。当前同步执行，未来可把 `run_conversion_task` 移到队列而不改 API。
- Python 端 `schema/script_schema.py` 负责 JSON Schema 校验和 YAML dump；前端 `src/schemas/script.ts` 用 zod 做编辑侧校验。
- EPUB 解析先用 `ebooklib` + 标准库 `HTMLParser`，避免为初版引入额外 HTML 解析依赖。

### Environment findings
- `python -m compileall backend` 通过。
- `python manage.py check` 通过。
- `python manage.py migrate --noinput` 通过。
- Django test client 样例调用 `/api/convert` 返回 201，任务状态 `completed`，结果 YAML 包含角色表和两章 Scene。
- 当前环境没有 `npm/pnpm/yarn/corepack`，Codex app 自带 `node.exe` 在普通 shell 中被拒绝执行，因此前端 build 暂时无法在本机完成。
- `python -m venv .venv` 失败于 `ensurepip` 临时目录权限；改用系统 Python 安装后端依赖并完成验证。`.venv/` 和 `.tmp/` 已纳入 gitignore。

## 2026-06-05 Phase 2 Merge Findings

### GitHub state
- Phase 2 PR #1 was merged into `master`.
- Remote `origin/master` is at merge commit `14ca2bf`.
- Phase 2 feature branch remains `origin/codex/phase-2-scaffold` at `8407950`.
- Local `master` is behind `origin/master` and should be synced before starting Phase 3.

### Frontend verification
- Usable Node tooling exists at `C:\Users\Administrator\AppData\Local\nvm\v20.19.5`; in this sandbox, invoking it may require elevated tool permission.
- Frontend dependencies are installed and `package-lock.json` is part of Phase 2.
- Deprecated `lucide-vue-next` was replaced by `@lucide/vue`.
- `npm run build` passed.

### Phase boundary
- Historical note from the Phase 2 handoff: no Phase 3 code was committed at that time.
- Superseded current state: Phase 3 was later completed and merged through PR #2. `master` is now at merge commit `18457d4`.
- Earlier exploratory Claude generator work was removed before P2 was finalized, so the Phase 3 branch started cleanly from `origin/master`.
- Hidden/background Django `runserver` processes did not expose `127.0.0.1:8000` in this desktop sandbox. Use a foreground terminal for backend live testing here.

## 2026-06-05 Phase 3 Design Findings

### First-principles framing
- 要解决的问题：把“章节文本”变成符合既有 YAML Schema 的 Scene/Beat 结构，而不是一次性解决全书质量。
- 最直接路径：保留现有 API、模型、前端和 placeholder，只把后端 scene 生成器替换成可插拔 provider converter。
- 从零设计：会先定义 `chapter -> scene` 的纯函数边界，再把 provider/API key/env 放在边界外；这样测试不依赖真实网络，未来 retry/队列/角色表都能沿用同一接口。

### P3 decisions
- 支持 Anthropic、OpenAI、阿里千问三类 provider；OpenAI 和千问共用 OpenAI-compatible client。原因：避免单一厂商锁死，国内外环境都能跑。
- 默认使用 `placeholder`，显式选择 `anthropic` / `openai` / `qwen` 才调用真实 LLM。原因：用户必须明确知道内容是否会发到外部模型。
- LLM 输出使用 JSON scene，再由后端组装 YAML。原因：JSON 更容易稳定解析，YAML 仍作为最终用户可编辑产物。
- 不静默吞掉 LLM 错误。原因：用户配置了真实 AI 后，错误应暴露在任务状态里，避免误以为真实转换成功。
- P3 不实现 retry。原因：重试和人工标记属于 PR8，提前加入会扩大 PR3 的行为面。
- `LLM_PROVIDER=auto` 按 Anthropic → OpenAI → 千问选择第一个可用 key；显式指定 provider 但缺 key 时失败。原因：auto 可能误用系统环境残留 key，只保留为高级模式，不作为默认。
- OpenAI 默认启用 JSON mode；千问默认不发送 `response_format`，仅用 prompt 约束 JSON。原因：OpenAI 官方明确支持 JSON mode，千问兼容文档主要承诺 OpenAI SDK、base_url 和模型名迁移，先避免可选参数兼容风险。

### Provider documentation findings
- OpenAI Chat Completions 支持 `response_format={"type":"json_object"}` JSON mode，可用于要求模型返回可解析 JSON：https://platform.openai.com/docs/api-reference/chat/create-chat-completion
- OpenAI 官方文档强调 API key 不能暴露在浏览器或客户端，应在服务端从环境变量加载：https://developers.openai.com/api/reference/overview
- 阿里云百炼千问支持 OpenAI 兼容接口，只需调整 API Key、BASE_URL 和模型名称；北京地域 base URL 为 `https://dashscope.aliyuncs.com/compatible-mode/v1`，示例模型 `qwen-plus`：https://help.aliyun.com/zh/model-studio/compatibility-of-openai-with-dashscope
- OpenAI 官方模型页显示 GPT-5 系列是当前更强的新模型，同时 GPT-4.1 mini 仍是可用的较快低成本模型；P3 保留 `OPENAI_MODEL` 可配置，默认先用 Chat Completions 兼容面更稳的 `gpt-4.1-mini`：https://platform.openai.com/docs/models
- Anthropic 文档显示 Claude Sonnet 4 是高性能模型，CLI 示例中也出现 `claude-sonnet-4-20250514` 模型 ID；P3 默认使用该模型但允许 `.env` 覆盖：https://docs.anthropic.com/en/docs/welcome

### P3 implementation findings
- `openai` SDK 已加入后端依赖，安装后本机版本为 `2.41.0`。
- OpenAI adapter 默认发送 `response_format={"type":"json_object"}`；千问 adapter 默认不发送，避免 OpenAI-compatible 可选参数兼容风险。
- Provider 配置和转换逻辑已隔离在 `build_scene_converter` 与 `llm_scene_converter.py`，pipeline 只面向 `SceneConverter` 接口。
- 没有真实 API key 的情况下，placeholder fallback 仍通过 `/api/convert` 测试主链路。
- 用户测试发现原始 OpenAI 401 错误会暴露到进度页；已改为后端统一清洗错误信息。原则：用户只需要知道下一步该检查哪个配置，不需要看到厂商返回的原始 JSON 和 key 片段。
- 当前本机 `.env` 为 `LLM_PROVIDER=qwen` 且 `QWEN_API_KEY=empty`，显式 qwen 会失败；系统环境中仍有 `OPENAI_API_KEY`，但 `DEBUG=true` 时 `.env` 空 key 已会清掉系统残留 key。
- 用户测试 YAML 编辑时把 `type` 改为 `talk`，前端把 Zod 原始错误渲染到标题并清空场景。修复原则：编辑器允许无效草稿存在，阅读/对照区继续使用最后一次有效结构；错误提示必须是人能读懂的位置和修正方向。
- 用户把 `.env` key 置空后仍能转换。排查显示：旧后端进程未重启会继续使用旧配置；同时系统环境中有 `OPENAI_API_KEY=set`，`load_dotenv` 默认不覆盖系统变量且空值不一定清理系统值。已改为 `DEBUG=true` 时 `.env` 空 LLM key 显式清空进程环境，默认 provider 改为 `placeholder`。

### Environment findings
- Local `origin/master` after fetch is merge commit `14ca2bf`; its tree matches Phase 2 feature commit `8407950`.
- Current Phase 3 branch: `codex/phase-3-claude-pipeline`.
- `backend/README.md` does not exist; project documentation currently lives in root `README.md` and `CODEX.md`.

## 2026-06-05 PR6 Character Grounding Findings

### First-principles framing
- The user does not need a decorative cast list; the product needs a reliable source-derived identity layer so generated script beats keep character names stable.
- The shortest useful path is local extraction before model calls: collect character evidence from the whole source, then pass that evidence into each chapter prompt.
- A full cross-chapter identity resolver is intentionally out of scope. PR6 should improve the signal that already exists in the source without adding a second LLM pipeline.

### Current implementation findings
- `extract_character_table` lives inside `pipeline.py` and only reads line-start speaker labels matching `Name: dialogue`.
- `build_chapter_prompt` already includes `Known characters JSON`, but weak extraction means that grounding input is often empty or incomplete.
- Placeholder conversion currently ignores the character table and treats any colon-like paragraph as dialogue, including possible metadata labels.

### PR6 decision
- Implement a deterministic extractor first. It supports no-key demo mode, is testable, and avoids making character extraction reliability depend on another provider call.
- Store only the existing schema fields (`name`, `role`, `description`) for now, with descriptions carrying compact evidence text. This keeps frontend YAML validation unchanged.

### Hand-test feedback
- A pasted inline sample like `时间：、地点：、林照：对白` exposed that the placeholder scene builder still treated the first colon label as a speaker when the character table was empty.
- A quoted attribution sample like `“别出声。”沈岚低声说。` proved character extraction worked, but placeholder output stayed as action, which made no-key demo behavior look weaker than the grounding layer.
- Resolution: detect inline speaker labels after metadata labels, reject metadata labels as speakers even without a character table, split multi-label placeholder paragraphs when a real speaker label appears, and convert Chinese attributed quotes into dialogue beats.

## 2026-06-06 PR10 Progress Page Findings

### First-principles framing
- 进度页的核心不是展示百分比，而是在等待期间降低不确定性：任务是否已接收、是否还在推进、当前处理到哪一章、失败后下一步是什么。
- 小说转换天然按章节推进，所以章节标题和摘录比内部轮询细节更有解释力。百分比只作为辅助反馈。
- 如果提交接口等待转换完成才返回任务号，进度页无法完成职责；必须先返回任务号，再让页面轮询状态。

### Current implementation findings
- `ConvertView.post` 当前创建任务后同步调用 `run_conversion_task(task)`，因此用户点击“开始转换”会停在上传页，直到转换结束才进入 `/progress/:taskId`。
- `run_conversion_task` 已在处理中持续写入 `progress`、`chapters_done` 和 `total_chapters`，但同步提交路径让这些中间状态基本不可见。
- 后端模型已有 `chapters` JSON 字段和 `chapter_to_payload` 摘录生成逻辑；把章节 payload 在拆分后尽早保存即可支撑进度页逐章预览，不需要新增表或改结果接口。
- 状态接口目前只返回进度数字和处理方式，缺少 `input_name`、`source_format` 和 `chapters`。PR10 可以扩展状态接口，保持结果接口兼容。

### Scope decisions
- 使用轻量后台线程启动现有转换流程，适合当前 demo 和 Render 免费层；不在 PR10 引入 Celery、Redis 或任务队列运维成本。
- 后台线程中的异常继续使用现有 `format_conversion_error` 写入 `failed + error_message`，避免把原始厂商错误暴露给普通作者。
- 进度页文案继续避免 `API/provider/YAML/Schema` 等技术词，保留“处理服务、处理方式、剧本初稿、对照编辑”等普通中文。

### Hand-test feedback
- 用户上传《且听风吟》EPUB 后，进度页显示 99 个处理单元。后端任务 `5f25b8c2-36c9-4fe7-964a-36ae2c516521` 的保存数据表明并非前端编号错误，而是 EPUB 解析把版权信息、版权申明、数字出版说明、译序分块、村上春树年谱和音乐列表都放进了章节列表。
- 修复方向：在 EPUB 解析层过滤明显非正文页面，而不是在进度页隐藏数字。进度页文案同时从“逐章预览”收窄为“逐段预览/素材”，因为长章节分块是处理单元，不一定等于原书章号。
