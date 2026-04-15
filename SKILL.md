---
name: literpod
description: "Convert an English PDF document into a Chinese two-speaker podcast audio file (WAV). Use this skill whenever the user wants to turn an English article, paper, or PDF into a Chinese audio dialogue for listening/commuting, mentions 文档转播客, 英文 PDF 转中文播客, literpod, 生成播客, audio overview, or uploads an English PDF and asks for a Chinese audio version. Handles the full pipeline end-to-end — PDF text extraction, English-to-Chinese two-person dialogue script rewriting, and multi-speaker TTS synthesis via Gemini 2.5 Flash."
---

# Literpod · English PDF → Chinese Podcast

Literpod 把一篇英文 PDF 文档变成一段中文双人对谈播客音频。整个流程分三步,你(Claude)作为编排者,依次调用脚本、生成脚本内容、合成音频。

**最终交付物**:一个可播放的 WAV 文件。只此一件,别的都是中间产物。

---

## 何时触发这个 skill

用户做出以下任意行为时,立即使用本 skill:
- 上传一个英文 PDF 并说"帮我做成中文播客" / "转成播客" / "生成音频" / "做个 audio overview"
- 提到 "Literpod" 这个名字
- 描述场景:"想在通勤时听完这篇英文论文" / "把这个英文文章变成中文对话"
- 直接说"用 Literpod 处理这个文件"

**不要触发**的情况:
- 用户只是想要翻译(没有音频需求)→ 直接翻译即可
- 用户上传的是中文 PDF → 告诉用户本 skill 专门处理英文转中文
- 用户想要单人朗读而不是对谈 → 告诉用户本 skill 是双人对谈,询问是否仍要继续

---

## 运行前提

这个 skill 需要三样东西:
1. **Python 3.10+** 和两个库:`pypdf` 和 `google-genai`。缺失时运行:
   ```bash
   pip install pypdf google-genai --break-system-packages
   ```
2. **代码执行环境**。这个 skill 会调用外部 API,必须在能跑 Python 的环境里(Claude Code、Claude.ai 带代码执行的高级版本)。纯对话环境(EasyClaw 等)无法完成音频合成这一步。
3. **Gemini API Key**。由用户提供。第一次运行时**必须主动向用户索要**。

---

## 三步工作流

### 第 1 步 · 提取 PDF 文本

调用 `scripts/extract_pdf.py`:

```bash
python scripts/extract_pdf.py <pdf_path> --output /tmp/literpod_text.txt
```

这个脚本会自动处理:
- 提取所有页面的文本层
- 检测扫描件并报错(Literpod v1 不支持 OCR)
- 默认截断到 30000 字符(约 5000 个英文词),避免 TTS 超长

如果脚本返回错误码 2,说明是扫描件,**立即停下**,告诉用户:
> "这份 PDF 看起来是扫描图片,没有文本层。Literpod 第一版不支持 OCR。请先用其他工具做文字识别后再试。"

### 第 2 步 · 改写为中文对谈脚本

拿到英文原文后,**由你(Claude)直接改写**为中文双人对谈脚本。不要调用外部 API,这一步就是你的核心能力。

按下面的规则写。**输出格式非常重要**,因为 Gemini TTS 依赖 `Speaker1:` / `Speaker2:` 标签来分配音色。

#### 角色设定

- **Speaker1** = 男主持人 "老陈":理性引导者,懂行,负责把内容讲清楚。语气平稳、逻辑清晰,偶尔自嘲。台词特征:"其实这事儿没那么玄" / "你可以把它想成……" / "这里有个关键点"。
- **Speaker2** = 女主持人 "小鹿":共情追问者,代表普通听众。好奇、反应快,会在听众困惑的地方主动喊停。台词特征:"哎我插一句" / "所以你的意思是……" / "普通人听到这儿可能想问"。

两人是平等的合作关系,不是老师和学生。

#### 写作原则

1. **听感优先于忠实度**。这不是翻译,是改写。原文里一句话有三层意思,对普通听众没用的那层直接省略。
2. **零翻译腔**。不要"这项研究表明 X 与 Y 之间存在显著的正相关关系",要"这个研究其实说的是,X 越多 Y 也越多,而且不是巧合"。警惕:滥用"的"、长定语、被动语态、"们"字复数、"进行"+动词。
3. **从生活切入**。永远不要用"今天我们来聊一篇论文"开场。用一个生活场景、反直觉的事实、或听众可能正在经历的困惑切入。
4. **术语由小鹿喊停、老陈解释**。遇到专业术语,不能直接用。
5. **人名地名第一次出现时加中文解释**("MIT,就是麻省理工")。
6. **数字转换成听众能感知的参照系**("相当于……" / "差不多是……的 3 倍")。
7. **每 3-4 轮要有一次小鹿帮听众回顾**,防止走神。

#### 结构

- **钩子**(1-2 轮):生活场景切入
- **背景**(2-3 轮):原文来源、作者、为什么值得聊
- **主体**(8-12 轮):按"论点→追问→解释→举例→小结"节奏推进核心论点
- **收尾**(1-2 轮):对普通人的启发,留一个开放思考

