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
