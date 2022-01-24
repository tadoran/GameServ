from typing import Optional
from copy import deepcopy
import numpy as np
from abc import ABC
from random import choice
from time import sleep


class AbstractPlayer(ABC):
    def __init__(self, game):
        self.game = game


class TicTacToeAbstractPlayer(AbstractPlayer):
    def __init__(self, game=None):
        super().__init__(game)

    def make_move(self, coords):
        if not self.game:
            raise AttributeError("Game is not initialized")
        else:
            return self.game.make_move(self, coords)

    @property
    def position(self):
        return self.game.get_player_position(self)

    def __str__(self):
        return f"Player {self.position}"


class TicTacToePersonPlayer(TicTacToeAbstractPlayer):
    def get_turn(self):
        valid = False
        while not valid:
            coords_to_hit_str = input("Select x,y to place your mark:\n")
            try:
                x, y = map(int, coords_to_hit_str.split(","))
                valid = True
            except ValueError:
                print("Invalid input")
                valid = False

        return self.make_move((x - 1, y - 1))


class TicTacToeComputerPlayer(TicTacToeAbstractPlayer):
    def get_turn(self):
        # empty_cells = [c for c in self.game.field if c == 0]
        empty_cells_raw = np.where(self.game.field == 0)
        cell_to_fill = choice(tuple(zip(empty_cells_raw[0], empty_cells_raw[1])))
        sleep(0.8)
        return self.make_move(cell_to_fill)


class TicTacToeGame:
    def __init__(self):
        self.field = np.zeros((3, 3), dtype='int8')
        self.players = (TicTacToePersonPlayer(self), TicTacToeComputerPlayer(self))
        self.win_conditions = ["123", "456", "789", "147", "258", "369", "159", "357"]
        self.started = False

    def start_game(self):
        self.started = True
        print("Game is started")
        while self.started:
            for player in self.players:
                if not self.started:
                    break
                print(f"{player} - it is your turn.")
                move = player.get_turn()
                while not move:
                    move = player.get_turn()

        return "AAA"

    def get_player_position(self, player: AbstractPlayer):
        return self.players.index(player) + 1

    def make_move(self, player: TicTacToeAbstractPlayer, coords: tuple[int, int]):
        if self.field[coords] != 0:
            print(f"Position {coords} is occupied!")
            return False
        else:
            print(f"{player} goes to {coords}")
            self.field[coords] = player.position
            print(self)
            if self.check_win(player, coords):
                print(f"{player} wins!")
                self.started = False
            elif len(self.win_conditions) == 0:
                print("No one wins!")
                self.started = False
        return True

    def __str__(self):
        txt = "\n".join(str(self.field[i]) for i in range(0, 3)) + "\n"
        # txt = txt.translate(txt.maketrans({"0": " ", "1": "X", "2": "O"}))
        txt = txt.translate(txt.maketrans("012[]", " XO||", ""))
        return txt

    def check_win(self, player: TicTacToeAbstractPlayer, pos: Optional[tuple] = None):
        win = False
        win_conditions = deepcopy(self.win_conditions)
        fld = np.ravel(self.field)
        for wc in win_conditions:
            fld_vals = fld[[int(k) - 1 for k in wc]]

            win = False not in [i == player.position for i in fld_vals]

            cannot_win = False not in [i in fld_vals for i in (1, 2)]
            if cannot_win:
                self.win_conditions.remove(wc)
                # continue
            if win:
                break
        return win


if __name__ == '__main__':
    g = TicTacToeGame()
    p1, p2 = g.players

    g.start_game()
