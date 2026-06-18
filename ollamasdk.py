import ollama

function_schemas = {
    "add": {
        "type": "function",
        "function": {
            "name": "add",
            "description": "Add two numbers together",
            "parameters": {
                "type": "object",
                "properties": {
                    "a": {"type": "integer", "description": "The first number"},
                    "b": {"type": "integer", "description": "The second number"}
                },
                "required": ["a", "b"]
            }
        }
    }
}

def call_ollama_sdk(prompt):
    response = ollama.chat(
        model='gemma3:1b',  #小模型用来选出函数就行
        messages=[{'role': 'user', 'content': prompt}]
    )
    return response['message']['content']

def add(a: int, b: int) -> int:
    """
    Add two numbers together
    
    Args:
        a: The first number
        b: The second number
    
    Returns:
        The sum of a and b
    """
    return a + b

def call_ollama_with_functions():
    while True:
        messages = [{'role': 'user', 'content': msg}]
        tool_name = call_ollama_sdk(msg + ",请在如下函数中选择一个最合适的返回，仅返回如下:add、sub中一个")
        tool_name = tool_name.strip().lower()
        #print("工具名:", tool_name)
        
        # ✅ 2. 核心：根据tool_name字符串，从function_schemas里拿出对应的schema，放到tools列表！
        tools = []
        if tool_name in function_schemas:
            tools.append(function_schemas[tool_name])  # ✅ 字符串映射到schema并添加！
            #print(f"成功把 {tool_name} 加入 tools 列表，现在 tools = {tools}")
            
        response = ollama.chat(
            model='qwen3:4b',  # 需要用支持 tool calling 的模型
            messages=messages,
            tools=tools  # 动态生成的tools列表！
        )
        
        #print("完整响应:", response)
        
        if response.message.tool_calls:
            for tool_call in response.message.tool_calls:
                print(f"工具调用: {tool_call.function.name}")
                print(f"参数: {tool_call.function.arguments}")
                
                # 直接调用函数
                func = globals()[tool_call.function.name]
                result = func(**tool_call.function.arguments)
                print(f"执行结果: {result}")
                print("解决思路"+call_ollama_sdk("用一段话说明问题的思路"+msg))
                return result

if __name__ == "__main__":
    while True:
        msg = input("你: ")  # ✅ 从终端输入！
        if msg.lower() in ['quit', 'exit', 'q']:  # 支持退出
            print("再见！")
            break
        call_ollama_with_functions()
