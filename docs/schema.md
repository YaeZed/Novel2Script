# 剧本 YAML Schema

## 结构

剧本文件固定为三层结构：

```text
Script → Act（幕）→ Scene（场）→ Beat（节拍）
```

示例：

```yaml
title: 作品标题
characters:
  - name: 林照
    role: 主要角色
    description: 原文证据：2 处对话标记
acts:
  - number: 1
    title: 第一幕：开端
    scenes:
      - number: 1
        title: 第一章 雨夜
        source_chapter: 1
        summary: 林照发现旧戏院异常。
        beats:
          - type: dialogue
            character: 林照
            content: 今晚不能再等了。
```

## 字段约定

| 层级 | 字段 | 说明 |
|------|------|------|
| Script | `title` | 作品或任务名称 |
| Script | `characters` | 来源证据角色表 |
| Character | `name` | 角色名 |
| Character | `role` | 角色定位 |
| Character | `description` | 对话标记、对白归因或叙述动作等原文证据摘要 |
| Act | `number` | 幕序号，从 1 开始 |
| Act | `title` | 幕标题，如 `第一幕：开端` |
| Scene | `number` | 全剧连续场序号，从 1 开始 |
| Scene | `source_chapter` | 对应原文章节序号，用于对照页定位原文 |
| Scene | `summary` | 场景摘要 |
| Beat | `type` | `dialogue`、`action`、`direction` |
| Beat | `character` | 对话角色，可选 |
| Beat | `content` | 节拍正文 |
| Beat | `parenthetical` | 括号指示，可选 |

## 生成策略

- 未配置真实模型 key 时，`placeholder` 按章节生成占位场景，每章前若干段落转为节拍。
- 配置 `anthropic`、`openai` 或 `qwen` 后，后端使用所选模型将单章转换为 Scene JSON，再组装为统一 YAML。
- 单章模型输出必须经过 JSON 解析、字段归一化和 schema 校验。
- 真实模型输出的节拍会按章节原文锚点稳定排序，降低对白或叙述顺序被模型重排的概率。
- 真实模型转换单章时会按 `LLM_SCENE_MAX_ATTEMPTS` 做章节级重试。

## 三幕边界

- 少于 3 个 Scene 时保持单幕：`第一幕：全篇`。
- `placeholder` 或模型边界不可用时，3 个及以上 Scene 使用确定性三幕拆分：开端、展开、收束。
- 真实模型 provider 会在所有 Scene 生成后读取场景标题、摘要、节拍概览和来源章节，建议三个连续幕范围。
- 后端只接受有序、连续、非空且完整覆盖全部 Scene 的三幕边界；非法结果回退确定性拆分。
- 模型三幕判断只影响 Scene 属于哪一幕，不改写 Scene、Beat、角色表或来源章节。

## Partial 草稿

长文处理期间，每完成一个章节后会保存一次 schema-valid partial 草稿。partial 草稿只使用单幕：

```yaml
acts:
  - number: 1
    title: 已处理部分
    scenes: []
```

这样用户可以提前进入对照页查看已处理内容，且后续新增章节不会导致已处理场景在 `展开` 和 `收束` 之间漂移。

## 人工处理场景

真实模型重试后仍无法得到合法 Scene 时，后端会生成一个符合现有 Schema 的“需人工处理”场景：

- `title` 追加 `（需人工处理）`。
- `source_chapter` 保持原文章节序号。
- `summary` 和第一个 `direction` beat 说明该章需要人工改写。
- 不新增必填字段，前后端 YAML schema 保持兼容。

认证失败、API key 缺失、provider 配置错误不会生成占位场；这些问题需要先修正服务端配置。
