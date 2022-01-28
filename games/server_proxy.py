from server.protocol import ProtocolCommand, Protocol
from server.proxy import Proxy


class GameProxy(Proxy):
    def __init__(self, name="Game Proxy"):
        super(GameProxy, self).__init__(name=name)
        self.protocol = Protocol()

    def receive(self, sender, message):
        super(GameProxy, self).receive(sender, message)
        try:
            abbr, receive_callback, args = self.protocol.parse_on_receive(message)
            response_callback_result = receive_callback(args)
            if response_callback_result:
                response = self.protocol[abbr].encode_command(response_callback_result)
                self.send(sender, response)

        except Exception as e:
            print(e)


class GameServerProxy(GameProxy):
    def __init__(self):
        super(GameServerProxy, self).__init__("Game Server")

        self.protocol = Protocol()

        new_connection = ProtocolCommand("connected", self.receive_new_connection, None)
        self.protocol.add_command(new_connection)

        get_user_id = ProtocolCommand("get_user_id", self.on_id_receive, self.on_id_request)
        self.protocol.add_command(get_user_id)

    def receive_new_connection(self, address: str):
        print(f"There is new connection from {address}")
        print(f"Requesting unique id")
        self.require_id(address)

    def require_id(self, address):
        self.send(address, self.protocol['get_user_id'].encode_command("1"))

    def on_id_request(self): # noqa
        return 1

    def on_id_receive(self, txt: str):
        pass


class GameClientProxy(GameProxy):
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
        super().receive(sender, message)

    def __str__(self):
        return str(hash(self))
