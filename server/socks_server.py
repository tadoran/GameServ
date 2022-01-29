import socket
import threading
from queue import Queue
from enum import Enum
from time import sleep

from server.proxy import Proxy


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
        if address:
            self.SERVER = address
        if port:
            self.PORT = port

        self.ADDRESS = self.SERVER, self.PORT
        self.proxy = proxy
        proxy.set_broker(self)

        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.role = role

        self.clients = {}

        self.send_queue = Queue()
        send_thread = threading.Thread(target=self._send_messages, daemon=True)

        self.receive_queue = Queue()
        receive_thread = threading.Thread(target=self._process_input_messages, daemon=True)

        send_thread.start()
        receive_thread.start()

    def _send_messages(self):
        while True:
            task = self.send_queue.get(block=True)
            address, message = task

            success = False

            client = self.clients.get(address, None)

            if not client:
                success = False
                # return False
            else:
                conn = client['conn']

                message = message.encode(self.FORMAT)
                msg_length = len(message)
                send_length = str(msg_length).encode(self.FORMAT)
                send_length += b' ' * (self.HEADER - len(send_length))
                try:
                    conn.send(send_length)
                    conn.send(message)
                    print(f"{self}: message '{message}' was sent to {address}")
                except ConnectionResetError:
                    conn.close()
                    success = False
                    # return False
                except OSError:  # [WinError 10038] Сделана попытка выполнить операцию на объекте, не являющемся сокетом
                    conn.close()
                    success = False
                    # return False

                finally:
                    success = True

                if not success:
                    print(f"Could not send message {message} to {address}")

    def _process_input_messages(self):
        while True:
            try:
                task = self.receive_queue.get(block=True)
                connection_proxy, address, message = task
                thr = threading.Thread(target=connection_proxy.receive, args=(address, message))
                thr.start()
            except Exception as e:
                print(e)

    def __str__(self):
        if hasattr(self, "name"):
            return f"{self.name} at {self.ADDRESS}({self.role})"
        else:
            return f"SocksServer at {self.ADDRESS}({self.role})"

    def send_message(self, address, message):
        self.send_queue.put((address, message))

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
            if message in (self.DISCONNECT_MESSAGE, "", None):
                connected = False
            else:
                connection_proxy = client['proxy']

                if message != "OK":
                    # print("Sending OK")
                    self.send_message(address, "OK")

                    if connection_proxy:
                        # print(f"Putting '{connection_proxy}', '{address}', '{message}' to receive_queue")
                        self.receive_queue.put((connection_proxy, address, message))
                        # connection_proxy.receive(address, message)

        print(f"Connection to {address} has been dropped.")
        self.clients.pop(address)
        conn.close()

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
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print(f"Connecting as client to {self.ADDRESS}")

        try:
            self.server.connect(self.ADDRESS)
        except Exception as e:
            print(e)
            self.server = None
            return

        thread = threading.Thread(target=self.listen_connection, kwargs={"address": self.ADDRESS}, daemon=True)
        self.clients = {self.ADDRESS: {"conn": self.server, "proxy": self.proxy, "thread": thread}}

        thread.start()

    def listen_connection(self, address):
        super(SocketClient, self).listen_connection(address)
        if hasattr(self, "auto_reconnect"):
            self.reconnect()

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
            raise RuntimeError(f"Could not connect to server at {self.ADDRESS}")

    @property
    def connection_attempts_limit_exceeded(self):
        return self.connection_attempts > self.MAX_RECONNECTIONS


class SocketServer(SocketObject):
    def __init__(self, address=None, port=None, proxy: Proxy = None):
        super(SocketServer, self).__init__(role=SocksRole.SERVER, address=address, port=port, proxy=proxy)
        print(f"Starting socks server on {self.ADDRESS}")
        self.server.bind(self.ADDRESS)
        self.clients = {}
        thread = threading.Thread(target=self.process_incoming_connections)
        thread.start()

    def process_incoming_connections(self):
        self.server.listen()
        while True:
            conn, address = self.server.accept()

            thread = threading.Thread(target=self.listen_connection, kwargs={"address": address}, daemon=True)
            self.clients[address] = {"conn": conn, "proxy": self.proxy, "thread": thread}

            thread.start()

    @property
    def connections_count(self):
        return len(self.clients)


if __name__ == '__main__':
    proxy = Proxy(name="ServerProxy")
    server = SocketServer(proxy=proxy, port=8080)
    server.name = "Server"
