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

## 转换流程

- 后端会先从全文本提取角色表，再逐章生成 Scene/Beat。
- 角色提取依据包括行首对话说话人、引号对白归因、叙述动作线索，并过滤 `时间`、`地点`、`备注` 等元数据标签。
- LLM prompt 已加入 grounding 约束：只基于当前章节原文生成，优先使用角色表中的名字，不凭空补主角、关系或跨章剧情，并保持节拍顺序贴近原文。
- 真实模型输出的节拍会再按章节原文锚点做稳定排序，避免后文对白提前到前文叙述之前。
- 所有章节 Scene 生成后，后端会统一按全剧顺序编号。少于 3 个 Scene 保持单幕；3 个及以上 Scene 组装为开端、展开、收束三幕。

## 三幕边界行为

- `LLM_PROVIDER=placeholder` 使用确定性三幕拆分，保证无 key 演示稳定。
- 真实模型 provider 会在所有场景生成后额外执行一次三幕边界判断。模型只读取场景序号、来源章节、标题、摘要和节拍概览，然后建议开端、展开、收束的连续场景范围。
- 后端只接受完整覆盖全部场景且没有重叠、空幕、缺口的建议；模型不可用或输出无效时回退到确定性拆分，不让转换失败。
- 长文仍在处理时，partial 草稿统一放在 `已处理部分`，最终三幕标签只在任务完成后出现。
- 当前还不支持在页面上手动调整并保存三幕边界。

## API

- `POST /api/convert`：创建转换任务，返回 `{ task_id }`
- `GET /api/status/<id>`：返回任务状态、进度、素材预览和是否已有可查看草稿
- `GET /api/result/<id>`：返回 YAML、角色表和章节信息

## 依赖

后端：

- Django + Django REST Framework
- django-cors-headers
- python-dotenv
- PyYAML + jsonschema
- ebooklib
- anthropic
- openai

前端：

- Vue 3 + Vite + TypeScript
- Vue Router
- axios
- js-yaml + zod
- @lucide/vue

## 原创功能

- 粘贴、TXT、EPUB 三种输入入口。
- 章节拆分、EPUB 正文抽取和非正文过滤。
- 来源证据角色表，并将角色证据输入逐章转换。
- 多厂商真实模型转换和无 key 的本地占位转换。
- 章节级重试与“需人工处理”兜底场景。
- 长文处理中查看已处理内容，并保护用户本地编辑不被自动覆盖。
- 原文与剧本按场对照，支持格式检查和剧本文件下载。
- 基于剧情事件的最终三幕边界规划，失败时回退确定性拆分。

## 当前能力

当前版本支持粘贴文本或上传 TXT/EPUB，后端会生成符合 Schema 的剧本 YAML。

- `LLM_PROVIDER=placeholder` 时：使用本地占位转换，便于无 key 演示端到端流程。
- `LLM_PROVIDER=anthropic` / `openai` / `qwen` 且配置对应 key 时：使用真实模型将单章小说转换为 Scene/Beat。

后端 `.env` 可配置：

```text
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

`LLM_PROVIDER` 支持 `placeholder`、`anthropic`、`openai`、`qwen`、`auto`。默认 `placeholder` 只跑本地占位转换，不调用外部模型。显式指定 `anthropic` / `openai` / `qwen` 但缺少对应 key 时，任务会失败并返回配置错误。`auto` 会按 Anthropic → OpenAI → 千问的顺序选择第一个已配置 key，只建议明确知道当前环境变量状态时使用。

真实模型单章转换默认最多尝试 `LLM_SCENE_MAX_ATTEMPTS=2` 次。重试后仍拿不到合法 Scene 时，该章节会生成“需人工处理”的占位场，任务仍可进入对照页；认证、key 缺失或 provider 配置错误不会走占位兜底，会直接失败并提示修正配置。

本地开发且 `DEBUG=true` 时，`backend/.env` 会覆盖系统环境变量；把某个 key 留空就表示禁用该 key。部署或 `DEBUG=false` 时，平台环境变量优先。修改 `.env` 后需要重启 Django 后端。

演示版只支持部署管理员通过环境变量切换模型，不在用户界面开放 API key 设置。这样用户侧只需要完成上传和查看结果，密钥、额度和模型选择留在部署边界内。
