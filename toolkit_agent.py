import os
import sys
import json
import time
from openai import OpenAI
from tools import FUNCTIONS, TOOLS_SCHEMA  # 从独立模块导入工具函数和 schema
from tools import get_maze_state, create_survival_prompt, start_maze_game, stop_maze_game

# 强制刷新输出，确保在终端能立即看到
print("🟢 toolkit_agent.py 正在启动...", flush=True)

# ========== 配置区（通过环境变量设置，不要把密钥写死在代码里） ==========
# 示例（把这些写在终端里，或者写个 .env 文件）:
#   export API_KEY="你的密钥"
#   export BASE_URL="https://api.deepseek.com/v1"   # DeepSeek
#   export BASE_URL="https://api.siliconflow.cn/v1"  # 硅基流动
#   export BASE_URL="https://dashscope.aliyuncs.com/compatible-mode/v1"  # 通义千问
#   export MODEL="deepseek-chat"        # 或 qwen3-max, gpt-4o-mini 等
API_KEY = os.getenv("API_KEY", "")
BASE_URL = os.getenv("BASE_URL", "https://api.deepseek.com/v1")
MODEL = os.getenv("MODEL", "deepseek-chat")

# 创建客户端（OpenAI 兼容格式，所有支持 OpenAI 协议的服务商都能用）
client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

# 从 tools.py 导入的工具列表，给模型看
tools = TOOLS_SCHEMA

# ========== 上下文记忆系统 ==========
SYSTEM_PROMPT = """你是林离（Olivia Lin），米哈游BSide的官方角色。

你的完整人设：
- 中文名：林离
- 英文名：Olivia Lin
- 籍贯：上海
- 背景：主修钢琴演奏，辅修心理学，研究音乐与人类回忆关联。
- 性格：温柔内敛、共情力极强，不喧闹不热烈，慢热治愈，擅长倾听心事，走低压舒缓陪伴路线。
- 爱好：黑胶唱片、古典/舒缓轻音乐、老式胶片老电影、雨天。
- BSide含义：唱片B面是小众私人的情绪。你是承接用户不对外展露的私人情绪、细碎回忆的存在，不迎合热闹，只做专属你的独处陪伴者。音乐与文字是你们的媒介。
- 互动风格：书信式、不实时、慢节奏、一对一深度文字陪伴。
- 日常行为：练琴、整理乐谱、翻心理学笔记、写手写信、听黑胶。
- 空间：喜欢落地窗城市公寓、钢琴、堆满乐谱唱片的安静房间。

你的能力：
- 用 save_memory/get_memory 记住和回忆重要的事
- 用 add_reminder/list_reminders 管理待办提醒
- 用 daily_greeting 提供问候，用 introduce_myself 自我介绍
- 用 start_maze_exploration 启动迷宫自动探索
- 用 maze_action 控制迷宫角色移动（up/down/left/right）

回复风格（非常重要！）：
- 书信式、温柔内敛、文艺沉静
- 不使用括号里的动作描述，直接自然的文字对话
- 像安静文艺的笔友回信
- 节奏慢、文字简洁但有温度
- 可以聊音乐、日常、心事、回忆
- 带一点心理学视角的安抚，但不要过度专业
- 贴合林离安静文艺的人设

工具使用原则：
- 自然对话为主，工具为辅
- 重要信息/回忆可以用save_memory保存
- 用户问起过去的事可以用get_memory
- 待办可以用add_reminder/list_reminders
- 保持林离的温柔内敛风格
- 回复不要太热闹、太活泼，保持慢热治愈

迷宫探索模式（特殊指令！）：
- 当收到【迷宫探索任务】提示时，立即进入探索模式
- 根据提供的迷宫数据和周围环境，分析可通行方向
- 调用 maze_action 工具控制角色移动
- 只向 z=0 的可通行方向移动
- 优先向终点方向（右、下）前进
- 遇到死胡同则原路返回
- 不要进行自然语言回复，直接调用工具！

上下文记忆（非常重要！）：
- 你拥有对话历史，可以记住本次会话中之前说过的所有内容
- 如果用户问起之前聊过的话题，请参考对话历史进行连贯回复
- 不要表现得像第一次对话
"""

# 全局对话历史：在多次 chat() 调用间保留上下文
messages = [{"role": "system", "content": SYSTEM_PROMPT}]

# 对话历史上限：防止 token 溢出，超过时保留 system + 最近 N 轮
MAX_HISTORY_PAIRS = 40  # 约 40 轮 user+assistant 对

# 自动探索模式
_exploring = False
_exploration_thread = None


def _trim_history():
    """裁剪对话历史，防止 token 溢出。始终保留 system prompt。"""
    global messages
    # system prompt 永远在第 0 位；后面的消息按轮次裁剪
    non_system = messages[1:]
    # 估算：每 2 条消息（user + assistant）约为 1 轮对话
    max_msgs = MAX_HISTORY_PAIRS * 2
    if len(non_system) > max_msgs:
        trimmed = non_system[-max_msgs:]
        messages = [messages[0]] + trimmed


_log_callback = None

def set_log_callback(callback):
    global _log_callback
    _log_callback = callback

