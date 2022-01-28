from server.socks_server import SocketClient
from server.proxy import Proxy
from time import sleep

proxy = Proxy(name="Client3 Proxy")
cl3 = SocketClient(proxy=proxy, port=8080)

connected = True
while True:
    connected = cl3.connected
    if connected:
        try:
            msg = input("Введите текст:\n")
            print(msg)
            if msg == SocketClient.DISCONNECT_MESSAGE:
                break
            cl3.send_message(cl3.ADDRESS, msg)
            sleep(0.001)
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
