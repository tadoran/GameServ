from time import sleep, time
from typing import Any

from games.TicTacToe.player import TicTacToeHumanSocketPlayer, TicTacToeComputerPlayer
from games.spectator import Spectator
from server.protocol import ProtocolCommand, Protocol
from server.proxy import Proxy
from games.TicTacToe.game import TicTacToeGame as Game


class SocketSpectactor(Spectator):

    def __init__(self, proxy: Proxy):
        # super().__init__()
        self.proxy = proxy

    def print(self, new_txt, *args, **kwargs):
        # super().print(new_txt, *args, **kwargs)
        print_func = self.proxy.protocol.get_send_callback("print")
        connected_clients = self.proxy.broker.clients
        recievers = connected_clients.keys()
        for client_address in recievers:
            print_func(client_address, new_txt)


class GameProxy(Proxy):
    def __init__(self, name="Game Proxy"):
        super(GameProxy, self).__init__(name=name)
        self.protocol = Protocol()
        self.awaiting_response: dict[tuple[str, str], Any] = {}

    def receive(self, sender, message):
        super(GameProxy, self).receive(sender, message)
        try:
            abbr, receive_callback, args = self.protocol.parse_on_receive(message)
            response_callback_result = receive_callback(sender=sender, message=args)
            is_waited = (sender, abbr) in self.awaiting_response
            if is_waited:
                self.awaiting_response[(sender, abbr)] = message
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
        self.game.spectator = SocketSpectactor(self)

        new_connection = ProtocolCommand("connected", self.receive_new_connection, None)
        self.protocol.add_command(new_connection)

        get_user_id = ProtocolCommand("get_user_id", self.on_id_receive, self.on_id_request)
        self.protocol.add_command(get_user_id)

        user_input = ProtocolCommand("user_input", self.on_input_receive, self.on_input_request)
        self.protocol.add_command(user_input)

        print_to_client = ProtocolCommand("print", None, self.send_text_to_client)
        self.protocol.add_command(print_to_client)

    # def __command_send_and_wait(self, *args, **kwargs):
    #     a = asyncio.to_thread(self._command_send_and_wait, *args, **kwargs)
    #     return a

    def send_text_to_client(self, receiver, message):
        encoded_message = self.protocol['print'].encode_command(message)
        self.send(receiver, encoded_message)

    def command_send_and_wait(self, receiver, command: str, timeout: int = 20, *args, **kwargs):
        send_callback = self.protocol.get_send_callback(command)
        send_callback(*args, **kwargs)

        receiver_address = self.clients.get(receiver, None)
        if not receiver_address:
            return None
        else:
            awaiting_response_key = receiver_address, command

            sent_time = time()
            self.awaiting_response[awaiting_response_key] = None
            while self.awaiting_response[awaiting_response_key] is None and time() - sent_time < timeout:
                sleep(0.1)

            message = self.awaiting_response.get(awaiting_response_key, None)
            result = self.protocol.parse_on_receive(message)[2]
            return result

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

        print_to_client = ProtocolCommand("print", self.print_text_on_client, None)
        self.protocol.add_command(print_to_client)

    def print_text_on_client(self, sender, message):
        print(message)

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
