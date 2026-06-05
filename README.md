# AI 小说转剧本工具

把小说文本转换为结构化剧本 YAML，并提供原文与剧本的并排对照编辑。

## 快速开始

后端：

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

前端：

```powershell
cd frontend
npm install
npm run dev
```

默认前端访问 `http://127.0.0.1:5173`，后端 API 为 `http://127.0.0.1:8000`。

## API

- `POST /api/convert`：创建转换任务，返回 `{ task_id }`
- `GET /api/status/<id>`：返回任务状态和进度
- `GET /api/result/<id>`：返回 YAML、角色表和章节信息

## 当前能力

当前版本支持粘贴文本或上传 TXT/EPUB，后端会生成符合 Schema 的剧本 YAML。

- `LLM_PROVIDER=placeholder` 时：使用本地占位转换，便于无 key 演示端到端流程。
- `LLM_PROVIDER=anthropic` / `openai` / `qwen` 且配置对应 key 时：使用真实模型将单章小说转换为 Scene/Beat。

后端 `.env` 可配置：

```text
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

`LLM_PROVIDER` 支持 `placeholder`、`anthropic`、`openai`、`qwen`、`auto`。默认 `placeholder` 只跑本地占位转换，不调用外部模型。显式指定 `anthropic` / `openai` / `qwen` 但缺少对应 key 时，任务会失败并返回配置错误。`auto` 会按 Anthropic → OpenAI → 千问的顺序选择第一个已配置 key，只建议明确知道当前环境变量状态时使用。

本地开发且 `DEBUG=true` 时，`backend/.env` 会覆盖系统环境变量；把某个 key 留空就表示禁用该 key。部署或 `DEBUG=false` 时，平台环境变量优先。修改 `.env` 后需要重启 Django 后端。
