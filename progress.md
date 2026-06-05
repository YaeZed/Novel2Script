# Progress Log

## Session: 2026-06-05

### Phase 1: 需求确认
- **Status:** complete
- **Started:** 2026-06-05
- Actions taken:
  - 通过 grill-me 完成 10 轮需求深挖，确认全部技术决策
  - 确认技术栈：Vue 3 + TS + Django + 多厂商 LLM provider
  - 确认输入方式：粘贴 / txt / epub
  - 确认 Schema 颗粒度：Act → Scene → Beat 三层
  - 确认对照视图按场对齐
  - 确认分块策略 + 角色提取流程
  - 确认 3 天时间分配 + 14 PR 策略
  - 初始化 git 仓库
  - 创建 task_plan.md / findings.md / progress.md
- Files created/modified:
  - task_plan.md (created)
  - findings.md (created)
  - progress.md (created)

### Phase 2: 项目初始化 + 核心定义
- **Status:** complete
- Actions taken:
  - Superseded by the detailed Phase 2 build session below.
- Files created/modified:
  - See Phase 2 build session below.

## Test Results
| Test | Input | Expected | Actual | Status |
|------|-------|----------|--------|--------|
|      |       |          |        |        |

## Error Log
| Timestamp | Error | Attempt | Resolution |
|-----------|-------|---------|------------|
|           |       |         |            |

## 5-Question Reboot Check
| Question | Answer |
|----------|--------|
| Where am I? | PR3 merged into `master`; preparing Phase 4 |
| Where am I going? | Phase 4 → Phase 6 |
| What's the goal? | AI 小说→剧本转换工具，3 天上线 |
| What have I learned? | See findings.md |
| What have I done? | 需求确认完成，规划文件已创建 |

---
*Update after completing each phase or encountering errors*

## Session: 2026-06-05 Build Start

### Phase 2: scaffold + schema baseline
- **Status:** complete
- Actions taken:
  - Read `agents.md`, `task_plan.md`, `findings.md`, `progress.md`.
  - Ran planning session catchup; confirmed previous session created planning docs and initial commit.
  - Added `CODEX.md` project execution guide before code changes.
  - Created backend Django + DRF structure under `backend/`.
  - Added `ConversionTask`, serializers, API routes, synchronous placeholder conversion pipeline, chapter splitter, EPUB parser, prompts, and Python schema validation.
  - Created frontend Vue 3 + Vite + TypeScript structure under `frontend/`.
  - Added upload, progress, compare pages, API client, polling composable, zod schema, and base CSS.
  - Added `docs/schema.md`, `README.md`, `.gitignore`, backend requirements, env example.
- Validation:
  - `python -m compileall backend`: passed.
  - `python manage.py check`: passed.
  - `python manage.py migrate --noinput`: passed.
  - Django test client API smoke test: passed.
  - Frontend build: blocked because no Node package manager is available in this environment.
  - Django hidden `runserver` process stayed alive briefly but did not expose `127.0.0.1:8000`; direct `runserver --noreload` stayed running until timeout, so API correctness is currently verified by Django test client instead of a live HTTP server.
- Errors:
  - `rg --files` failed with access denied; used PowerShell file listing.
  - `python -m venv .venv` failed because `ensurepip` could not write temporary wheel files.
  - `node --version` failed with access denied; `npm` command not found.
  - `Invoke-WebRequest http://127.0.0.1:8000/api/convert` could not connect after hidden `runserver`; stopped the invalid background process.
- Files created/modified:
  - `CODEX.md`, `.gitignore`, `README.md`
  - `backend/**`
  - `frontend/**`
  - `docs/schema.md`

### Phase 3: Claude pipeline abstraction
- **Status:** superseded by the later Phase 3 multi-provider implementation
- Actions taken:
  - No Phase 3 code was committed in this early build-start session.
  - Earlier exploratory generator changes were deliberately removed to keep Phase 2 PR single-purpose.
- Remaining:
  - Superseded. Phase 3 was later completed as `codex/phase-3-claude-pipeline` and merged through PR #2.

### Phase 2 user validation
- **Status:** accepted
- User tested the P2 compare flow in the in-app browser.
- Fixed the YAML validation toolbar icon from a save metaphor to a check icon.
- Amended the fix into Phase 2 commit: `8407950 Build phase 2 project scaffold`.
- Pushed branch to GitHub: `origin/codex/phase-2-scaffold`.
- Pushed `master` to GitHub as the PR base branch.
- User merged PR #1 on GitHub; remote `origin/master` is now at merge commit `14ca2bf`.