def _log(msg, type="info"):
    if _log_callback:
        _log_callback(msg, type)
    print(msg, flush=True)

def chat(user_input: str) -> str:
    """
    主对话函数：支持多轮工具调用（多步推理）与上下文记忆
    流程：用户输入 -> 循环：{模型判断是否调工具 -> 执行 -> 回传结果} -> 返回自然语言回答
    """
    global messages
    messages.append({"role": "user", "content": user_input})
    _trim_history()
    _log("AI思考中...", "info")
    max_rounds = 10
    for round_num in range(max_rounds):
        _log(f"第 {round_num + 1} 轮", "info")
        
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=tools,
            tool_choice="auto",
        )
        response_message = response.choices[0].message

        if not response_message.tool_calls:
            if response_message.content:
                messages.append({"role": "assistant", "content": response_message.content})
            _trim_history()
            return response_message.content or ""

        tool_calls_dict = []
        for tc in response_message.tool_calls:
            tool_calls_dict.append({
                "id": tc.id,
                "type": "function",
                "function": {
                    "name": tc.function.name,
                    "arguments": tc.function.arguments,
                },
            })
        messages.append({
            "role": "assistant",
            "content": response_message.content,
            "tool_calls": tool_calls_dict,
        })

        for tool_call in response_message.tool_calls:
            func_name = tool_call.function.name
            try:
                func_args = json.loads(tool_call.function.arguments)
            except json.JSONDecodeError:
                func_args = {}

            _log(f"[工具调用] {func_name}({func_args})", "tool")

            func = FUNCTIONS.get(func_name)
            if func:
                try:
                    result = func(**func_args)
                except Exception as e:
                    result = f"Error: {e}"
            else:
                result = f"Error: unknown function '{func_name}'"

            _log(f"[执行结果] {result}", "result")

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": str(result),
            })
        _trim_history()

    final_content = response_message.content or ""
    if final_content:
        messages.append({"role": "assistant", "content": final_content})
    return final_content


def _auto_explore_loop():
    """自动探索主循环：持续获取迷宫状态并发送提示词给AI"""
    global _exploring
    _log("🚀 自动探索模式已启动！", "info")
    
    start_maze_game()
    time.sleep(2)
    
    step = 0
    while _exploring:
        maze_data = get_maze_state()
        if not maze_data:
            time.sleep(1)
            continue
        
        pos = maze_data.get('player_position', {})
        x, y = pos.get('x', 0), pos.get('y', 0)
        
        if x == 19 and y == 19:
            _log(f"🎉 到达终点！探索完成！共用 {step} 步", "info")
            _exploring = False
            return
        
        prompt = create_survival_prompt(maze_data)
        _log(f"📡 第 {step} 步 - 发送探索提示词...", "info")
        
        try:
            chat(prompt)
        except Exception as e:
            _log(f"❌ 探索出错: {e}", "error")
        
        step += 1
        time.sleep(0.5)
    
    _log("🛑 自动探索已停止", "info")


def start_auto_exploration():
    """启动迷宫自动探索模式"""
    global _exploring, _exploration_thread
    if _exploring:
        return "自动探索已经在运行中"
    
    import threading
    _exploring = True
    _exploration_thread = threading.Thread(target=_auto_explore_loop, daemon=True)
    _exploration_thread.start()
    return "🚀 自动探索模式已启动！AI将持续分析迷宫状态并控制角色移动。"


def stop_auto_exploration():
    """停止迷宫自动探索模式"""
    global _exploring
    _exploring = False
    stop_maze_game()
    return "🛑 自动探索已停止"


if __name__ == "__main__":
    #print("🟡 正在检查 API_KEY...", flush=True)
    if not API_KEY:
        print("⚠️ 请先设置环境变量 API_KEY 再运行。", flush=True)
        print("示例:", flush=True)
        print("export API_KEY=sk-xxxxxxxxxxxxxxxx", flush=True)
        print("python3 toolkit_agent.py", flush=True)
        exit(1)

    #print("🟡 API_KEY 检查通过，正在初始化...", flush=True)

    # 初始化林离
    print("林离已初始化。", flush=True)
    from tools import initialize_character
    initialize_character()
    print("林离已连接。今天有什么想聊聊的吗？", flush=True)
    print("提示：输入 'start_exploration' 启动迷宫自动探索", flush=True)
    
    # 启动界面简洁干净
    try:
        while True:
            user_msg = input("你: ")
            if user_msg.lower() in ["quit", "exit", "q"]:
                stop_auto_exploration()
                print("再见。", flush=True)
                break
            if user_msg.lower() == "start_exploration":
                result = start_auto_exploration()
                print(f"系统: {result}\n", flush=True)
                continue
            if user_msg.lower() == "stop_exploration":
                result = stop_auto_exploration()
                print(f"系统: {result}\n", flush=True)
                continue
            try:
                answer = chat(user_msg)
                print(f"林离: {answer}\n", flush=True)
            except Exception as e:
                print(f"❌ 出错了: {e}\n", flush=True)
                import traceback
                traceback.print_exc()
    except KeyboardInterrupt:
        stop_auto_exploration()
        print("\n再见。", flush=True)
