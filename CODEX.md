# CODEX Guide

## 项目定位

AI 小说转剧本工具。用户输入 3 章以上小说文本或 EPUB，系统生成结构化剧本 YAML，并提供原文与剧本的并排对照和编辑入口。

## 当前阶段

Phase 2：建立可运行骨架与 Schema 基线。

第一版采用同步占位转换：提交文本后立即生成可校验的 YAML 草稿。这样用户可以先验证上传、进度、结果、对照编辑这条主链路，后续再替换为 Claude API 管道。

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
└── progress.md
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
ANTHROPIC_API_KEY=
```

前端读取 `frontend/.env`：

```text
VITE_API_BASE_URL=http://127.0.0.1:8000
```

## 交互规则

- 上传页只突出输入和开始转换，不做营销页。
- 进度页必须告诉用户当前状态和下一步，不只显示百分比。
- 对照页以场景为单位组织，不做逐句强对齐。
- YAML 编辑必须保留用户改动，不自动覆盖。

## 技术决策

| 决策 | 为什么 | 对用户的影响 |
|------|--------|--------------|
| 同步占位转换先行 | 最短路径验证端到端体验 | 无 API key 也能试用主流程 |
| Django 模型存任务结果 | 免费层部署简单，避免先引入队列 | 初版可靠但长文本会等待 |
| Scene 级对照 | 小说和剧本不是逐句映射 | 对照更自然，编辑成本更低 |
| Schema 双端校验 | 后端保证输出结构，前端保护编辑体验 | 错误能早发现并定位 |
