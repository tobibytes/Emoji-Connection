import threading
import socket
from utils import is_valid_username
host = "127.0.0.1"
PORT = 60006


class ConnectionManager:
    def __init__(self):
        self.user_to_connection = {}
        self.connnection_to_user = {}
    
    def print_connections_db(self):
        print('connections: ', self.user_to_connection)
    
    def get_username(self, conn: socket.socket):
        conn.send("Type in your username: ".encode('utf-8'))
        username = conn.recv(1024).decode('utf-8')
        if is_valid_username(username):
            self.user_to_connection[username] = conn
            self.connnection_to_user[conn] = username


def handle_connection(conn: socket.socket, addr, conn_manager: ConnectionManager):
    conn.send("Hello from server -1".encode('utf-8'))
    conn_manager.get_username(conn)
    conn_manager.print_connections_db()
    
    while True:
        recv_data = conn.recv(1024).decode('utf-8')
        print(f"recieved from {conn_manager.connnection_to_user[conn]}: {recv_data}")
        conn.send("processed it".encode('utf-8'))
    
    
    
def main():
    connection_manager = ConnectionManager()
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # TCP/IPv4 socket
    server.bind((host, PORT))
    print("started listening")
    server.listen()
    while True:
        conn, addr = server.accept()
        t = threading.Thread(target=handle_connection, args=(conn, addr, connection_manager))
        t.start()


if __name__ == "__main__":
    main()