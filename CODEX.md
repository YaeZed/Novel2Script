# CODEX Guide

## Current Rule

- 当前分支：`codex-phase-5-pr10-1-incremental-compare`，从 PR10 合并后的 `master` 开出。
- Phase 4 已合并完成：章节/EPUB 处理、角色提取、prompt grounding、多章拼装、Act 划分、章节级 retry 和人工处理标记都已实现。
- Phase 5 已完成 PR9 上传页和 PR10 进度页，当前正在做 PR10.1 长文处理中查看已处理章节。
- PR10.1 允许为“边处理边查看”做最小后端边界调整：每章完成后保存 partial script；进度页增加“查看已处理”入口；对照页顶部显示处理进度并增量读取新章节。不要重写 LLM provider、retry、Act 组装或引入编辑保存/复杂合并逻辑。

## 项目定位

AI 小说转剧本工具。用户输入 3 章以上小说文本或 EPUB，系统生成结构化剧本 YAML，并提供原文与剧本的并排对照和编辑入口。

## 当前阶段

Phase 5 已完成上传入口。当前端到端 demo 已具备：

- 默认 `LLM_PROVIDER=placeholder`，无 API key 也能完成本地占位转换。
- 显式配置 `anthropic` / `openai` / `qwen` 后，后端会调用对应模型把单章小说转换为 Scene/Beat。
- 后端会先拆分章节/EPUB、提取来源证据角色表，再逐章转换。
- 多章结果会按全剧顺序重新编号 Scene，并按开端、展开、收束组装为 Act。
- 真实模型单章失败会先按 `LLM_SCENE_MAX_ATTEMPTS` 重试；重试后仍失败时生成“需人工处理”的 Scene，任务仍可进入对照页。
- 提交后会立即进入进度页；进度页按任务状态轮询，显示处理方式、章节进展和逐章预览。
- 对照页 YAML 编辑已支持“草稿无效但保留最后一次有效结构”的校验体验；PR10.1 中对照页还需要在用户未编辑时自动载入新增章节，在用户已编辑时只提示有新内容，不自动覆盖。

PR10.1 的前端边界：

- 进度页只增加“查看已处理”入口，不重做 PR10 布局。
- 对照页顶部进度只做轻量工作状态，不打断原有场景栏、原文栏和剧本编辑栏。
- 后台新增内容必须以最小干扰方式进入：用户未编辑时自动更新；用户已编辑时提示手动载入。
- 继续复用 `frontend/src/components/` 里的基础按钮、标题区和状态组件，样式对齐 PR9/PR10 的面板、进度条、按钮和低饱和绿灰体系。
- 用户可见文案继续遵守普通中文规则，避免直接暴露技术词。

## 目录约定

```
demo/
├── frontend/                 # Vue 3 + Vite + TypeScript SPA
│   └── src/
│       ├── api/              # HTTP client and API types
│       ├── components/       # Reusable UI components
│       ├── composables/      # Vue state and polling logic
│       ├── pages/            # Route-level pages
│       └── schemas/          # zod schemas for script YAML
├── backend/                  # Django + DRF API
│   ├── converter/            # Conversion task app
│   │   └── services/         # Pipeline, chapter splitting, EPUB parsing
│   ├── novel_script_converter/
│   └── schema/               # Python JSON Schema validation
├── docs/                     # Product and schema docs
├── task_plan.md
├── findings.md
├── progress.md
└── problems.md               # 已发现问题、根因和修复复盘
```

新目录只放对应职责的文件。跨层共享约定先写到 `docs/` 或 `CODEX.md`，再进入实现。

## 开发命令

### 后端

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

### 前端

```powershell
cd frontend
npm install
npm run dev
```

### 验证

```powershell
cd backend
python -m compileall .
python manage.py check
python manage.py test
```

```powershell
cd frontend
npm run build
```

## 环境变量

后端读取 `backend/.env`：

```text
DJANGO_SECRET_KEY=change-me
DEBUG=true
LLM_PROVIDER=placeholder
LLM_MAX_TOKENS=3000
LLM_SCENE_MAX_ATTEMPTS=2
ANTHROPIC_API_KEY=
ANTHROPIC_MODEL=claude-sonnet-4-20250514
OPENAI_API_KEY=
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4.1-mini
OPENAI_JSON_MODE=true
QWEN_API_KEY=
QWEN_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
QWEN_MODEL=qwen-plus
QWEN_JSON_MODE=false
```

本地开发且 `DEBUG=true` 时以 `backend/.env` 为准，`.env` 会覆盖系统环境变量；部署或 `DEBUG=false` 时平台环境变量优先。修改 `.env` 后必须重启 Django 后端，否则运行中的进程仍使用旧配置。

真实 provider 单章转换默认最多尝试 `LLM_SCENE_MAX_ATTEMPTS=2` 次。模型输出仍无法解析时生成“需人工处理”的 Scene，让作者继续进入对照页；认证、key 缺失和 provider 配置错误属于管理员动作，不做人工占位兜底。

前端读取 `frontend/.env`：

```text
VITE_API_BASE_URL=http://127.0.0.1:8000
```

## 交互规则

- 上传页只突出输入和开始转换，不做营销页。
- 进度页必须告诉用户当前状态和下一步，不只显示百分比。
- 对照页以场景为单位组织，不做逐句强对齐。
- YAML 编辑必须保留用户改动，不自动覆盖。
- 用户界面文案面向普通作者，避免直接显示“前端、后端、API、provider、Schema、YAML、Act、Scene、Beat”等技术词；需要表达时改成“页面、处理服务、服务、处理方式、剧本格式、剧本文件、幕、场、节拍”等自然中文。

## PR 规范

- 每个 PR 只做一件事；大功能拆成多个独立 PR。
- PR 标题用一句话说明新增或修改了什么。
- PR 描述必须包含：功能描述、实现思路、测试方式。
- 提交 PR 时直接给 GitHub 创建链接和规范 PR 正文；不要探测或依赖本机是否安装 `gh`。
- PR 合并后 `master` 必须保持可运行，评委可随时复现演示效果。
- 新阶段从最新 `master` 开分支，分支名使用 `codex/<phase-or-feature>`。

## 技术决策

| 决策 | 为什么 | 对用户的影响 |
|------|--------|--------------|
| 同步占位转换先行 | 最短路径验证端到端体验 | 无 API key 也能试用主流程 |
| 默认 placeholder，显式选择真实 provider | 防止系统环境残留 key 导致用户误把内容发到外部模型 | 用户明确知道当前是否会联网、是否会花额度 |
| 多厂商 LLM provider | 避免产品被单一厂商锁死，国内外 key 都能接 | 用户只改 `.env` 就能换模型服务 |
| Django 模型存任务结果 | 免费层部署简单，避免先引入队列 | 初版可靠但长文本会等待 |
| Scene 级对照 | 小说和剧本不是逐句映射 | 对照更自然，编辑成本更低 |
| Schema 双端校验 | 后端保证输出结构，前端保护编辑体验 | 错误能早发现并定位 |
