# 剧本 YAML Schema

## 结构

## PR6 Characters Note

`characters` 仍保持 `name` / `role` / `description` 三列。PR6 起，`description` 会包含简短原文证据，例如对话标记、对白归因或叙述动作出现次数；这不改变前后端 schema，只提高角色表对 prompt 和作者编辑的可用性。

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

## 第一版策略

未配置 LLM key 时，占位转换按章节生成场景，每章前 5 个段落转为 beat。含冒号的段落识别为 dialogue，其余识别为 action。

配置 LLM key 后，后端使用所选厂商将单章转换为 Scene JSON，再组装为同一 YAML Schema。当前支持 `anthropic`、`openai`、`qwen`；OpenAI 和千问共用 OpenAI-compatible client。这样前端和用户编辑格式不随生成方式变化。
