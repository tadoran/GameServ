from copy import deepcopy
import numpy as np
from random import shuffle

from games.TicTacToe.player import TicTacToeAbstractPlayer, TicTacToePersonPlayer, TicTacToeComputerPlayer
from games.spectator import Spectator


class TicTacToeGame:
    # global spectator

    def __init__(self):
        self.field = np.zeros((3, 3), dtype='int8')
        self.max_players = 2
        self.players: list[TicTacToeAbstractPlayer] = []
        self.win_conditions = ["123", "456", "789", "147", "258", "369", "159", "357"]
        self.started = False
        self.spectator = Spectator()

    def add_player(self, player: TicTacToeAbstractPlayer):
        self.players.append(player)

    def start_game(self):
        if len(self.players) != self.max_players:
            raise ValueError("Not enough players!")

        shuffle(self.players)
        self.started = True
        self.spectator.print("Game is started")
        while self.started:
            for player in self.players:
                if not self.started:
                    break
                self.spectator.print(f"{player} - it is your turn.")
                move = player.get_turn()
                while not move:
                    move = player.get_turn()

    def get_player_position(self, player: TicTacToeAbstractPlayer):
        return self.players.index(player) + 1

    def make_move(self, player: TicTacToeAbstractPlayer, coords: tuple[int, int]):
        if self.field[coords] != 0:
            self.spectator.print(f"Position {coords} is occupied!")
            return False
        else:
            self.spectator.print(f"{player} goes to {coords}")
            self.field[coords] = player.position
            self.spectator.print(self)
            if self.check_win(player):
                self.spectator.print(f"{player} wins!")
                self.started = False
            elif len(self.win_conditions) == 0:
                self.spectator.print("Tie, no one wins!")
                self.started = False
        return True

    def __str__(self):
        txt = "\n".join(str(self.field[i]) for i in range(0, 3)) + "\n"
        # txt = txt.translate(txt.maketrans({"0": " ", "1": "X", "2": "O"}))
        txt = txt.translate(txt.maketrans("012[]", " XO||", ""))
        return txt

    def check_win(self, player: TicTacToeAbstractPlayer):
        win = False
        win_conditions = deepcopy(self.win_conditions)
        fld = np.ravel(self.field)
        for wc in win_conditions:
            fld_vals = fld[[int(k) - 1 for k in wc]]
            win = False not in [i == player.position for i in fld_vals]
            cannot_win = False not in [i in fld_vals for i in (1, 2)]
            if cannot_win:
                self.win_conditions.remove(wc)
            if win:
                self.started = False
                break
        return win


if __name__ == '__main__':
    g = TicTacToeGame()
    spectator = Spectator()
    g.spectator = spectator
    g.add_player(TicTacToePersonPlayer(g))
    g.add_player(TicTacToeComputerPlayer(g))
    p1, p2 = g.players

    g.start_game()
