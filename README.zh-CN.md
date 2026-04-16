# prompt-language-coach

> [English](README.md) | 中文

> 面向 AI 编辑器的常驻语言教练 —— 在 Codex、Claude Code 和 Cursor 中，一边工作一边提升任何目标语言。

[![Codex Plugin](https://img.shields.io/badge/Codex-Plugin-green)](https://github.com/leeguooooo/prompt-language-coach)
[![Claude Code Plugin](https://img.shields.io/badge/Claude%20Code-Plugin-blue)](https://github.com/leeguooooo/prompt-language-coach)
[![Cursor Plugin](https://img.shields.io/badge/Cursor-Plugin-black)](https://github.com/leeguooooo/prompt-language-coach)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---
<img width="1662" height="894" alt="image" src="https://github.com/user-attachments/assets/8c64bc95-706c-43c8-a3c3-f67b52b82213" />

## 它能做什么

Prompt Language Coach 原生支持 **Codex**、**Claude Code** 和 **Cursor**。

你发送的每一条消息，都会在真实模型回答之前先接受辅导：

- 用目标语言写作？→ 获得语法纠错 + 地道的母语表达
- 用母语写作？→ 获得一个简洁自然的目标语言版本
- 中英混写？→ 获得完整意思的自然表达版本

辅导核心支持以下模式：

- `everyday`
- `scored-writing`
- `scored-speaking`
- `review`

支持**任意语言对**：中文 → 英语、日语 → 英语、西班牙语 → 法语，等等。

它的核心卖点：

- **常驻辅导** —— 每条 prompt 都自动变成一次语言训练
- **任意语言对** —— 不局限于英语学习
- **需要时可切到 IELTS 深度模式** —— 从轻量纠错升级到考试导向训练

| 平台 | 原生接入方式 | 状态 |
| --- | --- | --- |
| Codex | `.codex-plugin` + `UserPromptSubmit` hook | 一等公民 |
| Claude Code | `.claude-plugin` + `UserPromptSubmit` hook | 一等公民 |
| Cursor | `.cursor-plugin` / 规则式会话注入 | 一等公民 |

---

## 演示

你发送的每条消息都会在助手回答**之前**接受辅导。辅导内容显示在一个独立的视觉框中，与实际回答清晰分隔。

**日常模式（everyday）** —— 你写道：
> "I want to know how can i to fix this bug in my code"

**助手先辅导，再回答：**
```
╭─ 📚 English Coaching ─────────────────────
│ 原文：   "I want to know how can i to fix this bug"
│ 纠正：   "I want to know how I can fix this bug"
│ 更自然： "How do I fix this bug?" / "Can you help me debug this?"
│ 关键点： modal verb + bare infinitive — "can fix", not "can to fix"
╰────────────────────────────────────────────

(Claude 的实际回答在这里)
```

**评分写作模式（scored-writing）** —— 你写道：
> "The environment is very important and we should protect it because many reason."

**助手辅导：**
```
╭─ 📚 English · Scored Writing ─────────────
│ Band 估分：  5.0–5.5
│ 亮点：       主题明确，有因果逻辑意识
│ 扣分项：     "many reason" → "many reasons"；论点空洞，缺乏具体论据
│ 高分改写：   "Environmental protection is critical, as unchecked
│              pollution threatens biodiversity and public health."
│ 可复用句式： "[Topic] is critical, as [specific consequence]."
│ 练习：       用上面句式写一句关于 education 的句子
╰────────────────────────────────────────────

(Claude 的实际回答在这里)
```

---

## 安装

### Codex

**前置条件：** `python3`

先把本仓库添加为 Codex 的 marketplace 源：

```bash
codex marketplace add leeguooooo/prompt-language-coach
```

然后：

1. 重启 Codex
2. 打开插件目录并安装 **Prompt Language Coach**
3. 运行 `/language-coach setup`

设置流程会写入 `~/.codex/language-coach.json`，并自动安装 Codex 的 `UserPromptSubmit` hook。

### Claude Code

**前置条件：** `python3`

```
/plugin marketplace add leeguooooo/plugins
/plugin install language-coach@leeguooooo-plugins
/reload-plugins
/language-coach:language-coach setup
```

### Cursor

**前置条件：** `python3`

通过 Cursor 插件市场安装，或直接添加插件库：

1. 打开 **Cursor Settings → Plugins → Marketplace**
2. 添加插件库：`leeguooooo/plugins`
3. 安装 **language-coach**

然后在 Cursor 的 AI 面板中运行设置命令：

```
/language-coach setup
```

设置向导会逐一询问你的母语、目标语言、学习目标、辅导风格和回复语言，与 Claude Code 一致。配置存储于 `~/.cursor/language-coach.json`。

---

## 设置与使用

### Codex 设置

运行 `/language-coach setup` 并完成引导问题。

在 Codex 中，setup 结束后还会自动安装 `UserPromptSubmit` hook，因此从下一条提示开始就会进入常驻辅导。Codex 配置文件存储于 `~/.codex/language-coach.json`。

### Claude Code 设置

运行 `/language-coach:language-coach setup`，按照引导回答以下问题：

1. 你的母语是什么？
2. 你在学习哪种语言？
3. 你的主要目标是什么？（`everyday` / `scored`）
4. 选择辅导风格？（`teaching` / `concise` / `translate`）
5. 辅导结束后用什么语言回复？（`native` / `target`）

如果你选择 `scored`，设置流程还会额外存储：

1. 当前评分模式：`scored-writing` 或 `scored-speaking`
2. 评分重点：`writing`、`speaking` 或 `both`
3. 目标估计值
4. 当前水平

设置完成后，Claude 辅导会在每条提示上自动激活。

---

## 命令列表

在 **Codex** 和 **Cursor** 中，使用 `/language-coach ...`。

在 **Claude Code** 中，使用 `/language-coach:language-coach ...`。

| 命令 | 说明 |
|---|---|
| `/language-coach setup` | 一次性交互式设置向导 |
| `/language-coach native <lang>` | 修改你的母语 |
| `/language-coach target <lang>` | 修改你正在学习的语言 |
| `/language-coach style <mode>` | 切换辅导风格：`teaching`、`concise`、`translate` |
| `/language-coach response <mode>` | 切换回复语言：`native` 或 `target` |
| `/language-coach goal <mode>` | 切换学习目标：`everyday` 或 `scored` |
| `/language-coach mode <mode>` | 切换辅导模式：`everyday`、`scored-writing`、`scored-speaking` 或 `review` |
| `/language-coach practice-focus <mode>` | 设置评分重点：`writing`、`speaking` 或 `both` |
| `/language-coach focus <mode>` | `practice-focus` 的旧别名 |
| `/language-coach estimate <value>` | 存储你的目标估计值 |
| `/language-coach band <score>` | `estimate` 的旧别名 |
| `/language-coach level <text>` | 存储你的当前水平 |
| `/language-coach status` | 显示当前配置 |
| `/language-coach off` | 暂停辅导（配置保留） |
| `/language-coach on` | 恢复辅导 |
| `/language-coach progress` | 显示所有语言的估计历史 |
| `/language-coach progress <lang>` | 显示指定语言的估计历史 |

---

## 模式说明

| 模式 | 你会得到什么 |
|---|---|
| `everyday` | 简洁辅导，包含原文、纠正版、更自然的表达，以及一条关键要点 |
| `scored-writing` | 面向评分提升的写作反馈，自动使用目标语言最合适的量表，包含估计、问题、改写、可复用句式及练习 |
| `scored-speaking` | 面向评分提升的口语自然度反馈，涵盖流利度、词汇、语法、句式及练习指导 |
| `review` | 简洁的复习总结，涵盖反复出现的错误、可复用句式及下一步练习 |

## 进度追踪

以下情况同时满足时，评分估计会自动记录到共享 progress 文件（`~/.prompt-language-coach/language-progress.json`），并同步到旧的平台文件：

1. 当前模式为 `scored-writing` 或 `scored-speaking`
2. 用户使用目标语言书写（非纯母语输入）
3. Claude 在辅导框中给出了对应量表的估计值

记录永久保存，不会自动删除。使用 `/language-coach:language-coach progress` 查看历史：

```
English progress (last 5 sessions):
  2026-04-13  5.5
  2026-04-14  5.5
  2026-04-15  6.0
Current estimate: 6.0
```

如果你也使用 [Claude Status Bar](https://github.com/leeguooooo/claude-code-usage-bar)，当前估计值和趋势会自动显示在状态栏（`📚 EN:6.0↑`），宠物也会根据学习状态做出反应。

---

## 辅导风格

| 风格 | 变化内容 |
|---|---|
| `teaching` | 带解释的辅导，包含原因分析和提升建议 |
| `concise` | 简短的纠错为主的辅导 |
| `translate` | 以目标语言为主，解释最少 |

---

## 配置说明

配置存储于当前平台对应的配置文件中：

- Codex：`~/.codex/language-coach.json`
- Claude Code：`~/.claude/language-coach.json`
- Cursor：`~/.cursor/language-coach.json`

标准化 JSON 结构如下：

```json
{
  "nativeLanguage": "Chinese",
  "targetLanguage": "English",
  "goal": "scored",
  "mode": "scored-writing",
  "style": "teaching",
  "responseLanguage": "target",
  "enabled": true,
  "scoringFocus": "writing",
  "targetEstimate": "7.0",
  "currentLevel": "6.0",
  "version": 1
}
```

| 字段 | 可选值 | 默认值 | 说明 |
|---|---|---|---|
| `nativeLanguage` | 任意语言名称 | `"Chinese"` | 你的母语 |
| `targetLanguage` | 任意语言名称 | `"English"` | 你正在学习的语言 |
| `goal` | `everyday` / `scored` | `"everyday"` | 顶层学习目标 |
| `mode` | `everyday` / `scored-writing` / `scored-speaking` / `review` | `"everyday"` | 当前激活的辅导模式 |
| `style` | `teaching` / `concise` / `translate` | `"teaching"` | 输出详细程度 |
| `responseLanguage` | `native` / `target` | `"native"` | 辅导后使用的回复语言 |
| `enabled` | `true` / `false` | `true` | 开关辅导，不丢失配置 |
| `scoringFocus` | `writing` / `speaking` / `both` | `"both"` | 存储的评分模式侧重点 |
| `targetEstimate` | 自由文本 | `""` | 当前语言量表上的目标估计值 |
| `currentLevel` | 自由文本 | `""` | 当前估计水平 |
| `version` | 整数 | `1` | 配置结构版本号 |

旧版 `native` / `target` 字段在加载时会自动规范化为当前结构。

---

## 工作原理

Codex、Claude Code 和 Cursor 都通过共享 Python 核心渲染辅导上下文：

1. `shared/config/` 加载并规范化平台配置
2. `shared/pedagogy/modes.py` 根据当前模式选择反馈格式
3. `shared/prompts/build_prompt.py` 构建辅导指令文本
4. `scripts/render_coaching_context.py` 生成钩子 JSON 载荷

**Codex** 使用 `.codex-plugin/plugin.json` 配合 `platforms/codex/hook_entry.py` —— 通过 Codex 的 `UserPromptSubmit` hook 在每条提示前注入辅导。

**Claude Code** 使用 `UserPromptSubmit` 钩子（`hooks/language-coach.sh`）——每条提示均触发辅导，通过 `hookSpecificOutput.additionalContext` 注入。

**Cursor** 使用 `sessionStart` 钩子（`hooks/cursor-language-coach.sh`）——会话开始时通过 `additional_context` 注入辅导上下文。

所有接入层在以下情况下均静默退出（不辅导、不报错）：

- 未安装 `python3`
- 平台配置文件尚不存在（`~/.codex/language-coach.json`、`~/.claude/language-coach.json` 或 `~/.cursor/language-coach.json`）
- `enabled` 为 `false`

---

## 使用场景

- **ESL 学习者**，正在为英语国家（澳大利亚、英国、美国、加拿大）的就业市场做准备
- **语言学习者**，希望在不离开开发工作流的情况下进行沉浸式练习
- **远程工作者**，每天需要用第二语言进行书面沟通
- **工程师**，希望提升技术文档的英语写作质量

---

## 为什么采用这种方式？

大多数语言学习应用都是独立工具，使用时需要切换上下文。这个插件让每次编码会话都成为语言练习机会 —— 零上下文切换，零额外努力。

---

## 手动安装

### Codex

你也可以把本地 checkout 直接作为 Codex marketplace 源：

```bash
codex marketplace add .
```

然后运行：

```bash
/language-coach setup
```

重启 Codex 后，从插件目录里安装这个插件。设置流程会写入 `~/.codex/language-coach.json`，并在 `~/.codex/hooks.json` 中安装 Codex 的 `UserPromptSubmit` hook。

### Claude Code

克隆仓库后在 `~/.claude/settings.json` 中添加钩子：

```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "bash \"/path/to/prompt-language-coach/hooks/language-coach.sh\""
          }
        ]
      }
    ]
  }
}
```

然后创建 `~/.claude/language-coach.json` 并填入你的配置。

### Cursor

克隆仓库并将其放置于 `~/.cursor/plugins/local/language-coach`，Cursor 会自动识别 `.cursor-plugin/plugin.json`。钩子读取 `~/.cursor/language-coach.json` 中的配置。

在 Cursor AI 面板中运行设置：

```
/language-coach setup
```

---

## 贡献

欢迎提交 PR。如果你想新增辅导风格、改进提示词或添加新命令，请先开 issue 讨论。

---

## 作者

由 [leeguooooo](https://github.com/leeguooooo) 构建 —— 一名高级前端工程师，正在为澳大利亚就业市场做准备，每天都在使用这个插件。

---

## 完整使用示例

下面的示例使用 Claude Code 的命令界面，但辅导模型和配置概念在 Codex 与 Cursor 上是一致的。

一个完整示例：中国高中生同时学习英语和日语，使用评分模式练习（目标估计值 6.5）。

### 1. 安装并运行设置

```
/plugin marketplace add leeguooooo/plugins
/plugin install language-coach@leeguooooo-plugins
/reload-plugins
/language-coach:language-coach setup
```

向导逐一提问：

```
What is your native language?          → Chinese
What language are you learning?        → english, japanese
What is your main goal?                → scored
Which scored mode?                     → scored-writing and scored-speaking
Target estimate?                       → 6.5
Current level?                         → 高中生水平
Coaching style?                        → teaching
Response language after coaching?      → native
```

最终配置存储在 `~/.claude/language-coach.json`：

| 字段 | 值 |
|---|---|
| 母语 | Chinese |
| 目标语言 | English + Japanese（自动检测） |
| 学习目标 | scored |
| 辅导模式 | Scored Writing |
| 辅导风格 | Teaching（详细讲解） |
| 回复语言 | Chinese（母语） |
| 目标估计值 | 6.5 |
| 当前水平 | 高中生水平 |

### 2. 重新加载并开始写作

```
/reload-plugins
```

从现在起，每条消息都会自动接受辅导。辅导框出现在 Claude 实际回答**之前**，清晰分隔。

**写了一个带语法错误的英语句子：**

用户输入：`"ok, It's work well."`

```
╭─ 📚 English · Scored Writing ─────────────
│ Band 估分：  这句较短，但有语法错误
│ 亮点：       用了副词 "well" 修饰动词 ✓
│ 扣分项：     "It's work well" — it's = it is，后面不能接动词原形
│ 高分改写：   "It works well." / "It's working well."
│ 可复用句式： It + works / is working + adverb — 描述某物正常运转
│ 练习：       "The system ___ well after the update." — works 还是 is working？
╰─────────────────────────────────────────────

（Claude 的实际回答在这里，无边框）
```

**写日语**时会触发相同的结构，但使用日语专属标题：

```
╭─ 📚 Japanese · Scored Writing ────────────
│ ...
╰─────────────────────────────────────────────
```

随时切换模式：

```
/language-coach:language-coach mode everyday       # 返回日常辅导模式
/language-coach:language-coach mode scored-writing  # 返回评分写作模式
/language-coach:language-coach status              # 显示当前配置
```

---

## 相关链接

- [Claude Status Bar](https://github.com/leeguooooo/claude-code-usage-bar) — 在状态栏显示当前语言估计进度（`📚 EN:6.0↑`），与 Claude 使用量、上下文用量并排展示。读取本插件同步写入的 progress 文件。
- [Claude Code 文档](https://docs.anthropic.com/en/docs/claude-code)
- [Claude Code 钩子指南](https://docs.anthropic.com/en/docs/claude-code/hooks)
- [Claude Code 插件市场](https://docs.anthropic.com/en/docs/claude-code/plugins)
