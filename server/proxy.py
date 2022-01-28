# from server.socks_server import SocketObject
from time import strftime, localtime


class Proxy:
    def __init__(self, name: str = "DefaultProxy"):
        self.name = name
        self.broker = None

    def set_broker(self, broker):
        self.broker = broker

    def receive(self, sender, message):
        print(f"{strftime('%H:%M:%S', localtime())} {self.name}: Received from {sender}: {message}")

    def send(self, receiver, message):
        print(f"{strftime('%H:%M:%S', localtime())} {self.name}: Sent to {receiver}: {message}")
        self.broker.send_message(receiver, message)
