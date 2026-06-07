# CODEX Guide

## 当前状态

- 当前保留分支：`master`。PR11.1 已合并，非 `master` 本地/远端分支已清理。
- Phase 5 已完成：上传页、进度页、处理中查看已处理内容、对照视图、基于剧情事件的三幕边界规划。
- 下一步进入 Phase 6：PR12 深浅/护眼模式与阅读体验、PR13 Schema 文档收束、PR14 部署与 README 完成。
- 后端当前能力包括：章节/EPUB 处理、来源证据角色表、逐章 Scene/Beat 转换、章节级 retry、人工处理场景、partial 草稿、最终三幕边界规划。
- 对照页当前能力包括：场景导航、原文依据、剧本草稿编辑、格式检查、下载，以及长文处理期间的增量载入保护。

## 项目定位

AI 小说转剧本工具。用户输入 3 章以上小说文本或 EPUB，系统生成结构化剧本 YAML，并提供原文与剧本的并排对照和编辑入口。

## 当前阶段

Phase 5 已完成，准备 Phase 6 打磨、文档和部署。当前端到端 demo 已具备：

- 默认 `LLM_PROVIDER=placeholder`，无 API key 也能完成本地占位转换。
- 显式配置 `anthropic` / `openai` / `qwen` 后，后端会调用对应模型把单章小说转换为 Scene/Beat。
- 后端会先拆分章节/EPUB、提取来源证据角色表，再逐章转换。
- 多章结果会按全剧顺序重新编号 Scene。`placeholder` 使用确定性三幕拆分；真实模型 provider 会在最终组装前根据场景事件建议开端、展开、收束的连续范围，非法建议回退到确定性拆分。
- 真实模型单章失败会先按 `LLM_SCENE_MAX_ATTEMPTS` 重试；重试后仍失败时生成“需人工处理”的 Scene，任务仍可进入对照页。
- 提交后会立即进入进度页；进度页按任务状态轮询，显示处理方式、素材进展、预览和“查看已处理”入口。
- 对照页按场景组织：左侧场景导航，中间原文依据，右侧剧本草稿，场景切换同步原文和编辑位置。
- 对照页剧本编辑支持“草稿无效但保留最后一次有效结构”，长文处理时只在用户没有本地编辑时自动载入新内容。
- 真实模型输出的节拍会按原文章节锚点稳定重排，避免对照页出现后文对白提前到前文叙述之前。

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
├── test/                     # Manual hand-test fixtures and expected observations
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
