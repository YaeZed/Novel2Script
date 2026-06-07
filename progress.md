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

## Session: 2026-06-05 Phase 4 PR6 Execution

### PR6: character extraction + prompt grounding
- **Status:** complete
- Actions taken:
  - Read `planning-with-files` instructions and restored `task_plan.md`, `findings.md`, `progress.md`.
  - User confirmed PR5 is merged.
  - Fetched `origin/master`, fast-forwarded local `master` to PR5 merge commit `2badfd1`, and created `codex/phase-4-pr6-character-grounding`.
  - Inspected the current pipeline, prompt builder, schema, serializers, and tests.
  - Recorded PR6 scope: deterministic full-text character extraction plus prompt grounding only.
  - Added `character_extractor.py` for source-derived character evidence from dialogue labels, quoted/prefaced dialogue attribution, narration action hints, and English attribution.
  - Replaced the inline pipeline extractor and passed the richer character table into both LLM prompts and placeholder conversion.
  - Tightened placeholder scene building so known metadata labels such as time/place/note stay as action text instead of fake dialogue when a character table exists.
  - Added prompt grounding rules so model output must stay inside the supplied chapter text and source-derived character table.
- Validation:
  - `python -m compileall backend`: passed.
  - `python manage.py check`: passed.
  - `python manage.py test`: passed, 20 tests.
  - `npm run build`: first attempt blocked by PowerShell `npm.ps1` execution policy; reran with `npm.cmd` and passed.
  - `git diff --check`: passed; only CRLF normalization warnings.

### PR6 hand-test feedback fix
- **Status:** complete
- User browser screenshots showed:
  - `时间：、地点：、林照：对白` produced `characters: []` and a fake dialogue beat with `character: 时间`.
  - `“别出声。”沈岚低声说。` extracted `沈岚` but placeholder still rendered the sentence as action.
- Actions taken:
  - Added inline speaker extraction after punctuation/metadata labels.
  - Added placeholder metadata-label rejection even when no character table exists.
  - Added multi-label placeholder parsing so metadata labels are skipped and real speaker labels can still become dialogue.
  - Added Chinese attributed quote parsing for placeholder dialogue beats with parenthetical voice hints.
- Validation:
  - `python -m compileall backend`: passed.
  - `python manage.py check`: passed.
  - `python manage.py test`: passed, 24 tests.
  - Local smoke conversion confirmed the two screenshot samples now generate `character: 林照` and `character: 沈岚`.
  - `npm.cmd run build`: passed.
  - `git diff --check`: passed; only CRLF normalization warnings.

## Session: 2026-06-06 Phase 4 PR7 Execution

### PR7: multi-chapter assembly + Act grouping
- **Status:** complete
- Actions taken:
  - Read `planning-with-files` instructions and restored `task_plan.md`, `findings.md`, `progress.md`.
  - Ran planning session catchup; detected only old initialization context, unrelated to PR7.
  - Attempted branch `codex/phase4-pr7`; Git could not create the nested ref path in this Windows workspace.
  - Created working branch `codex-phase4-pr7` with elevated `git switch` after `.git/refs` permission blocked the first attempt.
  - Read `CODEX.md`, backend pipeline/schema/tests, frontend schema/compare usage, and docs schema.
  - Updated `CODEX.md`, `task_plan.md`, and `findings.md` with PR7 scope and first-principles design.
  - Added `script_assembler.py` for deterministic script assembly.
  - Wired pipeline output through the assembler after per-chapter Scene conversion.
  - Added unit coverage for multi-act grouping, short-script single-act behavior, global scene numbering, and pipeline YAML persistence.
  - Updated `README.md` and `docs/schema.md` with Act assembly rules.
- Current scope:
  - Normalize generated scenes into continuous full-script numbering.
  - Group scenes into deterministic Acts while preserving `source_chapter`.
  - Keep retry/manual-review fallback out of this PR.
