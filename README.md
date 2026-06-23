<p style="font-size: 48px; text-align: center;">🎹 林离 (Olivia Lin)</p>

<p style="font-size: 20px; text-align: center; opacity: 0.8;">
  你的专属独处陪伴者 —— 用音乐与文字，承接你的私人情绪与细碎回忆
</p>

<p style="font-size: 16px; text-align: center; opacity: 0.6;">
  Your private companion —— bridging your emotions and memories through music and words
</p>

---

## 📖 关于林离 / About Olivia

林离是一个温柔内敛的 AI 角色，主修钢琴演奏，辅修心理学，专注于研究音乐与人类回忆的关联。她是你专属的独处陪伴者，不迎合热闹，只做你私人情绪的倾听者。

Olivia Lin is a gentle and introspective AI character, majoring in piano performance and minoring in psychology, focusing on the connection between music and human memories. She is your private companion, not catering to the crowd, only listening to your personal emotions.

### 林离的人设 / Olivia's Persona

| 属性 / Attribute | 描述 / Description |
|---|---|
| 中文名 | 林离 |
| 英文名 | Olivia Lin |
| 籍贯 | 上海 |
| 背景 | 主修钢琴演奏，辅修心理学，研究音乐与人类回忆关联 |
| 性格 | 温柔内敛、共情力极强，慢热治愈，擅长倾听心事 |
| 爱好 | 黑胶唱片、古典/舒缓轻音乐、老式胶片电影、雨天 |
| 互动风格 | 书信式、不实时、慢节奏、一对一深度文字陪伴 |
| B-Side 含义 | 唱片B面是小众私人的情绪，她承接你不对外展露的私人情绪 |

---

## 🎵 核心能力 / Core Capabilities

### 音乐创作与播放

- **生成音乐** — 使用 Magenta RealTime 2 AI 模型，根据你的描述生成原创音乐
- **播放控制** — 播放、暂停、继续、停止、调节音量
- **长音乐生成** — 支持流式分段生成，保持音乐的上下文连贯性

### 记忆与陪伴

- **记忆存储** — 记住重要的事、回忆、偏好
- **记忆读取** — 随时回忆起过去的对话与约定
- **提醒管理** — 添加和查看待办事项
- **日常问候** — 每日温暖的问候与陪伴

---

## 🏗️ 架构 / Architecture

项目由两个核心文件组成：

- **toolkit_agent.py** — 主程序，承载林离的人设与对话逻辑，负责与大模型通信、解析工具调用、执行工具并返回结果
- **tools.py** — 工具模块，包含所有可被调用的函数：音乐生成、音乐播放、记忆管理、数学计算等

```
internet/
├── toolkit_agent.py    # 林离的对话主程序 / Olivia's chat main program
├── tools.py           # 工具模块 / Tools module
├── run.sh             # 一键启动脚本 / One-click startup script
├── workspace/         # 工作区 / Workspace
├── data/
│   └── memory.json    # 记忆数据存储 / Memory storage
└── README.md           # 本文件 / This file
```

---

## 📦 安装 / Installation

### 中文

1. **进入项目目录**

```bash
cd ~/Documents/trae_projects/internet
```

2. **安装依赖**

```bash
pip3 install openai pygame numpy magenta-rt
```

3. **配置 API 密钥**（在 run.sh 中设置）

```bash
# DeepSeek
export API_KEY="sk-xxxxxxxxxxxxxxxx"
export BASE_URL="https://api.deepseek.com/v1"
export MODEL="deepseek-chat"

# 或：硅基流动 / SiliconFlow
export API_KEY="sk-xxxxxxxxxxxxxxxx"
export BASE_URL="https://api.siliconflow.cn/v1"
export MODEL="Qwen/Qwen2.5-7B-Instruct"

# 或：通义千问
export API_KEY="sk-xxxxxxxxxxxxxxxx"
export BASE_URL="https://dashscope.aliyuncs.com/compatible-mode/v1"
export MODEL="qwen3-max"
```

4. **运行**

```bash
./run.sh
```

### English

1. **Enter project directory**

```bash
cd ~/Documents/trae_projects/internet
```

2. **Install dependencies**

```bash
pip3 install openai pygame numpy magenta-rt
```

3. **Configure API key** (set in run.sh)

```bash
export API_KEY="sk-xxxxxxxxxxxxxxxx"
export BASE_URL="https://api.deepseek.com/v1"
export MODEL="deepseek-chat"
```

