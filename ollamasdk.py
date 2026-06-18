import ollama

def call_ollama_sdk(prompt):
    response = ollama.chat(
        model='gemma3:1b ',  # 换成你下载的模型
        messages=[{'role': 'user', 'content': prompt}]
    )
    return response['message']['content']

# 使用示例
if __name__ == "__main__":
    print("回答:", call_ollama_sdk("你好，请介绍一下自己"))