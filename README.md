<p style="font-size: 48px; text-align: center;">🧰 toolkit-agent</p>

<p style="font-size: 20px; text-align: center; opacity: 0.8;">
  一个轻量级 Python 框架，让大模型通过调用外部工具完成任务
</p>

<p style="font-size: 16px; text-align: center; opacity: 0.6;">
  A lightweight Python framework for letting LLMs accomplish tasks via tool-calling
</p>

---

## 📖 概述 / Overview

### 中文

toolkit-agent 是一个极简的 **AI 代理框架。核心思想很简单：

1. **定义工具** — 写一个 Python 函数，附上一份 JSON schema 描述
2. **模型选工具** — 大模型根据用户问题，从工具列表中选择合适的工具
3. **本地执行** — 在你的机器上执行代码，把结果回传给模型
4. **多步推理** — 模型可以连续调用多个工具，一步步解决复杂问题

这正是 OpenAI Code Interpreter、Claude Tools 等产品的核心原理。不同的是，**工具的实现完全在你本地，不受平台限制，可以随意扩展：数学函数、文件读写、C 扩展、自定义 API 调用……

### English

toolkit-agent is a minimal **LLM agent framework**. The core idea is simple:

1. **Define tools** — Write a Python function with a JSON schema description
2. **Model chooses tools** — The LLM picks appropriate tools based on user input
3. **Local execution** — Code runs on your machine, results sent back to the model
4. **Multi-step reasoning** — The model can chain multiple tool calls to solve complex problems

This is exactly how OpenAI Code Interpreter, Claude Tools, and similar products work. The difference: **tool implementation is entirely local** — no platform lock-in, freely extensible with math functions, file I/O, C extensions, custom API calls...

---

## 🏗️ 架构 / Architecture

### 中文

项目由两个核心文件组成：

- **toolkit_agent.py** — 与大模型对话的主程序。它负责把用户问题发给模型、解析模型返回的工具调用请求、在本地执行工具、把执行结果回传给模型，然后循环这个过程直到模型给出最终回答。
- **tools.py** — 工具模块。所有可被模型调用的函数、以及它们的 JSON schema 描述，都集中定义在这里。

简单来说，`toolkit_agent.py` 负责调度，`tools.py` 负责干活。你可以随意往 `tools.py` 里加新工具（数学计算、文件读写、外部 API、甚至用 ctypes 引入 C 扩展），主程序一行都不用改。

### English

The project consists of two core files:

- **toolkit_agent.py** — The main program that chats with the LLM. It sends user questions to the model, parses tool-call requests, executes tools locally, sends results back to the model, and loops until the model produces a final answer.
- **tools.py** — The tools module. All callable functions and their JSON schema descriptions are defined here in one place.

In short, `toolkit_agent.py` handles orchestration, and `tools.py` handles the actual work. You can freely add new tools to `tools.py` (math operations, file I/O, external API calls, even C extensions via ctypes) without touching the main program.

---

## ⚙️ 核心机制 / How It Works

### 中文

一次完整的工具调用循环分为以下几步：

1. 你输入一个问题，主程序把它发送给大模型，同时附上所有工具的 JSON schema 描述。
2. 大模型读到这些描述后，判断哪些工具可以解决问题。它会返回一个结构化的工具调用请求（包含工具名和参数）。
3. 主程序从工具映射表里找到对应的 Python 函数，用模型给出的参数去调用它。
4. 函数执行后，主程序把结果回传给大模型。
5. 大模型收到结果后，可以继续选择调用下一个工具，或者直接给出最终回答。
6. 如果还需要工具就回到第 2 步继续循环；如果不需要了，就把自然语言回答返回给你。

整个过程对用户是透明的——你只管提问，其余的都由主程序自动处理。

### English

One complete tool-call cycle works as follows:

1. You type a question. The main program sends it to the LLM, along with the JSON schema descriptions of all available tools.
2. The LLM reads these descriptions and decides which tools can help solve the problem. It returns a structured tool-call request containing tool names and arguments.
3. The main program looks up the corresponding Python function from the function map, then calls it with the model's arguments.
4. After the function runs, the main program sends the result back to the LLM.
5. The LLM, now armed with the result, can either choose to call another tool, or produce a final natural-language answer.
6. If more tools are needed, the loop goes back to step 2; otherwise, the LLM returns its final answer to you.

The entire process is transparent to the user — you just ask questions, and the main program handles everything else automatically.

---

## 🛠️ 内置工具 / Built-in Tools

| 工具 / Tool | 说明 / Description |
|---|---|
| `add(a, b)` | 加法 / Addition |
| `sub(a, b)` | 减法 / Subtraction |
| `mul(a, b)` | 乘法 / Multiplication |
| `div(a, b)` | 除法 / Division |
| `sqrt(a)` | 平方根 / Square root |
| `pow(a, b)` | 幂运算 / Power |
| `log(a)` | 自然对数 / Natural logarithm |
| `sort_array(arr, descending)` | 数组排序 / Sort array |

---

## 📦 安装 / Installation

### 中文

1. **克隆项目**

```bash
git clone <your-repo-url>
cd toolkit-agent
```

2. **安装依赖**

