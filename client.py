import socket
PORT = 60005

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(("127.0.0.1", PORT))

while True:
    data = client.recv(1024).decode('utf-8')
    if data[-2:] == "-1":
        print("skip received: ", data)
        continue
    print("received: ", data)
    send_data = input("Send: ")
    client.send(send_data.encode('utf-8'))