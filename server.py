import threading
import socket
from typing import List, Dict
from utils import is_valid_username

host = "0.0.0.0"
PORT = 10758


class ConnectionManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def instance(cls):
        return cls()

    def __init__(self):
        if getattr(self, "_initialized", False):
            return
        self.user_to_connection: Dict[str, socket.socket] = {}
        self.connnection_to_user: Dict[socket.socket, str] = {}
        self.message_handler = None
        self.server: socket.socket | None = None
        self.on_join_messages: List[str] = []
        self._initialized = True

    def set_message_handler(self, handler):
        self.message_handler = handler

    def set_on_join_messages(self, messages: List[str]):
        self.on_join_messages = list(messages or [])

    def send_to_user(self, username: str, message: str):
        conn = self.user_to_connection.get(username)
        if not conn:
            return
        try:
            conn.send(message.encode("utf-8"))
        except Exception:
            pass

    def get_users(self) -> List[str]:
        return list(self.user_to_connection.keys())

    def get_username(self, conn: socket.socket):
        conn.send(b"Type in your username: \n")
        try:
            username = conn.recv(1024).decode("utf-8").strip()
        except Exception:
            return
        if not is_valid_username(username):
            username = f"player{len(self.connnection_to_user)+1}"
        base, i = username, 1
        while username in self.user_to_connection:
            username = f"{base}{i}"
            i += 1
        self.user_to_connection[username] = conn
        self.connnection_to_user[conn] = username
        conn.send(f"Enjoy the game {username} \n-1".encode("utf-8"))
        self.broadcast(f"{len(self.connnection_to_user)} players active-1")
        try:
            if self.on_join_messages:
                for msg in self.on_join_messages:
                    conn.send(msg.encode("utf-8"))
            else:
                conn.send(b"whats your pick: \n")
        except Exception:
            pass

    def broadcast(self, message: str):
        dead: List[socket.socket] = []
        for conn in list(self.connnection_to_user.keys()):
            try:
                conn.send(message.encode("utf-8"))
            except Exception:
                dead.append(conn)
        for c in dead:
            self.terminate(c)

    def terminate(self, conn: socket.socket):
        user = self.connnection_to_user.pop(conn, None)
        if user:
            self.user_to_connection.pop(user, None)
        try:
            conn.close()
        except Exception:
            pass

    @staticmethod
    def initialize(message_handler=None):
        cm = ConnectionManager.instance()
        if message_handler:
            cm.set_message_handler(message_handler)

        def serve():
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((host, PORT))
            s.listen()
            cm.server = s
            print(f"Server listening on {host}:{PORT}")
            try:
                while True:
                    conn, addr = s.accept()
                    print(addr)
                    t = threading.Thread(
                        target=handle_connection, args=(conn, addr, cm), daemon=True
                    )
                    t.start()
            except Exception as e:
                print(f"Server error: {e}")
            finally:
                s.close()

        threading.Thread(target=serve, daemon=True).start()


def handle_connection(conn: socket.socket, addr, cm: ConnectionManager):
    cm.get_username(conn)
    try:
        while True:
            data = conn.recv(1024)
            if not data:
                break
            msg = data.decode("utf-8").strip()
            user = cm.connnection_to_user.get(conn)
            if cm.message_handler and user:
                try:
                    cm.message_handler(user, msg, cm)
                except Exception as e:
                    print(f"handler error: {e}")
            else:
                conn.send(b"Server not ready-1")
    except Exception as e:
        print(f"connection error: {e}")
    finally:
        cm.terminate(conn)
