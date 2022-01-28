from games.server_proxy import GameClientProxy
from server.socks_server import SocketClient
from server.proxy import Proxy
from time import sleep, localtime, strftime
from games.chat.proxy import ChatProxy

# proxy = Proxy(name="Time Daemon")
# proxy = ChatProxy()
proxy = GameClientProxy()


cl3 = SocketClient(proxy=proxy, port=8080)

connected = True
while True:
    connected = cl3.connected
    curr_time = localtime()
    curr_clock = strftime("%H:%M:%S", curr_time)

    if connected:
        try:
            msg = curr_clock
            proxy.send(cl3.ADDRESS, msg)
            sleep(2)
        except OSError as e:
            print(e)
            pass
        except Exception as e:
            print(e)
            break
    else:
        if cl3.connection_attempts_limit_exceeded:
            break
        sleep(1)
