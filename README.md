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

当前版本是端到端骨架：支持粘贴文本或上传 TXT/EPUB，后端生成占位剧本 YAML。Claude API 管道会在后续 Phase 3 接入。
