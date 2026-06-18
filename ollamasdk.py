import ollama
import re

# 1. 定义可执行函数
def add(a, b):
    return a + b

# 2. 调用 ollama（你已经写好的）
def call_ollama_sdk(prompt):
    response = ollama.chat(
        model='gemma3:1b ',
        messages=[{'role': 'user', 'content': prompt}]
    )
    return response['message']['content']

# 3. 核心：正则匹配 + 提取 + 调用！
def parse_and_execute(llm_output):
    #print(f"大模型返回的原始字符串: {llm_output}")
    
    # 正则表达式匹配 ADD(a,b)
    pattern = r'ADD\(\s*(\d+)\s*,\s*(\d+)\s*\)'
    match = re.search(pattern, llm_output)
    
    if match:
        # 提取参数
        a_str = match.group(1)
        b_str = match.group(2)
        a = int(a_str)
        b = int(b_str)
        
        #print(f"成功提取: 函数 ADD, 参数 a={a}, b={b}")
        
        # 调用函数
        result = add(a, b)
        print(f"执行结果: {a} + {b} = {result}")
        return result
    else:
        print("匹配失败！没有找到 ADD(a,b) 格式")
        return None

# 4. 完整测试
if __name__ == "__main__":
    user_prompt = "请计算32+21，给出计算表达式，输出结果仅显示ADD(a,b)的形式"
    llm_output = call_ollama_sdk(user_prompt)
    
    # 解析并执行
    parse_and_execute(llm_output)