- Validation:
  - `python -m compileall backend`: passed.
  - `python manage.py check`: passed.
  - `python manage.py test`: passed, 27 tests.
  - `npm.cmd run build`: passed.
  - `git diff --check`: passed; only CRLF normalization warnings.
- Errors:
  - `rg` execution is denied in this sandbox; switched to PowerShell file search.
  - A broad `Select-String` over `backend` searched `db.sqlite3` and produced binary noise; future searches should filter source extensions.

## Session: 2026-06-06 Phase 4 PR8 Execution

### PR8: retry + manual-review fallback
- **Status:** complete
- Actions taken:
  - Read `planning-with-files` instructions and restored `task_plan.md`, `findings.md`, `progress.md`.
  - Ran session catchup; unsynced context only repeated old project-initialization messages and does not change PR8 scope.
  - Confirmed local `HEAD` and `origin/master` are both `e791b65`.
  - Created branch `codex/phase-4-pr8-retry-fallback`.
  - Inspected pipeline, LLM scene converter, task model, serializers, view error handling, backend tests, frontend status polling, and progress page.
  - Recorded PR8 scope: chapter-level retry, manual-review placeholder scene after retry exhaustion, hard failure for config/auth errors.
  - Added `conversion_recovery.py` for retry orchestration, non-recoverable error detection, manual-review scene generation, and progress warning text.
  - Wired `run_conversion_task` through chapter-level retry and persisted warning text on completed tasks when fallback scenes exist.
  - Added `LLM_SCENE_MAX_ATTEMPTS` setting and documented it in `.env.example`, README, CODEX, and schema docs.
  - Updated the progress page to show completed-with-warning as “已完成，部分章节待处理”.
  - Added regression tests for retry success, retry exhaustion fallback, and provider auth errors not being retried.
- Current scope:
  - Do not change PR7 Act assembly.
  - Do not add new task statuses unless existing completed/failed semantics cannot express the UX.
- Errors:
  - `git rev-parse --short master origin/master HEAD` failed because this Git invocation needed a single revision with `--short`; reran separate revision checks.
  - First branch creation failed because the sandbox could not create nested `.git/refs/heads/codex/...`; reran with approved escalation.
  - Self-review found a misleading manual-scene sentence claiming the failure reason was summarized on the progress page; removed it and reran validation.
- Validation:
  - `python -m compileall backend`: passed.
  - `python manage.py check`: passed.
  - `python manage.py test`: passed, 30 tests.
  - `npm.cmd run build`: passed.
  - `git diff --check`: passed; only CRLF normalization warnings.

### PR8 hand-test and neat-freak sync
- **Status:** complete
- User hand-tested PR8 fallback flow in the browser and reported no issues.
- Ran `neat-freak` knowledge cleanup:
  - Checked root file inventory, docs inventory, markdown file list, and line counts.
  - Updated `CODEX.md` from PR7/PR8-in-progress wording to PR8-ready-for-PR wording.
  - Updated `agents.md` current conversion flow so retry/manual-review fallback is current behavior, not a future target.
  - Updated `docs/schema.md` to remove the stale “failure fallback later” note.
  - Updated `task_plan.md` current phase to Phase 5 after PR8 completion.
- Validation:
  - Root docs remain under size limits: `CODEX.md` 145 lines, `agents.md` 122 lines, `docs/schema.md` 68 lines.

## Session: 2026-06-06 Phase 5 PR9 Execution

### PR9: upload page
- **Status:** complete
- Actions taken:
  - Read `planning-with-files` instructions and restored `task_plan.md`, `findings.md`, `progress.md`.
  - Ran session catchup; detected only old initialization context, unrelated to PR9.
  - Found existing uncommitted frontend draft on `master`: upload/progress/compare pages already partially switched to `AppButton` and `SectionHeader`.
  - Created working branch `codex-phase-5-pr9-upload-page` after nested `codex/...` branch creation failed in this Windows workspace.
  - Inspected upload page, progress page, compare page, frontend API client, shared styles, and backend convert serializer/view.
  - Recorded PR9 scope in `CODEX.md`, `task_plan.md`, and `findings.md`.
  - Reworked upload page around `mode -> source readiness -> submit`: paste, TXT/EPUB file, and sample modes now share one clear submission path.
  - Added source readiness feedback, text/file preview, file-size display, and Chinese actionable submit-error formatting.
  - Added reusable `AppButton.vue` and `SectionHeader.vue`, then aligned progress and compare page headers/actions to those components.
  - Updated global styles for shared controls, upload layout, focus states, hidden file input, cooler neutral page background, and mobile stacking.
