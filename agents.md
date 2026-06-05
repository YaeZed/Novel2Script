# Agents Guide — AI 小说转剧本工具

## 项目概述
将小说文本（3 章以上）自动转换为结构化剧本（YAML），提供原文 vs 剧本并排对照视图，供作者快速获得可编辑的剧本初稿。

## 技术栈

| 层 | 技术 | 用途 |
|----|------|------|
| 前端 | Vue 3 + Vite + TypeScript | SPA，上传/进度/对照视图三页面 |
| 后端 | Django + Django REST Framework | API 服务，LLM 调用编排 |
| AI | Claude API (anthropic Python SDK) | 文本→剧本结构化转换 |
| 校验 | zod (前端) + js-yaml | Schema 校验，YAML 解析 |
| 部署 | Vercel（前端）+ Render（后端） | 免费层部署 |

## 目录结构

```
demo/
├── frontend/                # Vue 3 + Vite 前端
│   ├── src/
│   │   ├── pages/           # Upload, Progress, Compare 三个页面
│   │   ├── components/      # 可复用组件
│   │   ├── api/             # 后端 API 调用封装
│   │   ├── schemas/         # zod schema 定义
│   │   └── composables/     # Vue composables
│   └── ...
├── backend/                 # Django 后端
│   ├── converter/           # 核心转换 app
│   │   ├── services/        # LLM pipeline, epub parser, chapter splitter
│   │   ├── models.py        # ConversionTask
│   │   ├── views.py         # API 端点
│   │   ├── serializers.py   # DRF serializers
│   │   └── prompts.py       # LLM prompt 模板
│   ├── schema/              # YAML Schema 定义 + 校验
│   └── ...
├── docs/
│   └── schema.md            # 剧本 YAML Schema 文档
├── README.md
├── task_plan.md
├── findings.md
├── progress.md
└── agents.md                # 本文件
```

## 核心约定

### Schema 三层结构
```
Act (幕) → Scene (场) → Beat (节拍)
```
Beat 包含字段：`type`（dialogue/action/direction）、`character`（可选）、`content`、`parenthetical`（可选括号指示）

### 转换流程
1. 全文本 → 角色提取（LLM）→ 角色表 JSON
2. 按章节拆分（epub 用 ebooklib，txt 用正则匹配"第X章"）
3. 逐章转换：全文 + 当前章 + 角色表 → Scene/Beat YAML
4. 拼装：各章 YAML 合并 → Act 划分 → 统一角色名
5. 质量兜底：YAML 解析 → zod 校验 → 失败重试 2 次 → 标记人工处理

### API 端点
- `POST /api/convert` → `{task_id}`
- `GET /api/status/<id>` → `{status, progress, chapters_done}`
- `GET /api/result/<id>` → `{script_yaml, characters, chapters[]}`

### 前端路由
- `/` — 上传页（三种输入方式）
- `/progress/:taskId` — 进度页（轮询 + 逐章预览）
- `/compare/:taskId` — 对照视图（按场对齐 + 内联编辑）

## 开发约定

- **语言**：代码/命令/变量名用英文，注释/文档/PR 描述用中文
- **PR 粒度**：每 PR 单一功能，小步提交，参考 task_plan.md 中的 PR 清单
- **分支策略**：从 main 开出 feature 分支，PR 合并后删除
- **可运行**：main 分支任何时刻 `python manage.py runserver` + `npm run dev` 不报错
- **Commit**：英文 message，描述本次变更
- **验证**：改完主动跑 lint/build，不积压错误

## 依赖清单（用于 README）

### 后端 (Python)
- Django + Django REST Framework
- anthropic (Claude API SDK)
- ebooklib (EPUB 解析)
- django-cors-headers (CORS)
- python-dotenv (环境变量)
- PyYAML + jsonschema (YAML 校验)

### 前端 (Node.js)
- Vue 3 + Vite + TypeScript
- Vue Router
- axios
- js-yaml + zod
- 无 UI 框架，手写 CSS

## 关键决策记录

| 决策 | 原因 |
|------|------|
| 不拆前后端独立仓库 | 3 天项目，monorepo 省配置时间 |
| 不做 PDF/Word 解析 | 格式清理成本高，txt+epub 够用 |
| 不做流式/SSE | Render 免费层不支持长连接 |
| 不逐句对齐对照 | 小说→剧本非 1:1 映射，按场对齐更合理 |
| Render 免费层冷启动 ~30s | 前端进度页 toast 提示，可接受 |
| 14 个 PR 分步提交 | 满足持续交付要求，每 PR 单一功能 |
