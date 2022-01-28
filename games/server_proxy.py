from games.TicTacToe.player import TicTacToeHumanSocketPlayer, TicTacToeComputerPlayer
from server.protocol import ProtocolCommand, Protocol
from server.proxy import Proxy
from games.TicTacToe.game import TicTacToeGame as Game


class GameProxy(Proxy):
    def __init__(self, name="Game Proxy"):
        super(GameProxy, self).__init__(name=name)
        self.protocol = Protocol()

    def receive(self, sender, message):
        super(GameProxy, self).receive(sender, message)
        try:
            abbr, receive_callback, args = self.protocol.parse_on_receive(message)
            response_callback_result = receive_callback(sender=sender, message=args)
            if response_callback_result:
                response = self.protocol[abbr].encode_command(response_callback_result)
                self.send(sender, response)

        except Exception as e:
            print(e)


class GameServerProxy(GameProxy):
    def __init__(self):
        super(GameServerProxy, self).__init__("Game Server")
        self.clients = {}
        self.game = Game()

        self.protocol = Protocol()

        new_connection = ProtocolCommand("connected", self.receive_new_connection, None)
        self.protocol.add_command(new_connection)

        get_user_id = ProtocolCommand("get_user_id", self.on_id_receive, self.on_id_request)
        self.protocol.add_command(get_user_id)

        user_input = ProtocolCommand("user_input", self.on_input_receive, self.on_input_request)
        self.protocol.add_command(user_input)

    def on_input_receive(self, sender: str, message: str):
        print(sender, message)
        pass

    def on_input_request(self, player_id: str, input_str: str):
        player = self.clients.get(player_id, None)
        if not player:
            raise RuntimeError(f"Player {player_id} is not connected")

        message = self.protocol["user_input"].encode_command(input_str)
        self.send(player, message)

    def receive_new_connection(self, sender: str, message: str):
        address = message

        print(f"There is new connection from {address}")
        print(f"Requesting unique id")
        self.send(address, self.protocol['get_user_id'].encode_command("1"))

    def on_id_request(self, sender, message):  # noqa
        return 1

    def on_id_receive(self, sender, message: str):
        player_id = message

        print(f"Player {player_id} is connected now")

        player_exists = self.clients.get(player_id, None)
        self.clients[player_id] = sender
        if not player_exists:
            player = TicTacToeHumanSocketPlayer(game=self.game, proxy=self, name=player_id)
            self.game.add_player(player)
            self.game.add_player(TicTacToeComputerPlayer(game=self.game))
            self.game.start_game()


class GameClientProxy(GameProxy):
    def __init__(self):
        super(GameClientProxy, self).__init__("Game Client")

        self.protocol = Protocol()

        get_id = ProtocolCommand("get_user_id", self.id_requested, self.provide_id)
        self.protocol.add_command(get_id)

        user_input = ProtocolCommand("user_input", self.on_input_request, None)
        self.protocol.add_command(user_input)

    def on_input_request(self, sender, message):
        txt = input(message)

        return_message = self.protocol["user_input"].encode_command(txt)
        self.send(sender, return_message)

    def id_requested(self, sender, message):
        # print(args, kwargs)
        return str(self)

    def provide_id(self, sender, message):
        print(sender, message)

    def receive(self, sender, message):
        super().receive(sender, message)

    def __str__(self):
        return str(hash(self))