- Current scope:
  - Polish upload page input workflow and visual hierarchy.
  - Reuse only the basic button/header components needed across existing pages.
  - Keep backend conversion and later Phase 5 page behavior unchanged.
- Errors:
  - `rg` execution is denied in this sandbox; using PowerShell source search.
  - `git switch -c codex/phase-5-pr9-upload-page` failed because Git could not create the nested ref path.
  - `git switch -c codex-phase-5-pr9-upload-page` first failed on `.git/refs` permission, then succeeded with elevated permission.
- Validation:
  - `npm.cmd run build`: passed.
  - `git diff --check`: passed; only CRLF normalization warnings.
  - Browser check on `http://127.0.0.1:5173/`: paste/file/sample modes rendered correctly; file mode no longer exposes a duplicate native file button; missing-backend submit error now says to confirm the API is running.

### PR9 user-copy cleanup
- **Status:** complete
- Actions taken:
  - Replaced user-visible technical wording on the upload page with plain Chinese: `YAML` became 剧本文件/剧本初稿, `API/backend` became 服务/处理服务, and preview labels became Chinese.
  - Replaced progress-page model/provider wording with “处理方式”.
  - Replaced compare-page YAML validation labels with “格式检查/剧本格式”.
  - Updated backend user-facing failure messages so progress errors no longer ask ordinary users to edit env/provider/API settings directly.
  - Added the plain-Chinese user-copy rule to `CODEX.md`, `agents.md`, and `findings.md` for future neat-freak sync.

### PR9 merge sync
- **Status:** complete
- Actions taken:
  - User merged PR9 on GitHub.
  - Fetched `origin`; `origin/master` advanced to `7d9be12`.
  - Switched local workspace back to `master` and fast-forwarded it to `origin/master`.
  - Updated `CODEX.md` from PR9 execution state to PR10 handoff state.
  - Recorded PR9 merge status in `task_plan.md`.
- Next:
  - Start PR10 from `master`.
  - Scope PR10 to progress page waiting/feedback/preview behavior only.

## Session: 2026-06-06 Phase 5 PR10 Execution

### PR10: progress page
- **Status:** complete
- Actions taken:
  - Read `planning-with-files` instructions and restored `task_plan.md`, `findings.md`, `progress.md`.
  - Confirmed local `master` was synced to `origin/master` after PR9.
  - Created working branch `codex-phase-5-pr10-progress-page` after nested `codex/...` branch creation failed in this Windows workspace and the flat branch needed elevated `.git/refs` permission.
  - Inspected progress page, upload page, shared styles, polling composable, API client, status/result serializers, views, task model, pipeline, and tests.
  - Recorded PR10 first-principles scope in `task_plan.md` and `findings.md`.
  - Found that `POST /api/convert` synchronously ran conversion before returning `task_id`, which made intermediate progress states invisible to users.
  - Added a lightweight backend task runner so the submit endpoint returns immediately and conversion continues in a background thread in the same process.
  - Kept failure handling through the existing sanitized conversion error formatter.
  - Saved chapter title/excerpt payloads as soon as chapter splitting finishes, so the progress page can show previews during processing.
  - Extended the status response with task name, source type, and chapter previews while excluding full chapter text from polling responses.
  - Rebuilt the progress page with stage copy, progress facts, next-step guidance, and a chapter preview list aligned with PR9 styles.
  - Changed polling failure copy to actionable Chinese instead of raw network/library messages.
