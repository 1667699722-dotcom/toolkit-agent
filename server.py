import socket # 导入socket模块
def main():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # 创建socketsocket对象
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # 设置socket选项，允许地址重用
    server_socket.bind(('0.0.0.0', 8888))# 绑定socket对象到指定的IP地址和端口号
    server_socket.listen(5) # 监听连接，最大连接数是5个
    print("服务器已启动，监听 0.0.0.0:8888")
    while True:
        client_socket, client_address = server_socket.accept()# 掭受客户端连接
        print(f"连接已建立，客户端地址：{client_address}")
        data = client_socket.recv(1024) #接收客户端数据，最大字节数是1024字节
        if data:
            print(f"收到客户端数据：{data.decode()}")
            client_socket.send(data)
        else:
            break
        client_socket.close() # 关闭客户端socket
    server_socket.close() # 关闭服务器socket
    print("服务器已关闭")
if __name__ == "__main__":
    main()