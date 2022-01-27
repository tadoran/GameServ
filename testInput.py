from server.socks_server import SocketClient, Proxy
from time import sleep
import sys
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
            cl3.send_message(cl3.ADDR, msg)
            sleep(0.001)
        except OSError as e:
            print(e)
            pass
        except Exception as e:
            print(e)
            break
    else:
        sleep(1)

# cl3 = None
# sys.exit()