- Current scope:
  - Do not introduce Celery/Redis or deployment queue infrastructure in PR10.
  - Do not change LLM provider selection, retry/manual-review rules, Act assembly, or compare-page YAML editing.
- Validation so far:
  - `python -m compileall backend`: passed.
  - `python manage.py check`: passed.
  - `python manage.py test`: passed, 33 tests.
  - `node node_modules\vue-tsc\bin\vue-tsc.js --noEmit`: passed.
  - `node node_modules\vite\bin\vite.js build`: passed.
  - `git diff --check`: passed; only CRLF normalization warnings.
  - Django client smoke test with temporary `LLM_PROVIDER=placeholder`: passed. `POST /api/convert` returned immediately, status reached `completed`, status chapter payload excluded full chapter text, and result returned script content.

### PR10 hand-test feedback: EPUB non-story documents
- **Status:** complete
- User uploaded `且听风吟.epub` and observed 99 progress units for a book expected to have fewer story sections.
- Findings:
  - Saved task `5f25b8c2-36c9-4fe7-964a-36ae2c516521` had 99 chapter payloads.
  - The first payloads were `版权信息`, `版权申明`, a digital publishing note, and a translator preface split into two chunks.
  - The tail payloads were author chronology entries and `《且听风吟》音乐列表`.
  - This was backend EPUB filtering, not a frontend numbering bug.
- Actions taken:
  - Added EPUB non-story filtering for copyright pages, publishing notes, translator preface/afterword, author chronology, and music-list pages.
  - Added a regression test that reproduces those EPUB front/back matter pages and keeps only story sections.
  - Changed progress page labels from strict chapter wording to material/processing-segment wording so long-chapter chunks are not misrepresented as original book chapters.
- Validation:
  - `python manage.py test converter.tests.EpubParserTests`: passed, 2 tests.
  - `python -m compileall backend`: passed.
  - `python manage.py check`: passed.
  - `python manage.py test`: passed, 33 tests.
  - `node node_modules\vue-tsc\bin\vue-tsc.js --noEmit`: passed.
  - `node node_modules\vite\bin\vite.js build`: passed.
  - `git diff --check`: passed; only CRLF normalization warnings.

### PR10.1 follow-up request recorded
- **Status:** planned
- User requested a long-article workflow improvement:
  - Add a “查看已处理” entry next to refresh on the progress page.
  - Allow users to open the compare page while conversion is still running.
  - Show a progress bar at the top of the compare page.
  - Incrementally update later processed chapters with minimal disruption to compare-page reading/editing.
- Decision:
  - Keep the current PR focused on PR10 progress page and EPUB count fix.
  - Add this as Phase 5 `PR10.1` so it can include the necessary backend partial-result persistence and compare-page polling behavior without bloating PR10.

### PR10.1 incremental compare execution
- **Status:** complete
- Actions taken:
  - Created branch `codex-phase-5-pr10-1-incremental-compare` from PR10-merged `master`.
  - Added status response field `can_view_result` so the frontend only shows the compare entry when a real draft exists.
  - Changed the pipeline to persist a schema-valid partial script after each processed chapter.
  - Added progress-page “查看已处理” entry next to refresh while conversion is still running.
  - Added a lightweight progress panel at the top of the compare page using existing `SectionHeader`, `StatusPill`, `AppButton`, `.panel`, `.progress-readout`, and `.meter` styling.
  - Added compare-page polling that auto-loads new server drafts only when the user has not edited the current YAML text.
  - Added a non-destructive “载入新内容” prompt when background processing finishes more chapters while the user has local edits.
- Validation so far:
  - `python manage.py test converter.tests.ConversionApiTests converter.tests.ConversionPipelineTests`: passed, 22 tests.
  - `node node_modules\vue-tsc\bin\vue-tsc.js --noEmit`: passed.
