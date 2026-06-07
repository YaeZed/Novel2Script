# 剧本 YAML Schema

## 结构

## PR6 Characters Note

`characters` 仍保持 `name` / `role` / `description` 三列。PR6 起，`description` 会包含简短原文证据，例如对话标记、对白归因或叙述动作出现次数；这不改变前后端 schema，只提高角色表对 prompt 和作者编辑的可用性。

## PR7 Act Assembly Note

PR7 起，后端会在所有章节 Scene 生成后做一次确定性拼装：

- Scene `number` 按全剧顺序连续编号，从 1 开始。
- Scene `source_chapter` 保留原文章节序号，用于对照页定位原文。
- 少于 3 个 Scene 时保持单幕：`第一幕：全篇`。
- 3 个及以上 Scene 时按章节顺序拆为三幕：`第一幕：开端`、`第二幕：展开`、`第三幕：收束`。

这个规则先保证长篇结果可浏览、可编辑；更复杂的模型级 Act 大纲放到后续 PR。

## PR11.1 Act Boundary Note

PR11.1 keeps the same YAML shape. It only changes how the backend chooses which scenes belong to each act:

- `placeholder` mode keeps the deterministic split from PR7.
- Real model providers may propose three act ranges from the ordered scene outline after all scenes are generated.
- The backend accepts a proposal only when ranges are ordered, contiguous, non-empty, and cover every scene exactly once.
- Invalid or unavailable proposals fall back to the deterministic split.
- Partial drafts saved during processing use a single `已处理部分` act, so scenes do not move between `展开` and `收束` while later chapters are still being generated.
- Model rationales are used only for validation/debug context in this PR and are not written into the YAML schema.

## PR8 Retry And Manual Review Note

PR8 起，真实模型转换单章时会按 `LLM_SCENE_MAX_ATTEMPTS` 做章节级重试。重试后仍无法得到合法 Scene 时，后端会生成一个符合现有 Schema 的“需人工处理”场景：

- `title` 追加 `（需人工处理）`。
- `source_chapter` 保持原文章节序号，方便对照页定位原文。
- `summary` 和第一个 `direction` beat 说明该章需要人工改写。
- 不新增必填字段，前后端 YAML schema 保持兼容。

认证失败、API key 缺失、provider 配置错误不会生成占位场；这些问题需要先修正服务端配置。

```yaml
title: 作品标题
characters:
  - name: 角色名
    role: 角色定位
    description: 简述
acts:
  - number: 1
    title: 第一幕
    scenes:
      - number: 1
        title: 第一章 雨夜
        source_chapter: 1
        summary: 场景摘要
        beats:
          - type: dialogue
            character: 林照
            content: 今晚不能再等了。
```

## 字段约定

| 层级 | 字段 | 说明 |
|------|------|------|
| Script | `title` | 作品或任务名称 |
| Script | `characters` | 角色表 |
| Act | `number` | 幕序号，从 1 开始 |
| Scene | `source_chapter` | 对应原文章节序号 |
| Beat | `type` | `dialogue`、`action`、`direction` |
| Beat | `character` | 对话角色，可选 |
| Beat | `content` | 节拍正文 |
| Beat | `parenthetical` | 括号指示，可选 |

## 转换策略

未配置 LLM key 时，占位转换按章节生成场景，每章前 5 个段落转为 beat。含真实角色冒号的段落识别为 dialogue，其余识别为 action。

配置 LLM key 后，后端使用所选厂商将单章转换为 Scene JSON，再把多章 Scene 组装为同一 YAML Schema。当前支持 `anthropic`、`openai`、`qwen`；OpenAI 和千问共用 OpenAI-compatible client。这样前端和用户编辑格式不随生成方式变化。
