import threading
import socket
from utils import is_valid_username
from typing import List, Dict
host = "127.0.0.1"
PORT = 60007


class ConnectionManager:
    def __init__(self):
        self.user_to_connection: Dict[str, socket.socket] = {}
        self.connnection_to_user: Dict[socket.socket, str] = {}
    
    def print_connections_db(self):
        print('connections: ', self.user_to_connection)
    
    def send_to_user(self, username: str, message: str):
        if username not in self.user_to_connection:
            print("could not find user")
        conn = self.user_to_connection[username]
        conn.send(message.encode('utf-8'))
        
    def get_users(self) -> List[str]:
        return list(self.user_to_connection.keys())

    def get_username(self, conn: socket.socket):
        conn.send("Type in your username: ".encode('utf-8'))
        username = conn.recv(1024).decode('utf-8')
        if is_valid_username(username):
            self.user_to_connection[username] = conn
            self.connnection_to_user[conn] = username
        conn.send(f"Enjoy the game {username} -1".encode('utf-8'))

    def terminate(self, conn: socket.socket):
        user = self.connnection_to_user[conn]
        del self.connnection_to_user[conn]
        del self.user_to_connection[user]
        conn.close()

def handle_connection(conn: socket.socket, addr, conn_manager: ConnectionManager):
    conn.send("Hello from server -1".encode('utf-8'))
    conn_manager.get_username(conn)
    start_message = "Welcome to Emoji Con\nFind the path from 😎 -----> 🤔"
    conn_manager.send_to_user(conn_manager.connnection_to_user[conn], start_message)
    try:
        while True:
            recv_data = conn.recv(1024).decode('utf-8')
            print(f"recieved from {conn_manager.connnection_to_user[conn]}: {recv_data}")
            conn.send("processed it".encode('utf-8'))
    except:
        conn_manager.terminate(conn)
    
def main():
    connection_manager = ConnectionManager()
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # TCP/IPv4 socket
    server.bind((host, PORT))
    print("started listening")
    server.listen()
    try:
        while True:
            conn, addr = server.accept()
            t = threading.Thread(target=handle_connection, args=(conn, addr, connection_manager))
            t.start()
    except:
        server.close()
        


if __name__ == "__main__":
    main()