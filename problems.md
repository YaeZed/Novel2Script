# Problems Log

## 2026-06-05: LLM key 置空后仍触发转换

### 现象
- 用户把 `backend/.env` 里的模型 key 置空后，前端仍然可以提交转换。
- 这会造成安全和体验错觉：用户以为没有调用外部模型，实际可能仍被系统环境变量中的 key 命中，导致小说内容外发和额度消耗。

### 根因
- `python-dotenv` 默认不会覆盖系统环境变量；如果 Windows/终端里残留 `OPENAI_API_KEY`，`LLM_PROVIDER=auto` 仍可能选择 OpenAI。
- 运行中的 Django 进程不会在 `.env` 修改后自动重读配置；不重启后端会继续使用旧 key。
- `auto` 作为默认值不适合安全优先的本地开发，因为它会隐式选择第一个可用 key。

### 决策
- 默认 `LLM_PROVIDER=placeholder`，只做本地占位转换，不调用外部 API。
- 真实模型必须显式配置 `LLM_PROVIDER=anthropic` / `openai` / `qwen`。
- 显式 provider 缺 key 时直接失败，并提示补 key 或切回 `placeholder`。
- `auto` 保留为高级模式，但不作为默认值。
- `DEBUG=true` 的本地开发环境中，`backend/.env` 覆盖系统环境变量；`DEBUG=false` 的部署环境中，平台环境变量优先。
- 修改 `.env` 后必须重启 Django 后端。

### 修复
- `backend/novel_script_converter/settings.py`
  - 默认 `LLM_PROVIDER` 改为 `placeholder`。
  - 使用 `load_dotenv(..., override=DEBUG)`：本地 `.env` 可覆盖系统环境，生产环境不覆盖平台配置。
  - 额外处理 `.env` 中的空 key：`DEBUG=true` 时，空值会显式覆盖系统环境变量；`.env` 未声明的 LLM key 会从进程环境中移除，避免系统残留 key 被误用。
- `backend/.env.example` / `README.md` / `CODEX.md`
  - 默认 provider 改为 `placeholder`。
  - 明确 `auto` 的风险和 `.env` 修改后需要重启。
- `GET /api/status/<id>`
  - 增加非敏感字段 `llm_provider`，便于前端展示当前是否在调用真实模型。
- `frontend/src/pages/ProgressPage.vue`
  - 进度页显示当前模式：本地占位、真实模型或配置异常。
- `backend/converter/tests.py`
  - 增加测试：`placeholder` 即使存在 key 也不调用外部 provider。
  - 增加测试：显式 provider 缺 key 必须失败。

### 验证
- `python -m compileall backend`
- `python manage.py check`
- `python manage.py test`
- `npm run build`
- `python manage.py shell` 非敏感检查：`.env` 中空的 OpenAI key 不再被系统环境变量补回。
