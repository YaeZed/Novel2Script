# 剧本 YAML Schema

## 结构

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

占位转换按章节生成场景，每章前 5 个段落转为 beat。含冒号的段落识别为 dialogue，其余识别为 action。Claude API 接入后仍保持同一 Schema，避免前端和用户编辑格式反复变化。
