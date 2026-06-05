# CODEX Guide

## PR6 Current Rule

- 当前分支：`codex/phase-4-pr6-character-grounding`。
- 本 PR 只处理角色提取和 prompt grounding：从全文本中提取来源证据角色表，并把角色表传入每章 LLM prompt。
- 用户影响：减少模型凭空造主角或混用人物名，让作者拿到更可编辑的剧本初稿。
- 不做：Act 划分、跨章结构重组、retry、人工处理标记；这些仍属于 PR7/PR8。

## 项目定位

AI 小说转剧本工具。用户输入 3 章以上小说文本或 EPUB，系统生成结构化剧本 YAML，并提供原文与剧本的并排对照和编辑入口。

## 当前阶段

Phase 3 已合并到 `master`。当前主分支具备可运行的端到端 demo：

- 默认 `LLM_PROVIDER=placeholder`，无 API key 也能完成本地占位转换。
- 显式配置 `anthropic` / `openai` / `qwen` 后，后端会调用对应模型把单章小说转换为 Scene/Beat。
- 进度页会显示当前模型模式；provider 配置错误会显示脱敏后的中文提示。
- 对照页 YAML 编辑已支持“草稿无效但保留最后一次有效结构”的校验体验。

下一阶段进入 Phase 4：补齐更完整的后端转换能力，包括更稳的章节/EPUB 处理、角色提取、多章拼装、Act 划分、重试和人工处理标记。

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

前端读取 `frontend/.env`：

```text
VITE_API_BASE_URL=http://127.0.0.1:8000
```

## 交互规则

- 上传页只突出输入和开始转换，不做营销页。
- 进度页必须告诉用户当前状态和下一步，不只显示百分比。
- 对照页以场景为单位组织，不做逐句强对齐。
- YAML 编辑必须保留用户改动，不自动覆盖。

## PR 规范

- 每个 PR 只做一件事；大功能拆成多个独立 PR。
- PR 标题用一句话说明新增或修改了什么。
- PR 描述必须包含：功能描述、实现思路、测试方式。
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
