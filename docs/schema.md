# 剧本 YAML Schema

本文档是当前项目的剧本文件格式说明。它描述两层契约：

- **内部契约**：后端保存、接口返回、后端校验使用的标准 YAML，字段名为英文 key。
- **作者编辑表面**：对照页为了中文写作体验，会把字段名和节拍类型显示为中文；校验和场景解析前再映射回内部契约。

颜色标记、场景标记、阅读模式都属于本地审阅状态，不属于剧本 YAML Schema。

## 结构总览

剧本固定为三层结构：

```text
Script -> Act（幕）-> Scene（场）-> Beat（节拍）
```

内部标准 YAML 示例：

```yaml
title: 灯塔样例
characters:
  - name: 沈岚
    role: 主要角色
    description: 原文证据：2 处对话标记，1 处对白归因
acts:
  - number: 1
    title: 第一幕：开端
    scenes:
      - number: 1
        title: 第一章 雾中来信
        source_chapter: 1
        summary: 沈岚在灯塔收到异常来信。
        beats:
          - type: dialogue
            character: 沈岚
            content: 今晚不能再等了。
          - type: action
            content: 海风把信纸压在灯塔门口。
```

对照页编辑区会显示为中文字段：

```yaml
标题: 灯塔样例
角色表:
  - 姓名: 沈岚
    身份: 主要角色
    说明: 原文证据：2 处对话标记，1 处对白归因
幕:
  - 编号: 1
    标题: 第一幕：开端
    场:
      - 编号: 1
        标题: 第一章 雾中来信
        来源章节: 1
        摘要: 沈岚在灯塔收到异常来信。
        节拍:
          - 类型: 对白
            人物: 沈岚
            内容: 今晚不能再等了。
          - 类型: 动作
            内容: 海风把信纸压在灯塔门口。
```

## 字段定义

| 层级 | 字段 | 必填 | 类型 | 说明 |
|------|------|------|------|------|
| Script | `title` | 是 | string | 作品名或任务名 |
| Script | `characters` | 是 | array | 来源证据角色表，可以为空数组 |
| Script | `acts` | 是 | array | 幕列表，至少 1 幕 |
| Character | `name` | 是 | string | 角色名 |
| Character | `role` | 否 | string | 角色定位，如“主要角色”“次要角色” |
| Character | `description` | 否 | string | 角色来源证据摘要 |
| Act | `number` | 是 | integer | 幕序号，从 1 开始 |
| Act | `title` | 是 | string | 幕标题 |
| Act | `scenes` | 是 | array | 该幕包含的场列表 |
| Scene | `number` | 是 | integer | 全剧连续场序号，从 1 开始 |
| Scene | `title` | 是 | string | 场标题 |
| Scene | `source_chapter` | 是 | integer | 对应原文处理段序号，用于对照页定位原文 |
| Scene | `summary` | 否 | string | 场景摘要 |
| Scene | `beats` | 是 | array | 节拍列表，至少 1 个 |
| Beat | `type` | 是 | string | 只能是 `dialogue`、`action`、`direction` |
| Beat | `character` | 否 | string | 说话人。通常只用于对白节拍 |
| Beat | `content` | 是 | string | 节拍正文 |
| Beat | `parenthetical` | 否 | string | 括号提示，如语气、动作提示 |

当前后端 JSON Schema 和前端 zod 校验都使用上述字段。实现没有把额外字段作为稳定扩展点；如果要新增字段，应先更新本文档，再改后端和前端校验。

## 中文显示映射

对照页编辑区支持中文字段名。前端在校验、场景列表解析、场景跳转前会转换回内部字段。

| 中文显示 | 内部字段 |
|----------|----------|
| `标题` | `title` |
| `角色表` | `characters` |
| `姓名` | `name` |
| `身份` | `role` |
| `说明` | `description` |
| `幕` | `acts` |
| `编号` | `number` |
| `场` | `scenes` |
| `来源章节` | `source_chapter` |
| `摘要` | `summary` |
| `节拍` | `beats` |
| `类型` | `type` |
| `人物` | `character` |
| `内容` | `content` |
| `括号提示` | `parenthetical` |

