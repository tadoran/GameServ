import socket
import threading
from enum import Enum
from time import sleep


class Proxy:
    def __init__(self, name: str = "DefaultProxy"):
        self.name = name
        self.broker = None

    def set_broker(self, broker):
        self.broker = broker

    def receive(self, sender, message):
        print(f"{self.name}: Received from {sender}: {message}")

    def send(self, receiver, message):
        print(f"{self.name}: Sent to {receiver}: {message}")
        self.broker.send_message(receiver, message)


class SocksRole(Enum):
    SERVER = 0
    CLIENT = 1


class SocketObject:
    HEADER = 64
    PORT = 8080
    SERVER = socket.gethostbyname(socket.gethostname())
    FORMAT = 'utf-8'
    DISCONNECT_MESSAGE = "!DISCONNECT"

    def __init__(self, role: SocksRole, address=None, port=None, proxy: Proxy = None):
        if address: self.SERVER = address
        if port: self.PORT = port
        self.ADDR = self.SERVER, self.PORT
        self.proxy = proxy
        proxy.set_broker(self)

        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.role = role

        self.clients = {}

    def __str__(self):
        if hasattr(self, "name"):
            return f"{self.name} at {self.ADDR}({self.role})"
        else:
            return f"SocksServer at {self.ADDR}({self.role})"

    def send_message(self, address, message):
        client = self.clients.get(address, None)
        if not client:
            return False
        else:
            conn = client['conn']

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
            msg_length = conn.recv(self.HEADER).decode(self.FORMAT)
            if msg_length:
                try:
                    msg_length = int(msg_length)
                except Exception as e:
                    return ""
                message = conn.recv(msg_length).decode(self.FORMAT)
                return message
        except ConnectionResetError:
            return ""
        except OSError:  # [WinError 10038] Сделана попытка выполнить операцию на объекте, не являющемся сокетом
            return ""

    def listen_connection(self, address):
        print(f"Connection to {address} has been established.")
        connected = True
        client = self.clients.get(address, None)
        if not client:
            return False
        else:
            conn = client['conn']

        while connected:
            message = self.parse_response(conn)
            if message == self.DISCONNECT_MESSAGE or message == "" or message is None:
                connected = False
            else:
                proxy = client['proxy']
                if proxy:
                    proxy.receive(address, message)

                if message != "OK":
                    # print("Sending OK")
                    self.send_message(address, "OK")

        print(f"Connection to {address} has been dropped.")
        self.clients.pop(address)
        conn.close()
        if hasattr(self, "auto_reconnect"):
            self.reconnect()

    # @property
    # def connected(self):
    #     # return not self.server._closed
    #     try:
    #         self.server.connect(self.ADDR)
    #     except
    @property
    def connected(self) -> bool:

        try:
            timeout = self.server.gettimeout()
            self.server.setblocking(False)
            # this will try to read bytes without blocking and also without removing them from buffer (peek only)
            # data = self.server.recv(16, socket.MSG_DONTWAIT | socket.MSG_PEEK)
            data = self.server.recv(16, socket.MSG_PEEK)
            if len(data) == 0:
                connected = False
            else:
                connected = True

        except BlockingIOError:
            connected = True  # socket is open and reading from it would block
        except ConnectionResetError:
            connected = False  # socket was closed for some other reason
        except OSError:
            connected = False
        except Exception as e:
            # logger.exception("unexpected exception when checking if a socket is closed")
            connected = False

        # self.server.setblocking(True)
        try:
            self.server.settimeout(timeout)
        except Exception:
            pass
        return connected


class SocketClient(SocketObject):
    MAX_RECONNECTIONS = 10

    def __init__(self, address=None, port=None, proxy: Proxy = None, auto_reconnect: bool = True,
                 max_attempts: int = 10):
        super(SocketClient, self).__init__(role=SocksRole.CLIENT, address=address, port=port, proxy=proxy)
        self.connection_attempts = 0
        self.auto_reconnect = auto_reconnect
        # self.connect_to_server()
        self.reconnect()

    def connect_to_server(self):
        # if attempt < self.MAX_RECONNECTIONS:
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print(f"Connecting as client to {self.ADDR}")

        try:
            self.server.connect(self.ADDR)
        except Exception as e:
            print(e)
            self.server = None
            return

        thread = threading.Thread(target=self.listen_connection, kwargs={"address": self.ADDR}, daemon=True)
        self.clients = {self.ADDR: {"conn": self.server, "proxy": self.proxy, "thread": thread}}

        thread.start()

    def reconnect(self):
        while not self.connected and not self.connection_attempts_limit_exceeded:
            try:
                self.connection_attempts += 1
                self.connect_to_server()
            except Exception as e:
                print(e)
                sleep(1)
        if self.connected:
            self.connection_attempts = 0
        else:
            raise RuntimeError(f"Could not connect to server at {self.ADDR}")

    @property
    def connection_attempts_limit_exceeded(self):
        return self.connection_attempts > self.MAX_RECONNECTIONS


class SocketServer(SocketObject):
    def __init__(self, address=None, port=None, proxy: Proxy = None):
        super(SocketServer, self).__init__(role=SocksRole.SERVER, address=address, port=port, proxy=proxy)
        print(f"Starting socks server on {self.ADDR}")
        self.server.bind(self.ADDR)
        self.clients = {}
        thread = threading.Thread(target=self.process_incoming_connections)
        thread.start()

    def process_incoming_connections(self):
        self.server.listen()
        # print(f"[LISTENING] Server is listening on {self.SERVER}")
        while True:
            conn, addr = self.server.accept()

            thread = threading.Thread(target=self.listen_connection, kwargs={"address": addr}, daemon=True)
            self.clients[addr] = {"conn": conn, "proxy": self.proxy, "thread": thread}

            thread.start()
            # print(f"[ACTIVE CONNECTIONS] {threading.active_count() - 1}")
            print(f"[ACTIVE CONNECTIONS] {self.connections_count}")

    @property
    def connections_count(self):
        return len(self.clients)


if __name__ == '__main__':
    # print("[STARTING] server is starting...")
    proxy = Proxy(name="ServerProxy")
    server = SocketServer(proxy=proxy, port=8080)
    server.name = "Server"
    # client1 = SocketObject(role=SocksRole.CLIENT, proxy=proxy, port=5050)
    # client1.name = "Client1"
    # client1.send_message(client1.ADDR, "client1 Hi")
    # client2 = SocketObject(role=SocksRole.CLIENT, proxy=proxy, port=5050)
    # client2.name = "Client2"
    # client2.send_message(client2.ADDR, "client2 Hi")
    # client2.send_message(client2.ADDR, "client2 Hi2")
    # client1.send_message(client1.ADDR, "client1 Hi2")
