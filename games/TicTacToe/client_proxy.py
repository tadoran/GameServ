from time import sleep

from games.server_proxy import GameClientProxy
from server.socks_server import SocketClient


class TicTacToeClientProxy(GameClientProxy):
    pass


if __name__ == '__main__':
    playerProxy = TicTacToeClientProxy()
    socks_client = SocketClient(proxy=playerProxy)
    # player.connect()
    # print("hello")
    # sleep(100)
    while socks_client.connected:
        sleep(5)
    print(f"Game was ended. So, we quit too.")
