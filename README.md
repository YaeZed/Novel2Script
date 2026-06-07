# AI 小说转剧本工具

把小说文本转换为结构化剧本 YAML，并提供原文与剧本的并排对照编辑。当前版本面向 demo 和毕业设计验收：默认不调用外部模型，配置服务端密钥后可切换 Anthropic、OpenAI 或阿里千问。

## 功能范围

- 输入：粘贴文本、TXT 文件、EPUB 文件。
- 输出：符合 `Act -> Scene -> Beat` 结构的剧本 YAML，格式详见 [`docs/schema.md`](docs/schema.md)。
- 审阅：按场景查看原文依据和剧本草稿，支持格式检查、下载、浅色/深色护眼阅读、阅读密度、场景标记和文本颜色标记。
- 长文处理：任务处理中可先查看已处理部分；新增内容只在用户没有本地编辑时自动载入。
- 模型：无 key 时走本地占位转换；配置真实 provider 后逐章调用模型，并在单章失败后重试或生成“需人工处理”的场景。

## 技术栈

| 层 | 技术 | 用途 |
|----|------|------|
| 前端 | Vue 3 + Vite + TypeScript | 上传页、进度页、对照页 |
| 后端 | Django + Django REST Framework | 转换任务、状态接口、结果接口 |
| AI | Anthropic / OpenAI / 阿里千问 | 可选真实模型转换 |
| 校验 | PyYAML + jsonschema + js-yaml + zod | 后端产物校验和前端编辑保护 |
| 部署 | Vercel + Render + PostgreSQL | 前端静态部署、后端 API 和任务数据 |

## 本地运行

后端：

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python manage.py migrate
python manage.py runserver
```

前端：

```powershell
cd frontend
npm install
Copy-Item .env.example .env
npm run dev
```

默认访问地址：

- 页面：`http://127.0.0.1:5173`
- 处理服务：`http://127.0.0.1:8000`
- 健康检查：`http://127.0.0.1:8000/healthz`

## 环境变量

后端读取 `backend/.env` 或部署平台环境变量：

```text
DJANGO_SECRET_KEY=change-me
DEBUG=true
DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost
CORS_ALLOWED_ORIGINS=http://127.0.0.1:5173,http://localhost:5173
CSRF_TRUSTED_ORIGINS=http://127.0.0.1:5173,http://localhost:5173
DATABASE_URL=
SECURE_SSL_REDIRECT=false
SECURE_HSTS_SECONDS=0

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

前端读取 `frontend/.env`：

```text
VITE_API_BASE_URL=http://127.0.0.1:8000
```

本地开发且 `DEBUG=true` 时，`backend/.env` 会覆盖系统环境变量；把某个 key 留空就表示禁用该 key。部署或 `DEBUG=false` 时，平台环境变量优先。修改环境变量后需要重启对应服务。

`LLM_PROVIDER` 支持 `placeholder`、`anthropic`、`openai`、`qwen`、`auto`。默认 `placeholder` 只跑本地占位转换，不调用外部模型。显式指定真实 provider 但缺 key 时，任务会失败并提示修正配置。

## 部署

推荐顺序：先部署 Render 后端，拿到后端公开地址；再部署 Vercel 前端，把该地址写入 `VITE_API_BASE_URL`。

### 1. Render 后端

仓库已提供 `render.yaml` 和 `backend/build.sh`。

1. 在 Render 选择 Blueprint，并连接本仓库。
2. Render 会创建：
   - `novel-to-script-api` Web Service
   - `novel-to-script-db` PostgreSQL 数据库
3. 后端构建命令：`bash ./build.sh`
4. 后端启动命令：`python -m gunicorn novel_script_converter.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --timeout 180`
5. 健康检查路径：`/healthz`

Render 会自动注入 `DATABASE_URL` 和 `RENDER_EXTERNAL_HOSTNAME`。如使用自定义域名，需要把域名加入 `DJANGO_ALLOWED_HOSTS`。
`/healthz` 已从 HTTPS 重定向中豁免，平台探活会稳定返回 200。

上线后至少设置这些变量：

```text
DEBUG=false
DJANGO_SECRET_KEY=<Render generated value>
SECURE_SSL_REDIRECT=true
SECURE_HSTS_SECONDS=3600
LLM_PROVIDER=placeholder
```

前端部署完成后，再把前端地址写入：

```text
CORS_ALLOWED_ORIGINS=https://your-frontend.vercel.app
CSRF_TRUSTED_ORIGINS=https://your-frontend.vercel.app
```

如果要启用真实模型，在 Render 环境变量里设置对应 key，并把 `LLM_PROVIDER` 改成 `anthropic`、`openai` 或 `qwen`。密钥只放后端，不进入前端代码。

### 2. Vercel 前端

在 Vercel 新建项目时选择 `frontend` 作为 Root Directory。

建议配置：

```text
Framework Preset: Vite
Build Command: npm run build
Output Directory: dist
Install Command: npm install
```

环境变量：

```text
VITE_API_BASE_URL=https://your-render-service.onrender.com
```

`frontend/vercel.json` 已把所有路径重写到 `index.html`，所以 `/progress/<taskId>` 和 `/compare/<taskId>` 刷新时不会 404。

### 3. 部署后验证

1. 打开 `https://your-render-service.onrender.com/healthz`，应返回 `{"status":"ok"}`。
2. 打开 Vercel 页面，使用示例文本或粘贴 3 章以上文本提交转换。
3. 进度页应显示任务推进；完成后进入对照页。
4. 对照页执行“检查格式”，应提示剧本格式可用。