```bash
pip3 install openai
```

3. **配置 API 密钥**（任选其一：

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
python3 toolkit_agent.py
```

### English

1. **Clone the project**

```bash
git clone <your-repo-url>
cd toolkit-agent
```

2. **Install dependencies**

```bash
pip3 install openai
```

3. **Configure API key** (choose one):

```bash
# DeepSeek
export API_KEY="sk-xxxxxxxxxxxxxxxx"
export BASE_URL="https://api.deepseek.com/v1"
export MODEL="deepseek-chat"

# or: SiliconFlow
export API_KEY="sk-xxxxxxxxxxxxxxxx"
export BASE_URL="https://api.siliconflow.cn/v1"
export MODEL="Qwen/Qwen2.5-7B-Instruct"

# or: Qwen / 通义千问
export API_KEY="sk-xxxxxxxxxxxxxxxx"
export BASE_URL="https://dashscope.aliyuncs.com/compatible-mode/v1"
export MODEL="qwen3-max"
```

4. **Run**

```bash
python3 toolkit_agent.py
```

---

## 🚀 使用示例 / Usage Examples

### 中文

```
✅ 已连接 https://api.deepseek.com/v1，使用模型: deepseek-chat
   输入 quit/exit/q 退出

你: 100加200，再把结果乘以3
第 1 轮
  [工具调用] add({'a': 100, 'b': 200})
  [执行结果] 300
第 2 轮
  [工具调用] mul({'a': 300, 'b': 3})
  [执行结果] 900
AI: 计算结果是 900。

你: 把 [5, 2, 8, 1, 9, 3] 从大到小排序
  [工具调用] sort_array({'arr': [5, 2, 8, 1, 9, 3], 'descending': True})
  [执行结果] [9, 8, 5, 3, 2, 1]
AI: 排序后的结果是 [9, 8, 5, 3, 2, 1]
```

### English

```
✅ Connected to https://api.deepseek.com/v1, using model: deepseek-chat
   Type quit/exit/q to exit

You: 100 plus 200, then multiply the result by 3
Round 1
  [Tool call] add({'a': 100, 'b': 200})
  [Result] 300
Round 2
  [Tool call] mul({'a': 300, 'b': 3})
  [Result] 900
AI: The result is 900.

You: sort [5, 2, 8, 1, 9, 3] from largest to smallest
  [Tool call] sort_array({'arr': [5, 2, 8, 1, 9, 3], 'descending': True})
  [Result] [9, 8, 5, 3, 2, 1]
AI: Sorted result is [9, 8, 5, 3, 2, 1]
```

---

## 🔧 扩展指南：添加新工具 / Adding New Tools

只需在 `tools.py` 中**改三处**：

### 中文

```python
# ① 在 TOOLS_SCHEMA 中加 schema
{
    "type": "function",
    "function": {
        "name": "factorial",
        "description": "Calculate the factorial of a number (n!)",
        "parameters": {
            "type": "object",
            "properties": {
                "n": {"type": "integer", "description": "The number to compute factorial for"}
            },
            "required": ["n"]
        }
    }
}

# ② 加函数实现
def factorial(n: int) -> int:
    """Calculate n!"""
    import math
    return math.factorial(n)

# ③ 加进映射表
FUNCTIONS = {
    ...,
    "factorial": factorial,
}
```

完事，`toolkit_agent.py` 一行都不用改。

### English

Just **three changes** in `tools.py`:

```python
# ① Add schema to TOOLS_SCHEMA
{
    "type": "function",
    "function": {
        "name": "factorial",
        "description": "Calculate the factorial of a number (n!)",
        "parameters": {
            "type": "object",
            "properties": {
                "n": {"type": "integer", "description": "The number to compute factorial for"}
            },
            "required": ["n"]
        }
    }
}

# ② Add function implementation
def factorial(n: int) -> int:
    """Calculate n!"""
    import math
    return math.factorial(n)

# ③ Add to function map
FUNCTIONS = {
    ...,
    "factorial": factorial,
}
```

That's it — no changes needed in `toolkit_agent.py`.

---

## 🌐 支持的大模型 / Supported LLMs

任何兼容 OpenAI 协议的 API 都能用 / Works with any OpenAI-compatible API:

| 服务商 / Provider | 模型示例 / Example Model | BASE_URL |
|---|---|---|
| DeepSeek | `deepseek-chat` | `https://api.deepseek.com/v1` |
| 硅基流动 / SiliconFlow | `Qwen/Qwen2.5-7B-Instruct` | `https://api.siliconflow.cn/v1` |
| 通义千问 / Qwen | `qwen3-max` | `https://dashscope.aliyuncs.com/compatible-mode/v1` |
| OpenAI | `gpt-4o-mini` | `https://api.openai.com/v1` |
| Ollama（本地 / local） | `qwen3:4b` | `http://localhost:11434/v1` |

---

## 📂 项目结构 / Project Structure

```
toolkit-agent/
├── toolkit_agent.py    # 主程序：与大模型对话 / Main: chat with LLM
├── tools.py           # 工具模块：函数 + schema / Tools module: functions + schema
└── README.md           # 本文件 / This file
```

---

## 📝 开源协议 / License

MIT