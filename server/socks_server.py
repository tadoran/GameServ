import socket
import threading
from enum import Enum


class Proxy:
    def __init__(self, name: str = "DefaultProxy"):
        # self.server_obj = server_obj
        self.name = name

    def recieve(self, sender, message):
        print(f"{self.name}: Recieved from {sender}: {message}")

    def send(self, receiver, message):
        print(f"{self.name}: Sent to {receiver}: {message}")
        # self.server_obj.send_message(receiver, message)


class SocksRole(Enum):
    SERVER = 0
    CLIENT = 1


class SocksServer:
    HEADER = 64
    PORT = 5050
    SERVER = socket.gethostbyname(socket.gethostname())
    FORMAT = 'utf-8'
    DISCONNECT_MESSAGE = "!DISCONNECT"

    def __init__(self, role: SocksRole, address=None, port=None, proxy: Proxy = None):
        if address:
            self.SERVER = address
        if port:
            self.PORT = port

        self.ADDR = (self.SERVER, self.PORT)

        self.proxy = proxy
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.role = role

        if role == SocksRole.SERVER:
            print(f"Starting socks server on {self.ADDR}")
            self.server.bind(self.ADDR)
            self.clients = {}
            thread = threading.Thread(target=self.start)
            thread.start()

        elif role == SocksRole.CLIENT:
            print(f"Connecting as client to {self.ADDR}")

            self.server.connect(self.ADDR)
            self.clients = {self.ADDR: {"conn": self.server, "proxy": proxy}}
            thread = threading.Thread(target=self.listen_client, kwargs={"addr": self.ADDR})
            thread.start()

    def __str__(self):
        if hasattr(self, "name"):
            return f"{self.name} at {self.ADDR}({self.role})"
        else:
            return f"SocksServer at {self.ADDR}({self.role})"

    def start(self):
        self.server.listen()
        # print(f"[LISTENING] Server is listening on {self.SERVER}")
        while True:
            conn, addr = self.server.accept()

            self.clients[addr] = {"conn": conn, "proxy": self.proxy}

            thread = threading.Thread(target=self.listen_client, kwargs={"addr": addr})
            thread.start()
            print(f"[ACTIVE CONNECTIONS] {threading.active_count() - 1}")

    def send_message(self, addr, message):
        client = self.clients.get(addr, None)
        if not client:
            return False
        else:
            conn = client['conn']

        # print(f'{self} - start send_message: "{message}"')
        message = message.encode(self.FORMAT)
        msg_length = len(message)
        send_length = str(msg_length).encode(self.FORMAT)
        send_length += b' ' * (self.HEADER - len(send_length))
        try:
            conn.send(send_length)
            conn.send(message)
        except ConnectionResetError:
            conn.close()
            return False
        except OSError:  # [WinError 10038] Сделана попытка выполнить операцию на объекте, не являющемся сокетом
            conn.close()
            return False

        return True

    def parse_response(self, conn) -> str:
        try:
            # print(f"<<{conn}>>, <<{args}>>")
            # print(f"{self} - start parse_response")
            msg_length = conn.recv(self.HEADER).decode(self.FORMAT)
            if msg_length:
                try:
                    msg_length = int(msg_length)
                except Exception as e:
                    # print(e)
                    pass
                message = conn.recv(msg_length).decode(self.FORMAT)
                # print(f'{self} received message from {conn}: "{message}"')
                return message
        except ConnectionResetError:
            return ""
        except OSError:  # [WinError 10038] Сделана попытка выполнить операцию на объекте, не являющемся сокетом
            return ""

    def listen_client(self, addr):
        print(f"Connection to {addr} has been established.")
        connected = True
        client = self.clients.get(addr, None)
        if not client:
            return False
        else:
            conn = client['conn']

        while connected:
            message = self.parse_response(conn)
            # print(f'{self}: new message from {addr}: "{message}"')
            if message == self.DISCONNECT_MESSAGE or message == "":
                connected = False
            else:
                proxy = client['proxy']
                if proxy:
                    proxy.recieve(addr, message)

                if message != "OK":
                    # print("Sending OK")
                    self.send_message(addr, "OK")

        print(f"Connecion to {addr} has been dropped.")
        self.clients.pop(addr)
        conn.close()


# class SocksClient:
#     HEADER = 64
#     PORT = 5050
#     FORMAT = 'utf-8'
#     DISCONNECT_MESSAGE = "!DISCONNECT"
#     SERVER = socket.gethostbyname(socket.gethostname())
#     ADDR = (SERVER, PORT)
#
#     def __init__(self, server, player):
#         self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#         self.client.connect(self.ADDR)
#
#     def disconnect(self):
#         pass
#
#     def send(self, command):
#         message = command.encode(self.FORMAT)
#         msg_length = len(message)
#         send_length = str(msg_length).encode(self.FORMAT)
#         send_length += b' ' * (self.HEADER - len(send_length))
#         self.client.send(send_length)
#         self.client.send(message)
#         print(self.client.recv(2048).decode(self.FORMAT))
#
#     def receive(self, command):
#         pass
#
#     def register_player(self, player):
#         pass


if __name__ == '__main__':
    # print("[STARTING] server is starting...")
    proxy = Proxy(name="ServerProxy")
    server = SocksServer(role=SocksRole.SERVER, proxy=proxy, port=5050)
    server.name = "Server"
    client1 = SocksServer(role=SocksRole.CLIENT, proxy=proxy, port=5050)
    client1.name = "Client1"
    client1.send_message(client1.ADDR, "client1 Hi")
    client2 = SocksServer(role=SocksRole.CLIENT, proxy=proxy, port=5050)
    client2.name = "Client2"
    client2.send_message(client2.ADDR, "client2 Hi")
    # client2.send_message(client2.ADDR, "client2 Hi2")
    # client1.send_message(client1.ADDR, "client1 Hi2")