- Final validation:
  - `python -m compileall backend`: passed.
  - `python manage.py check`: passed.
  - `python manage.py test`: passed, 35 tests.
  - `node node_modules\vue-tsc\bin\vue-tsc.js --noEmit`: passed.
  - `node node_modules\vite\bin\vite.js build`: passed.
  - `git diff --check`: passed; only CRLF normalization warnings.

## Session: 2026-06-07 Phase 5 PR11 Execution

### PR11: compare view
- **Status:** complete
- Actions taken:
  - Read `planning-with-files` instructions and restored `task_plan.md`, `findings.md`, `progress.md`.
  - Ran session catchup; it only surfaced old initialization context and did not affect PR11.
  - Created branch `codex-phase-5-pr11-compare-view` from local `master`; normal branch creation hit `.git/refs` permission and succeeded with approved elevated Git permission.
  - Inspected `CODEX.md`, PR11 plan context, `ComparePage.vue`, shared components, API types, script schema, progress page patterns, and global styles.
  - Recorded PR11 first-principles scope in `CODEX.md`, `task_plan.md`, and `findings.md`.
  - Added reusable `SceneNavigator.vue` and `ScriptValidationPanel.vue`.
  - Reworked the compare page into a scene workflow: scene list, source evidence, scene summary/facts, full draft editor, validation actions, and download guard.
  - Updated compare-page styles for wider scene navigation, denser scene metadata, source reading frame, scene facts, and responsive single-column behavior.
- Current scope:
  - Improve compare-page scene workflow, visual hierarchy, inline editing feedback, and component reuse.
  - Preserve PR10.1 incremental update behavior and the current backend API contract.
- Final validation:
  - `node node_modules\vue-tsc\bin\vue-tsc.js --noEmit`: passed.
  - `node node_modules\vite\bin\vite.js build`: passed.
  - `git diff --check`: passed; only CRLF normalization warnings.
  - Vite dev server available at `http://127.0.0.1:5173/` after elevated start; normal sandbox start failed with `spawn EPERM` from esbuild.
  - Browser screenshot automation was not available because `playwright` is not installed in the local Node REPL.

## Session: 2026-06-07 Phase 5 PR11.1 Execution

### PR11.1: model-driven act boundaries
- **Status:** in progress
- Actions taken:
  - Restored `task_plan.md`, `findings.md`, and `progress.md` with the planning-with-files workflow.
  - Ran session catchup; the unsynced context only repeated old initial planning setup and does not change PR11.1 scope.
  - Fetched `origin/master`, switched local `master`, and fast-forwarded to PR11 merge commit `abaff79`.
  - Attempted branch `codex/phase-5-pr11-1-act-boundaries`; Git could not create the nested refs directory in this Windows workspace.
  - Created working branch `codex-phase-5-pr11-1-act-boundaries` after `.git/refs` permission required elevated branch creation.
  - Recorded PR11.1 scope in `task_plan.md` and `findings.md`.
- Current scope:
  - Add backend model-assisted act boundary proposal from already generated scenes.
  - Keep deterministic split as fallback and keep `placeholder` deterministic.
  - Do not change compare-page interaction or add manual act boundary editing.
- Hand-test feedback:
  - User stopped the backend and noticed scenes previously under `收束` appeared under `展开`.
  - Confirmed this came from partial drafts recalculating deterministic three-act splits as each new processed scene was persisted.
  - Changed partial persistence to use a single `已处理部分` act; final completed scripts still use model-assisted or deterministic three-act boundaries.
  - User retested with the six-section lighthouse sample. Final result grouped scenes 1-2 as `开端`, 3-5 as `展开`, and 6 as `收束`, with no partial drift observed.
  - User found `背面写着` was extracted as a character in the same sample. Confirmed saved task also contained false `救船终于` evidence.
  - Tightened character extraction to reject object/narration labels and embedded action fragments, and added prompt guidance so generated scenes treat these as action/direction details.
  - User found chapter 3 dialogue/order drift in the compare page: 沈岚's later line appeared before the old administrator's earlier background information.
  - Added chronological beat-order guidance to scene prompts and a backend source-anchor reorder pass for real model scene outputs.
  - Added regression coverage for the lighthouse chapter 3 order case.
  - Added `test/README.md` with manual fixture directory rules and `test/lighthouse-pr11-1.md` with the lighthouse hand-test sample and expected observations.