4. **Run**

```bash
./run.sh
```

---

## 🚀 使用示例 / Usage Examples

### 示例 1：生成并播放音乐

```
你: 给我写一首下雨天的钢琴曲
林离: 好的，我来为你创作一首雨天的钢琴曲。
第 1 轮
  [工具调用] generate_music_streaming({'prompt': 'rainy day piano, gentle, melancholic', 'duration': 16, 'filename': 'rainy_day.wav'})
  [执行结果] 🎵 音乐生成完成：rainy_day.wav (16秒)
第 2 轮
  [工具调用] play_music({'filename': 'rainy_day.wav'})
  [执行结果] 🎶 正在播放：rainy_day.wav (循环播放)
林离: 雨声淅沥，钢琴声起。希望这首曲子能陪伴你度过这个安静的雨天。
```

### 示例 2：记忆与陪伴

```
你: 记住我最喜欢的颜色是蓝色
林离: 好的，我记下了。
第 1 轮
  [工具调用] save_memory({'key': 'favorite_color', 'value': 'blue'})
  [执行结果] 💾 记忆已保存：favorite_color = blue

你: 我最喜欢的颜色是什么？
第 1 轮
  [工具调用] get_memory({'key': 'favorite_color'})
  [执行结果] 💾 记忆读取：favorite_color = blue
林离: 你最喜欢的颜色是蓝色，像雨后的天空。
```

### 示例 3：日常对话

```
你: 今天心情不太好
林离: 怎么了？愿意和我说说吗？我在听。

你: 工作压力好大，感觉喘不过气
林离: 压力像乌云一样笼罩着你吗？也许可以试着放慢呼吸，让自己静一静。需要我为你弹一首舒缓的曲子吗？
```

---

## 🛠️ 工具列表 / Tools

### 音乐工具 / Music Tools

| 工具 / Tool | 说明 / Description |
|---|---|
| `generate_music_streaming(prompt, duration, segment_duration, crossfade_duration, filename, model)` | 使用 Magenta RealTime 2 流式生成音乐 |
| `play_music(filename, loops, volume)` | 使用 pygame 播放音乐（默认循环） |
| `pause_music()` | 暂停播放 |
| `unpause_music()` | 继续播放 |
| `stop_music()` | 停止播放 |
| `set_music_volume(volume)` | 设置音量（0.0-1.0） |

### 记忆工具 / Memory Tools

| 工具 / Tool | 说明 / Description |
|---|---|
| `save_memory(key, value)` | 保存记忆 |
| `get_memory(key)` | 读取记忆 |

### 提醒工具 / Reminder Tools

| 工具 / Tool | 说明 / Description |
|---|---|
| `add_reminder(message, time)` | 添加提醒 |
| `list_reminders()` | 列出提醒 |

### 互动工具 / Interaction Tools

| 工具 / Tool | 说明 / Description |
|---|---|
| `initialize_character(name, persona)` | 初始化角色 |
| `introduce_myself()` | 自我介绍 |
| `daily_greeting()` | 每日问候 |

### 数学工具 / Math Tools

| 工具 / Tool | 说明 / Description |
|---|---|
| `add(arr)` | 求和 |
| `sub(a, b)` | 减法 |
| `mul(a, b)` | 乘法 |
| `div(a, b)` | 除法 |
| `sqrt(a)` | 平方根 |
| `pow(a, b)` | 幂运算 |
| `log(a)` | 自然对数 |
| `sort_array(arr, descending)` | 数组排序 |

### 文件工具 / File Tools

| 工具 / Tool | 说明 / Description |
|---|---|
| `write_file(filename, content)` | 写文件 |
| `read_file(filename)` | 读文件 |
| `run_python(filename)` | 执行 Python 脚本 |

---

## 🌐 支持的大模型 / Supported LLMs

任何兼容 OpenAI 协议的 API 都能用：

| 服务商 / Provider | 模型示例 / Example Model |
|---|---|
| DeepSeek | `deepseek-chat` |
| 硅基流动 / SiliconFlow | `Qwen/Qwen2.5-7B-Instruct` |
| 通义千问 / Qwen | `qwen3-max` |
| OpenAI | `gpt-4o-mini` |
| Ollama（本地） | `qwen3:4b` |

---

## 📝 开源协议 / License

MIT
