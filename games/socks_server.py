import threading

from server.socks_server import SocketServer
from games.server_proxy import GameServerProxy


class GameServer(SocketServer):
    name = "GameServer"

    def process_incoming_connections(self):
        self.server.listen()
        while True:
            conn, address = self.server.accept()

            thread = threading.Thread(target=self.listen_connection, kwargs={"address": address}, daemon=True)
            self.clients[address] = {"conn": conn, "proxy": self.proxy, "thread": thread}

            thread.start()
            a = self.proxy.protocol['connected'].receive_callback(self.name, address)


if __name__ == '__main__':
    game_server = GameServer(proxy=GameServerProxy())
