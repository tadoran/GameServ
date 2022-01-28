from server.protocol import ProtocolCommand, Protocol
from server.proxy import Proxy


class GameServerProxy(Proxy):
    def __init__(self):
        super(GameServerProxy, self).__init__("Game Server")

        self.protocol = Protocol()

        get_user_id = ProtocolCommand("get_user_id", self.decode_id, self.get_id)
        self.protocol.add_command(get_user_id)

        new_connection = ProtocolCommand("connected", self.receive_new_connection, lambda x: x)
        self.protocol.add_command(new_connection)

    def receive_new_connection(self, address: str):
        print(f"There is new connection from {address}")
        print(f"Requesting unique id")
        self.require_id(address)

    def require_id(self, address):
        self.send(address, self.protocol['get_user_id'].encode_command("1"))

    def get_id(self, txt: str):
        return 1

    def decode_id(self, txt: str):
        print(txt)


class GameClientProxy(Proxy):
    def __init__(self):
        super(GameClientProxy, self).__init__("Game Client")

        self.protocol = Protocol()

        get_id = ProtocolCommand("get_user_id", self.id_requested, self.provide_id)
        self.protocol.add_command(get_id)

    def id_requested(self, *args, **kwargs):
        # print(args, kwargs)
        return str(self)

    def provide_id(self, *args, **kwargs):
        print(args, kwargs)

    def receive(self, sender, message):
        try:
            abbr, receive_callback, args = self.protocol.get_message_handler(message)
            response = self.protocol[abbr].encode_command(receive_callback(args))
            self.send(sender, response)
        except Exception as e:
            print(e)
            super().receive(sender, message)

    def __str__(self):
        return str(hash(self))
