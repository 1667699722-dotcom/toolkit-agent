import os
import json
from openai import OpenAI
from tools import FUNCTIONS, TOOLS_SCHEMA  # 从独立模块导入工具函数和 schema

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


def chat(user_input: str):
    """
    主对话函数：支持多轮工具调用（多步推理）
    流程：用户输入 -> 循环：{模型判断是否调工具 -> 执行 -> 回传结果} -> 返回自然语言回答
    """
    messages = [{"role": "user", "content": user_input}]
    max_rounds = 100  # 防止无限循环
    n=1
    for _ in range(max_rounds):
         
        # 调用模型：让它决定是否需要调用工具
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=tools,
            tool_choice="auto",
        )
        response_message = response.choices[0].message

        # 如果模型没调用工具 → 直接回答，结束循环
        if not response_message.tool_calls:
            return response_message.content
        print(f"第 {n} 轮") 
        # 有工具调用 → 先把模型的调用请求加入对话历史
        messages.append(response_message)
        #print(f"模型回复: {response_message.tool_calls}")
        # 遍历所有工具调用，一个个执行
        for tool_call in response_message.tool_calls:
            func_name = tool_call.function.name
            func_args = json.loads(tool_call.function.arguments)

            print(f"  [工具调用] {func_name}({func_args})")

            # 本地执行函数
            func = FUNCTIONS.get(func_name)
            if func:
                result = func(**func_args)
                print(f"  [执行结果] {result}")
            else:
                result = f"Error: unknown function '{func_name}'"

            # 把函数结果回传给模型（继续下一轮循环，模型会用这些结果继续推理）
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": str(result),
            })
         
        n+=1
    return response_message.content  # 达到最大轮次，返回最后一次回答


if __name__ == "__main__":
    if not API_KEY:
        print("⚠️  请先设置环境变量 API_KEY（也可以同时设置 BASE_URL 和 MODEL）")
        print("   示例:")
        print("     export API_KEY=sk-xxxxxxxxxxxxxxxx")
        print("     export BASE_URL=https://api.deepseek.com/v1")
        print("     export MODEL=deepseek-chat")
        print("   然后再运行: python3 ollamasdk.py")
        exit(1)

    print(f"✅ 已连接 {BASE_URL}，使用模型: {MODEL}")
    print("   输入 quit/exit/q 退出\n")

    while True:
        user_msg = input("你: ")
        if user_msg.lower() in ["quit", "exit", "q"]:
            print("再见！")
            break
        try:
            answer = chat(user_msg)
            print(f"AI: {answer}\n")
        except Exception as e:
            print(f"❌ 出错了: {e}\n")
