# Literpod Skill

把英文 PDF 文档变成中文双人对谈播客音频的 AI Skill。

一份 Markdown 指令 + 两个 Python 脚本,让支持 Skill 能力的大模型(Claude Code、Claude.ai 高级版等)能端到端完成"**英文 PDF → 中文播客 WAV**"的完整流程。

## 它做什么

1. **提取** —— 从英文 PDF 提取文本(支持文本层 PDF,不含 OCR)
2. **改写** —— 把英文文本改写成中文双人对谈脚本(不是翻译,是重新创作)
3. **合成** —— 用 Gemini 2.5 Flash TTS 一次调用合成双人音频,输出 WAV

## 快速开始

### 前提

- Python 3.10+
- 一个 Google Gemini API Key(免费申请:https://aistudio.google.com/apikey)
- 一个能加载 Skill 且能执行 Python 的环境(Claude Code、Claude.ai 带代码执行能力的版本)

### 安装依赖

```bash
pip install pypdf google-genai
```

### 加载 Skill

把整个 `literpod/` 目录放到你的 Skill 加载路径下(具体路径看你用的客户端)。例如 Claude Code 用户可以放到 `~/.claude/skills/literpod/`。

### 使用

加载后,直接对你的 AI 说:

> "用 Literpod 把这份 PDF 做成中文播客。"

然后把 PDF 拖进对话。AI 会按 SKILL.md 的流程依次调用脚本、生成脚本、合成音频,最后把 WAV 交给你。

第一次使用时会要求你提供 Gemini API Key。

## 设计哲学

Literpod 的三步分工有意义:

- **PDF 提取** 是工程操作 → 交给脚本(确定性、快、稳)
- **脚本改写** 是判断力密集型任务 → 交给 AI 本体(人设、节奏、术语消化)
- **语音合成** 是外部 API 调用 → 交给 Gemini 2.5 Flash TTS(原生双说话人,一次调用搞定)

这个分工体现了 AI Skill 设计的一个核心原则:**把能封装的封装成代码,把靠判断的交给模型,把能买的外包给 API**。

## 默认人设

- **Speaker1 / 老陈**(男声 Kore):理性引导者,把内容讲清楚
- **Speaker2 / 小鹿**(女声 Puck):共情追问者,代表普通听众

两人是平等合作关系,不是老师和学生。详细人设规则和写作原则见 [SKILL.md](./SKILL.md)。

## 已知限制(v1)

- 不支持扫描件 PDF(没有 OCR)
- 不支持中文 PDF(专做英文 → 中文方向)
- 音频时长固定在 3-6 分钟范围(单次 TTS 调用的稳定上限)
- 只出 WAV,不出字幕、封面、或 mp3
- 不支持自定义人设预设(需要手工改 SKILL.md)

这些限制都是 v1 的刻意克制,后续版本会逐步放开。

## 作者

David / 李光华
公众号 & 播客:David 的 AI 全景图

本 Skill 是配套 Vibe Coding 教学课程的实战案例,面向非技术背景的内容创作者和教育工作者。

## License

MIT