- Validation after beat-order fix:
  - `python -m compileall backend`: passed.
  - `python manage.py check`: passed.
  - `python manage.py test`: passed, 46 tests.

## Session: 2026-06-07 Neat-Freak Sync After PR11.1

### Documentation and memory cleanup
- **Status:** complete
- Actions taken:
  - Confirmed local and remote branches only retain `master` after PR11.1 merge.
  - Read root docs, `docs/schema.md`, `test/` fixtures, project rules, README, planning files, and relevant backend/frontend source files.
  - Removed stale PR11/PR11.1 branch-specific rules from `CODEX.md` and rewrote the current-state section for merged `master`.
  - Updated `agents.md` so model-assisted act boundaries, partial drafts, and `can_view_result` are current behavior rather than future work.
  - Rewrote `docs/schema.md` from PR-note fragments into current Schema behavior.
  - Updated `README.md` with current three-act behavior, dependencies, and original feature list.
  - Added the PR11.1 hand-test issues to `problems.md`.
  - Updated `task_plan.md` to Phase 6 and recorded PR11.1 completion/merge.
- Validation:
  - Stale branch/current-rule scan: cleaned root docs; remaining branch names only exist in historical progress/findings records.

## Session: 2026-06-07 Phase 6 PR12 Execution

### PR12: reading modes and scene marks
- **Status:** complete
- Actions taken:
  - Restored `task_plan.md`, `findings.md`, and `progress.md` with the planning-with-files workflow.
  - Ran session catchup; unsynced context only repeated old initialization messages and does not change PR12 scope.
  - Confirmed working tree was clean on `master`.
  - Tried branch `codex/phase-6-pr12-reading-mode`; nested ref creation failed in this Windows workspace.
  - Created branch `codex-phase-6-pr12-reading-mode` with elevated Git permission.
  - Recorded PR12 first-principles scope in `task_plan.md` and `findings.md`.
  - Added reusable `ReadingControls.vue` for compare-page light/dark eye-care mode and reading size controls.
  - Added reusable `SceneMarkControls.vue` and shared `frontend/src/types/review.ts`.
  - Extended `SceneNavigator.vue` to render scene mark badges from props.
  - Wired `ComparePage.vue` to persist reading preferences globally and scene marks per task in local storage.
  - Updated compare-page styles for scoped reader variables, dark mode, source/draft text sizing, mark badges, and mobile toolbar layout.
  - Updated `CODEX.md` with the new `frontend/src/types/` directory convention.
  - Added YAML draft color marking as a follow-up: selected text can be marked red/orange/yellow/green/blue through a reusable highlight editor.
  - Kept YAML color marks in local browser storage per task so the downloaded script text remains unchanged.
- Current scope:
  - Add reusable frontend components for reading appearance and scene marking.
  - Persist reading preferences and scene marks locally.
  - Keep backend APIs, conversion flow, YAML schema, and act grouping unchanged.
- Errors:
  - `rg --files` is denied in this environment; using PowerShell file listing and Node file reads.
  - Normal nested `codex/...` branch creation failed; using the flat branch name consistent with earlier Windows PRs.
- Validation:
  - `node node_modules\vue-tsc\bin\vue-tsc.js --noEmit`: passed.
  - `node node_modules\vite\bin\vite.js build`: passed.
  - `git diff --check`: passed; only CRLF normalization warnings.

### PR12 hand-test feedback: YAML color marking menu
- **Status:** fixed
- User reported:
  - Color menu opens, but selected content is covered.
  - Selecting a color does not visibly change the draft.
  - Clicking the `x` button does not close the color menu.
