# Agents Guide — AI 小说转剧本工具

## 项目概述
将小说文本（3 章以上）自动转换为结构化剧本（YAML），提供原文 vs 剧本并排对照视图，供作者快速获得可编辑的剧本初稿。

## 技术栈

| 层 | 技术 | 用途 |
|----|------|------|
| 前端 | Vue 3 + Vite + TypeScript | SPA，上传/进度/对照视图三页面 |
| 后端 | Django + Django REST Framework | API 服务，LLM 调用编排 |
| AI | 多厂商 LLM provider（Anthropic / OpenAI / 阿里千问） | 文本→剧本结构化转换 |
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

### 当前转换流程
1. 接收粘贴文本或 TXT/EPUB 文件，创建 `ConversionTask`
2. 按章节拆分输入内容
3. 从全文本提取来源证据角色表
4. 根据 `LLM_PROVIDER` 选择转换器：
   - `placeholder`：本地占位转换，不调用外部模型
   - `anthropic`：Claude API
   - `openai`：OpenAI API
   - `qwen`：阿里千问 DashScope OpenAI-compatible API
5. 逐章转换为 Scene/Beat；真实模型输出失败会按配置重试
6. 重试耗尽后生成“需人工处理”的 schema-valid Scene，认证/key/provider 配置错误仍直接失败
7. 按全剧顺序重新编号 Scene，并按开端 / 展开 / 收束组装 Act
8. 后端 schema 校验通过后保存 YAML、角色表、章节信息和必要的人工处理提示

### 后续目标流程
1. 更完整的角色统一策略：别名合并、跨章称呼规范化
2. 更高级的 Act 大纲：在当前确定性三幕规则上引入可解释的模型级结构建议
3. 前端 Phase 5 体验打磨：上传、进度反馈、对照编辑的完整验收

### API 端点
- `POST /api/convert` → `{task_id}`
- `GET /api/status/<id>` → `{status, progress, chapters_done, total_chapters, error_message, llm_provider}`
- `GET /api/result/<id>` → `{script_yaml, characters, chapters[]}`

### 前端路由
- `/` — 上传页（三种输入方式）
- `/progress/:taskId` — 进度页（轮询 + 逐章预览）
- `/compare/:taskId` — 对照视图（按场对齐 + 内联编辑）

## 开发约定

- **语言**：代码/命令/变量名用英文，注释/文档/PR 描述用中文
- **PR 粒度**：每 PR 单一功能，小步提交，参考 task_plan.md 中的 PR 清单
- **分支策略**：从最新 `master` 开出 feature 分支，PR 合并后删除
- **可运行**：`master` 分支任何时刻 `python manage.py runserver` + `npm run dev` 不报错
- **Commit**：英文 message，描述本次变更
- **PR 创建**：提交 PR 时直接给 GitHub 创建链接和规范 PR 正文，不检查或依赖本机 `gh`
- **验证**：改完主动跑 lint/build，不积压错误

## 依赖清单（用于 README）

### 后端 (Python)
- Django + Django REST Framework
- anthropic (Claude API SDK)
- openai (OpenAI SDK；同时用于阿里千问 OpenAI-compatible 接口)
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
| 默认 `placeholder` | 无 key 也能演示，且避免系统残留 key 导致误调用真实模型 |
| demo 版不开放用户 API key 设置 | 密钥、计费和审计属于部署管理员边界，用户只需要完成上传转换 |
| Render 免费层冷启动 ~30s | 前端进度页 toast 提示，可接受 |
| 14 个 PR 分步提交 | 满足持续交付要求，每 PR 单一功能 |