总时长目标:对应 **3-6 分钟**音频(约 700-1500 中文字)。**不要超过 1500 字**,Gemini TTS 单次调用对超长输入会失败或质量下降。如果原文信息量大,只讲最值得讲的 2-3 个点。

#### 输出格式(给 TTS 用的严格格式)

**必须**使用这个格式,每行一个发言,`Speaker1:` 和 `Speaker2:` 顶格,后面是中文冒号+台词:

```
Speaker1: 你有没有过这种感觉,读了一篇英文文章,合上电脑十分钟后,啥也没记住?
Speaker2: 天天有啊,我还以为是我脑子不行。
Speaker1: 其实不是你的问题。今天聊的这篇,就是讲这件事背后的原理。
Speaker2: 等等,先告诉我这是谁写的?
Speaker1: 作者是 K. Anders Ericsson,佛罗里达州立大学的心理学家,研究人怎么变厉害这件事研究了一辈子。
```

**严禁**:
- 不要用"老陈:" / "小鹿:" ——TTS 认不出来
- 不要加 markdown 标题、列表符号、emoji
- 不要输出"以下是脚本"之类的引导语,直接开始对话
- 不要在脚本里夹杂英文原句(专有名词除外)

把写好的脚本保存到 `/tmp/literpod_script.txt`,准备进入第 3 步。

### 第 3 步 · 合成音频

调用 `scripts/generate_audio.py`:

```bash
python scripts/generate_audio.py \
    --script-file /tmp/literpod_script.txt \
    --output <user_specified_path_or_outputs_dir>/literpod_<name>.wav \
    --api-key <USER_PROVIDED_KEY>
```

**API Key 的处理**(这是关键):

第一次运行这个 skill 时,**你必须主动询问用户 API key**,用这样的话术:

> "Literpod 需要一个 Google Gemini API Key 来合成音频。如果你还没有,可以免费申请一个:
> 1. 打开 https://aistudio.google.com/apikey
> 2. 用 Google 账号登录,点 "Create API key"
> 3. 把 key 粘贴给我(形如 AIza... 开头的字符串)
> 
> Key 只用于这次合成,不会被保存。"

拿到 key 后,把它作为 `--api-key` 参数传给脚本。**不要**把 key 写进文件、不要在响应里复述这个 key、不要放进环境变量让它被日志记录。

**如果合成失败**:脚本的 stderr 会给出清晰原因(无效 key / 额度用尽 / 脚本太长 / 网络问题)。直接把原因转达给用户并建议下一步——比如额度问题就建议明天再试或升级账户,脚本太长就建议缩减。

### 第 4 步 · 交付

音频生成成功后,用 `present_files` 工具把 WAV 交给用户。不要长篇大论解释做了什么——用户想要的是一个能点开的播放器。简短说明即可:

> "播客音频已经生成,时长约 X 分钟。点开就能听。"

如果用户问"脚本长什么样",那时再给他们看脚本内容。**默认不要主动展示完整脚本**,那不是交付物。

---

## 边界情况处理

| 情况 | 处理方式 |
|---|---|
| PDF 是扫描件 | 第 1 步脚本会报错,转达给用户,停止 |
| PDF 是中文的 | 不调用 skill,告诉用户本 skill 专做英文转中文 |
| 原文少于 500 英文词 | 提示"内容偏短,生成的播客会比较简短",用户确认后继续 |
| 原文超过 30000 字符 | 脚本自动截断,在给用户的最终消息里说明"原文较长,我基于前半部分改写,重点讲了 X、Y、Z" |
| 涉及医疗/法律/投资建议 | 可以改写,但在脚本开头由老陈加一句"这是内容介绍,不构成专业建议哈" |
| 用户想要不同人设 | 询问目标人设(年龄/风格/行业),保留双人对话结构,其他规则不变 |
| 用户想要单人朗读 | 本 skill v1 不支持,告诉用户可以直接用 Gemini TTS 单说话人模式 |
| TTS 返回的音频质量差 | 检查脚本格式是否用了 `Speaker1:` / `Speaker2:`,重试一次;仍差则告诉用户并建议手工调整脚本后重跑第 3 步 |

---

## 为什么这样设计(给接手这份 skill 的人看)

1. **PDF 提取单独成脚本**:因为它是确定性的工程操作,写成脚本比每次让 LLM 做更快更稳。
2. **脚本改写交给 Claude 本体**:因为这是判断力密集型任务——人设、节奏、术语消化,这些靠规则约束 + LLM 发挥,效果远好于第三方 API。
3. **TTS 用 Gemini 2.5 Flash 而不是其他**:因为它是目前市面上少数支持"一次 API 调用生成双人对话"的模型,原生多说话人、不用拼接、24kHz 质量够听。模型名是 `gemini-2.5-flash-preview-tts`。
4. **API Key 运行时索要而不是预配**:出于隐私和成本控制——用户的 key 用户自己管,skill 不做代理,课堂上学员也能各用各的额度。
5. **输出只要 WAV**:v1 原则。后续版本可以加字幕、加封面、加 mp3 转换,但第一版刻意克制,确保"能跑通"比"功能多"更重要。

---

## 版本

- **v1.0**(2026-04):基础版。英文 PDF → 中文双人 WAV。固定人设、固定音色、单次调用。