- Root cause:
  - `.compare-pane .yaml-editor` overrode the transparent textarea styling, so the input layer covered the mirror highlight layer.
  - The selection stayed expanded after applying a color, so browser selection paint kept covering the new visual mark.
  - `selectionchange` reopened the menu for the same selected range immediately after close.
- Actions taken:
  - Added dismissed-selection tracking in `YamlHighlightEditor.vue`.
  - Collapsed the textarea selection after applying a highlight.
  - Prevented menu mouse actions from stealing the textarea selection.
  - Added a higher-specificity `.compare-pane .yaml-highlight-input` style so the textarea remains transparent and the mirror layer shows highlights.
- Validation:
  - `node node_modules\vue-tsc\bin\vue-tsc.js --noEmit`: passed.
  - `node node_modules\vite\bin\vite.js build`: passed.
  - `git diff --check`: passed; only CRLF normalization warnings.

### PR12 hand-test feedback: YAML selection and cursor alignment
- **Status:** fixed
- User reported:
  - Selecting YAML text showed doubled/overlapped content.
  - The text cursor could appear offset from the visible text.
- Root cause:
  - The first highlight editor implementation made both the textarea and mirror layer participate in visible text rendering. Even small differences in textarea and `pre` line wrapping, scrollbar width, or font rendering can make selection/cursor positions drift.
- Action taken:
  - Changed the highlight mirror layer to render only transparent text plus colored mark backgrounds.
  - Restored textarea text rendering so the visible text, selection, and cursor are all from the browser's native textarea layer.
- User impact:
  - YAML editing remains stable and cursor-accurate.
  - Color marks still appear as background highlights without relying on two visible text layers aligning perfectly.
- Validation:
  - `node node_modules\vue-tsc\bin\vue-tsc.js --noEmit`: passed.
  - `node node_modules\vite\bin\vite.js build`: passed.
  - `git diff --check`: passed; only CRLF normalization warnings.

### PR12 hand-test feedback: YAML typography
- **Status:** fixed
- User reported the YAML editor font felt inconsistent and visually rough.
- Action taken:
  - Added shared CSS font variables for app text and YAML surfaces.
  - Changed YAML editor, YAML preview, and highlight editor layers from Cascadia/Consolas-first to the app's Chinese-friendly font stack.
  - Increased YAML editor default size and line-height for long-form reading.
- User impact:
  - YAML draft now visually aligns with the rest of the compare page.
  - Chinese script content no longer falls back into a code-font look during review.
- Validation:
  - `node node_modules\vue-tsc\bin\vue-tsc.js --noEmit`: passed.
  - `node node_modules\vite\bin\vite.js build`: passed.
  - `git diff --check`: passed; only CRLF normalization warnings.

### PR12 hand-test feedback: Chinese YAML and highlight alignment
- **Status:** fixed
- User asked for YAML field names to be Chinese without affecting backend processing, and reported highlight background drift after typography changes.
- Actions taken:
  - Added compare-page display-layer YAML localization: backend English keys are shown as Chinese labels in the editor.
  - Added reverse mapping before frontend validation and scene parsing, so backend/API/schema contracts remain unchanged.
  - Localized beat type values in the editing surface: `dialogue/action/direction` display as `对白/动作/舞台指示`.
  - Updated scene YAML block detection to support Chinese labels (`编号`, `来源章节`, `节拍`) while retaining English fallback.
  - Added highlight range realignment from stored selected text so old marks recover after field-label or typography changes.
  - Adjusted YAML font stack to a Chinese-friendly but stable stack shared by textarea and highlight layer.
- User impact:
  - The YAML editor is now Chinese-first for the target Chinese novel workflow.
  - Backend result format and validation model stay stable.
  - Existing local color marks no longer remain on unrelated text when layout/content shifts.
- Validation:
  - `node node_modules\vue-tsc\bin\vue-tsc.js --noEmit`: passed.
  - `node node_modules\vite\bin\vite.js build`: passed.
  - `git diff --check`: passed; only CRLF normalization warnings.
