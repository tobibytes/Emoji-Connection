import os
import socket
HOST = os.getenv("EMOJI_HOST", "127.0.0.1")
PORT = int(os.getenv("EMOJI_PORT", "10758"))

def main():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Use blocking mode for a simpler UX; if you prefer a timeout, uncomment next line and keep handling socket.timeout below.
    # client.settimeout(20)

    try:
        client.connect((HOST, PORT))
        buffer = ""
        while True:
            try:
                chunk = client.recv(4096)
                if not chunk:
                    print("server closed connection")
                    break
                buffer += chunk.decode("utf-8")
            except socket.timeout:
                # No data yet; continue waiting
                continue

            # Handle possibly multiple messages coalesced in one TCP recv.
            # Convention: informational messages end with "-1", prompts do not.
            parts = buffer.split("-1")

            # Print all complete informational parts
            for part in parts[:-1]:
                if part:
                    print("skip received:", part)

            remainder = parts[-1]

            # If there's any non-empty remainder, treat it as a prompt and ask for input
            if remainder.strip():
                print("received:", remainder)
                try:
                    send_data = input("Send: ")
                except EOFError:
                    send_data = ""
                client.send(send_data.encode("utf-8"))
                buffer = ""
            else:
                # No prompt yet; clear processed info and wait for more data
                buffer = ""
    except Exception as e:
        print(f"error: {e}")
    finally:
        try:
            client.close()
        except Exception:
            pass


if __name__ == "__main__":
    main()
