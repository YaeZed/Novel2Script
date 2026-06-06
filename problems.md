# Problems Log

## 2026-06-06: EPUB 进度页素材数量多于用户预期章节数

### 现象
- 用户在进度页手测时上传一个预期约 98 章的 EPUB，但页面显示 99 个处理素材。
- 示例任务：`5f25b8c2-36c9-4fe7-964a-36ae2c516521`。
- 进度页显示的数量来自后端实际解析并保存的处理单元，不是前端编号从 0/1 开始造成的展示偏差。

### 根因
- EPUB 解析只按 spine 顺序抽取文档，过滤规则过宽，导致非正文页面也进入转换流程。
- 该任务中混入了版权信息、版权申明、数字出版说明、译者序拆分段、作者年谱、音乐列表等前后附属内容。
- 对用户来说，“章节数”应该接近正文阅读结构；但系统内部的“处理单元”还会包含长章节拆分后的段落，因此页面文案不能简单等同原书章节数。

### 用户影响
- 进度页数量会让用户怀疑系统读错书，降低对转换结果的信任。
- 非正文页面进入转换会浪费处理时间，并可能把版权页、年谱、附录误转成剧本内容。

### 处理决策
- 根治点放在后端 EPUB 解析：过滤明显的非正文前后材料，而不是在前端隐藏或修正数字。
- 进度页文案从严格“章节”调整为“素材 / 逐段预览”，避免把内部处理单元误导成原书章节。
- 已生成的旧任务不会自动重算；用户需要重新上传同一 EPUB 才能看到修正后的数量。

### 修复与验证
- 修复位置：`backend/converter/services/epub_parser.py`。
- 回归测试：`backend/converter/tests.py` 覆盖版权页、出版说明、译者序、年谱、音乐列表过滤。
- 已验证：
  - `python manage.py test converter.tests.EpubParserTests`
  - `python -m compileall backend`
  - `python manage.py check`
  - `python manage.py test`
  - `node node_modules\vue-tsc\bin\vue-tsc.js --noEmit`
  - `node node_modules\vite\bin\vite.js build`

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
