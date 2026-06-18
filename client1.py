import socket # 导入socket模块
def main():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
    # 创建socketsocket对象
    client_socket.connect(('127.0.0.1', 8888)) # 连接到服务器
    message = "Hello, TCP Echo Server!"# 发送的消息
    client_socket.send(message.encode('utf-8')) # 发送消息
    print(f"发送消息：{message}")
    response = client_socket.recv(1024)# 接收服务器响应，最大字节数是1024字节
    print(f"收到服务器响应：{response.decode('utf-8')}")
    client_socket.close() # 关闭客户端socket
    print("客户端已关闭")
if __name__ == "__main__":
    main()