## Session: 2026-06-05 Phase 3 Execution

### Phase 3: multi-provider single-chapter pipeline
- **Status:** complete
- Actions taken:
  - Read `planning-with-files` instructions and restored `task_plan.md`, `findings.md`, `progress.md`.
  - Ran planning session catchup; unsynced context only repeated earlier planning setup.
  - Fetched `origin/master`; confirmed it is merge commit `14ca2bf` and tree-equal to current Phase 2 commit.
  - Created and switched to `codex/phase-3-claude-pipeline` from `origin/master`.
  - Defined P3 scope: multi-provider single-chapter scene conversion only, with placeholder fallback when no API key exists.
  - Adjusted scope after user request: provider config now supports Anthropic, OpenAI, and Ali Qwen.
  - Added provider-agnostic scene converter module with Anthropic and OpenAI-compatible adapters.
  - Added provider selection from `LLM_PROVIDER` and API key env vars.
  - Added JSON parsing, scene normalization, beat validation, and placeholder fallback.
  - Updated project rules and docs for Anthropic / OpenAI / Qwen configuration.
  - Installed new `openai` dependency from `requirements.txt`.
- Validation:
  - `python -m compileall backend`: passed.
  - `python manage.py check`: passed.
  - `python manage.py test`: passed, 9 tests.
  - `python -m pip install -r requirements.txt`: passed, installed `openai==2.41.0`.
  - `python -c "import openai; print(openai.__version__)"`: passed, `2.41.0`.
  - `npm run build`: passed.
- Errors:
  - Initial skill path lookup used the wrong installation path; corrected to `C:\Users\Administrator\.agents\skills\planning-with-files\SKILL.md`.
  - `rg --files` failed with access denied; used PowerShell file listing.
  - `git fetch origin` first failed with `.git/FETCH_HEAD` permission denied; reran with approved escalation.
  - `git switch` first failed with `.git/index.lock` permission denied; reran with approved escalation.
  - Attempted to read `backend/README.md`; file does not exist, root docs are authoritative.
  - First `json_mode` patch failed because settings file context did not match; reapplied as smaller targeted patches.

### Phase 3 test feedback fix
- **Status:** complete
- User reported a failed progress page showing raw OpenAI 401 error and a masked key fragment.
- Root cause:
  - Backend stored raw provider exceptions in `ConversionTask.error_message`.
  - The shown task had selected OpenAI and received `invalid_api_key`.
- Actions taken:
  - Added backend error formatting so auth/config/model-output errors become user-actionable Chinese messages.
  - Removed raw provider JSON, URLs, and key fragments from user-facing `error_message`.
  - Added regression test for OpenAI invalid-key sanitization.
  - Checked current Django config without printing secrets: `LLM_PROVIDER=qwen`, resolved provider `qwen`, Qwen key set, OpenAI key also exists in environment.
- Validation:
  - `python -m compileall backend`: passed.
  - `python manage.py test`: passed, 10 tests.
  - `python manage.py check`: passed.

### Compare page YAML validation UX fix
- **Status:** complete
- User tested schema validation by changing a beat `type` to `talk`.
- Observed issue:
  - Validation caught the error, but the UI rendered raw Zod JSON in the pane title.
  - The invalid draft caused scene parsing to return null, clearing the left scene list and source pane.
- Actions taken:
  - Split YAML draft text from the last valid parsed script.
  - Scene rail and source pane now keep showing the last valid structure while the editor has invalid YAML.
  - Replaced raw Zod error output with a concise Chinese validation note.
  - Added validation statuses: valid, dirty, invalid.
  - Added human-readable path formatting such as `第 1 幕 / 第 1 场 / 第 3 个节拍`.
- Validation:
  - `npm run build`: passed.
  - `git diff --check`: passed.

### Env key reset behavior fix
- **Status:** complete
- User reported that conversion still worked after clearing keys in `.env`.
- Findings:
  - New Django process currently sees `LLM_PROVIDER=qwen`, `QWEN_API_KEY=empty`; explicit qwen would fail as expected.
  - Browser behavior likely came from a running backend process that had not been restarted after `.env` edits.
  - System environment still has `OPENAI_API_KEY=set`; with `LLM_PROVIDER=auto`, Python dotenv's default non-override behavior could still select that system key even when `.env` is blank.
