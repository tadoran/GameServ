from abc import ABC, abstractmethod
from random import choice
from time import sleep

import numpy as np

from games import spectator


class AbstractPlayer(ABC):
    def __init__(self, game):
        self.game = game


class AbstractServerSideProxy:
    pass


class AbstractClientSideProxy:
    pass


class TicTacToeAbstractPlayer(AbstractPlayer):
    def __init__(self, game=None):
        super().__init__(game)

    def make_move(self, coords):
        if not self.game:
            raise AttributeError("Game is not initialized")
        else:
            return self.game.make_move(self, coords)

    @abstractmethod
    def get_turn(self):
        pass

    @property
    def position(self):
        return self.game.get_player_position(self)

    def __str__(self):
        return f"Player {self.position}"


class TicTacToePersonPlayer(TicTacToeAbstractPlayer):
    def get_turn(self):
        valid = False
        x, y = 0, 0

        while not valid:
            coords_to_hit_str = input("Select x,y to place your mark:\n")
            try:
                x, y = map(int, coords_to_hit_str.split(","))
                valid = True
            except ValueError:
                spectator.print("Invalid input")
                valid = False

        return self.make_move((x - 1, y - 1))

    def __str__(self):
        return "Kostia"


class TicTacToeHumanSocketPlayer(TicTacToeAbstractPlayer):
    def __init__(self, game, proxy, name: str):
        super(TicTacToeHumanSocketPlayer, self).__init__(game)
        self.proxy = proxy
        self.name = name

    def get_turn(self):
        valid = False
        x, y = 0, 0

        while not valid:
            # coords_to_hit_str = input("Select x,y to place your mark:\n")
            # coords_to_hit_str = self.proxy.Protocol.get_send_callback("user_input")
            # send_callback = self.proxy.protocol.get_send_callback("user_input")
            # send_callback(self.name, "Select x,y to place your mark:\n")

            coords_to_hit_str = self.proxy.command_send_and_wait(
                                                                receiver=self.name,
                                                                command="user_input",
                                                                player_id=self.name,
                                                                input_str="Select x,y to place your mark:\n"
                                                                )


            # ].prepare(self.name, "Select x,y to place your mark:\n")
            try:
                x, y = map(int, coords_to_hit_str.split(","))
                valid = True
            except ValueError:
                spectator.print("Invalid input")
                valid = False

        return self.make_move((x - 1, y - 1))


class TicTacToeComputerPlayer(TicTacToeAbstractPlayer):
    def get_turn(self):
        empty_cells_raw = np.where(self.game.field == 0)
        cell_to_fill = choice(tuple(zip(empty_cells_raw[0], empty_cells_raw[1])))
        sleep(0.8)
        return self.make_move(cell_to_fill)

    def __str__(self):
        return "Computer"