Render 免费层可能冷启动，首次访问可能等待数十秒。长文本转换由 Web 进程后台线程处理，适合 demo；高并发或生产使用应换成队列和独立 worker。

参考官方部署文档：

- [Render Django 部署文档](https://render.com/docs/deploy-django)
- [Vercel 项目配置文档](https://vercel.com/docs/project-configuration)

## API

- `POST /api/convert`：创建转换任务，返回 `{ task_id }`
- `GET /api/status/<id>`：返回任务状态、进度、素材预览和是否已有可查看草稿
- `GET /api/result/<id>`：返回剧本 YAML、角色表和章节信息
- `GET /healthz`：部署健康检查

## 转换流程

1. 接收粘贴文本或 TXT/EPUB 文件，创建转换任务。
2. 拆分章节；EPUB 会按 spine 顺序抽取正文并过滤明显非正文页面。
3. 从全文本提取来源证据角色表。
4. 根据 `LLM_PROVIDER` 选择本地占位转换或真实模型转换。
5. 逐章生成场景和节拍；真实模型输出失败时按 `LLM_SCENE_MAX_ATTEMPTS` 重试。
6. 重试耗尽后生成“需人工处理”的合规场景，任务仍可进入对照页。
7. 每章完成后保存 partial 草稿；处理中统一放在 `已处理部分`。
8. 最终按全剧顺序重新编号场景，并组装开端、展开、收束三幕。
9. 真实模型 provider 会额外尝试按剧情事件规划三幕边界；非法结果回退确定性拆分。

后端/API 的剧本契约使用英文 key；对照页编辑区显示中文字段，并在校验和解析前映射回内部字段。阅读模式、场景标记、文本颜色标记只保存在当前浏览器，不写入剧本 YAML。

## 依赖清单

后端：

- Django + Django REST Framework
- django-cors-headers
- python-dotenv
- dj-database-url
- psycopg2-binary
- gunicorn
- WhiteNoise
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

## 验证命令

后端：

```powershell
cd backend
python -m compileall .
python manage.py check
python manage.py test
```

前端：

```powershell
cd frontend
npm run build
```

全仓库空白字符检查：

```powershell
git diff --check
```

## 目录结构

```text
demo/
├── backend/                  # Django + DRF API
│   ├── converter/            # 转换任务 app 和核心服务
│   ├── novel_script_converter/
│   ├── schema/               # Python JSON Schema 校验
│   ├── build.sh              # Render 构建脚本
│   └── requirements.txt
├── frontend/                 # Vue 3 + Vite + TypeScript SPA
│   ├── src/
│   └── vercel.json           # Vercel SPA 深链接配置
├── docs/
│   └── schema.md
├── test/                     # 人工验收样例
├── render.yaml               # Render Blueprint
├── CODEX.md
├── task_plan.md
├── findings.md
├── progress.md
└── problems.md
```