- Actions taken:
  - Changed the default provider to `placeholder`, so blank keys never imply a hidden external API call.
  - Kept `auto` as an advanced provider mode, but removed it as the default.
  - Changed settings so `DEBUG=true` makes `.env` override and explicitly clear system LLM keys; `DEBUG=false` leaves platform environment variables authoritative.
  - Documented that `.env` changes require a Django backend restart.
  - Added status API field `llm_provider` and a progress-page mode note.
- Validation:
  - `python manage.py shell` confirmed current `.env` blank OpenAI key is no longer filled from system environment.
  - `python -m compileall backend`: passed.
  - `python manage.py check`: passed.
  - `python manage.py test`: passed, 13 tests.
  - `npm run build`: passed.

### Demo deployment model boundary
- **Status:** recorded
- Decision:
  - Demo deployment will support model switching only through administrator-managed environment variables.
  - The user-facing UI will not expose API key input or per-user model settings in this phase.
- Rationale:
  - This keeps the demo focused on the core conversion workflow.
  - It avoids introducing account, key storage, encryption, deletion, billing, and audit requirements before they are needed.
  - BYOK can be revisited later as a productized advanced setting.

## Session: 2026-06-05 Post-PR3 Neat-Freak Sync

### PR3 merge verification and documentation alignment
- **Status:** complete
- Context:
  - User merged PR3 through GitHub PR #2.
  - Local `master` is at merge commit `18457d4`.
  - User manually tested the demo after merge and reported tests passed.
- Actions taken:
  - Reconciled `CODEX.md` with the merged Phase 3 state and Phase 4 handoff.
  - Updated `agents.md` so current implementation and future target conversion flow are separate.
  - Added demo deployment model boundary to `README.md`.
  - Updated `task_plan.md` current phase to Phase 4 and recorded PR3 merge handoff.
- Next:
  - Start Phase 4 from latest `master`.
  - Keep PR5-PR8 scoped to backend completeness rather than model provider plumbing, which is already merged.

## Session: 2026-06-05 Phase 4 PR5 Execution

### PR5: chapter splitting + EPUB parsing
- **Status:** complete
- Actions taken:
  - Read planning-with-files instructions and restored `task_plan.md`, `findings.md`, `progress.md`.
  - Ran planning session catchup; unsynced context only repeated the initial planning handoff and does not change PR5 scope.
  - Confirmed local `master` matches `origin/master` at `9c1a5c2`.
  - Created branch `codex/phase-4-pr5-chapter-epub`.
  - Recorded PR5 first-principles design boundary in `task_plan.md` and `findings.md`.
  - Enhanced chapter heading recognition for Chinese, preface/extra chapters, English `Chapter N`, and numeric headings.
  - Added paragraph-based fallback chunking for long text without chapter headings and oversized chapters.
  - Changed EPUB parsing to use spine order, skip short auxiliary documents, preserve/derive chapter headings, and avoid duplicating `<title>` in body text.
  - Added splitter and EPUB parser regression tests.
- Current scope:
  - Strengthen chapter splitting and EPUB parsing only.
  - Keep character extraction, Act merging, retry, and manual-review flags for PR6-PR8.
- Validation:
  - `python -m compileall .`: passed.
  - `python manage.py check`: passed.
  - `python manage.py test`: passed, 16 tests.
  - `npm run build`: passed.
- Errors:
  - First `python manage.py test` run failed because `\s*` in the heading regex consumed newlines and made the English/preface split test return one chapter.
  - Fixed by changing regex whitespace to line-local whitespace (`[^\S\n]`), then reran tests successfully.

### PR5 hand-test feedback: compare scene YAML positioning
- **Status:** complete
- User observed in the browser that switching scenes updated the source text but left the YAML editor visually on the previous/full document position.
- Root cause:
  - Compare page kept the YAML editor as one full-document textarea and only changed `activeScene`; it did not move the editor cursor/scroll position to the selected scene.
- Action taken:
  - Added scene selection handling in `ComparePage.vue` that scrolls to the selected scene's YAML block.
  - Reworked YAML positioning to detect scene blocks by YAML structure (`source_chapter` + `beats`) instead of a fixed two-space `- number` regex.
  - Added per-scene source text scroll memory so returning to a scene restores that scene's original scroll position.
  - Kept full-document YAML editing/download behavior unchanged.
- Validation:
  - `npm run build`: passed.
