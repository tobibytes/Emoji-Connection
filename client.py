import socket
PORT = 10758
HOST="3.133.207.110"

def main():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.settimeout(10)

    try:
        client.connect((HOST, PORT))
        
        while True:
            data = client.recv(1024).decode('utf-8')
            if data[-2:] == "-1":
                print("skip received: ", data[:-2])
                continue
            print("received: ", data)
            send_data = input("Send: ")
            client.send(send_data.encode('utf-8'))
    except Exception as e:
        print(f"error: {e}")
        client.close()


if __name__ == "__main__":
    main()