节拍类型也支持中文显示：

| 中文显示 | 内部值 | 用途 |
|----------|--------|------|
| `对白` | `dialogue` | 人物说出的台词 |
| `动作` | `action` | 可拍摄的动作、事件、画面 |
| `舞台指示` | `direction` | 场面说明、转场、人工处理提示 |

注意：后端接口返回的是内部字段；对照页下载的是当前编辑区文本，因此会保留作者看到的字段形式。颜色标记不会写入下载文件。

## 编号与来源

- `Act.number` 从 1 开始。
- `Scene.number` 是全剧连续编号，不是每章内编号。最终结果和 partial 草稿都会重新归一化为 `1..N`。
- `Scene.source_chapter` 指向后端拆分后的原文处理段序号。它用于对照页找到左侧原文，不等同于 `Scene.number`。
- `Beat` 当前没有单独编号；顺序由数组顺序表达。

## 生成与校验

后端生成流程以“章节 -> 场 -> 全剧”为边界：

1. 输入文本或 EPUB 被拆成原文处理段。
2. 后端从全文提取来源证据角色表。
3. 每个处理段生成一个 `Scene`。
4. 所有 `Scene` 按全剧顺序重新编号。
5. 后端组装 `Act`，生成完整 Script YAML。
6. 后端用 JSON Schema 校验，前端编辑时用 zod 校验。

真实模型 provider 只被要求输出单场 JSON，不直接输出完整剧本 wrapper。这样模型输出失败时可以按章节隔离问题，后端也能统一做字段归一化和最终校验。

## 三幕规则

最终完成的剧本使用以下幕结构：

- 少于 3 个 Scene：单幕，标题为 `第一幕：全篇`。
- `placeholder`：3 个及以上 Scene 使用确定性三幕拆分。
- 真实模型 provider：在所有 Scene 生成后，额外读取场景序号、来源章节、标题、摘要和节拍概览，建议开端、展开、收束三个连续范围。
- 后端只接受有序、连续、非空、完整覆盖所有 Scene 的三幕边界。
- 模型建议无效、不可用或缺失时，回退确定性三幕拆分。

三幕边界只决定 Scene 属于哪一幕，不改写 Scene、Beat、角色表或来源章节。

## Partial 草稿

长文仍在处理时，每完成一个处理段，后端会保存一次可查看草稿。partial 草稿仍是合法 Script YAML，但只使用单幕：

```yaml
title: 任务名
characters: []
acts:
  - number: 1
    title: 已处理部分
    scenes:
      - number: 1
        title: 已处理场景
        source_chapter: 1
        beats:
          - type: action
            content: 已生成内容
```

这样用户可以提前进入对照页，同时避免后续新增场景导致已处理内容在“展开”和“收束”之间来回移动。最终三幕只在任务完成后应用。

## 人工处理场景

真实模型单章转换会按 `LLM_SCENE_MAX_ATTEMPTS` 重试。重试后仍无法得到合法 Scene 时，后端生成一个 schema-valid 的人工处理场景：

- `title` 追加 `（需人工处理）`。
- `source_chapter` 保持原文处理段序号。
- `summary` 说明该段需要人工处理。
- 第一个 beat 使用 `type: direction`，提示作者参考左侧原文重写。
- 可追加一个 `action` beat 放原文摘录。

认证失败、API key 缺失、provider 配置错误不会生成占位场；这些属于服务配置问题，任务会失败并提示修正配置。

## 审阅状态不进 Schema

以下信息只保存在当前浏览器本地，不属于剧本 YAML：

- 阅读模式：浅色 / 深色护眼、阅读密度。
- 场景标记：未标记 / 待处理 / 已确认。
- 文本颜色标记：红、橙、黄、绿、蓝。

这些信息不会进入后端结果，不参与后端 schema 校验，也不会作为可移植剧本数据保存。颜色标记基于文本位置和选中文本恢复；如果剧本文本变化过大，前端会丢弃无法对齐的旧标记。
