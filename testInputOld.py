from server.socks_server import SocketClient, Proxy
from time import sleep
proxy = Proxy(name="Client3 Proxy")
cl3 = SocketClient(proxy=proxy, port=8080)

connected = True
while connected:
    connected = cl3.connected
    if connected:
        try:
            msg = input("Введите текст:\n")
            print(msg)
            cl3.send_message(cl3.ADDR, msg)
            sleep(0.001)
        except EOFError as e:
            print("sssdsd")
            connected = False
            break
        #     exit(e)
        except Exception as e:
            print(e)
            connected = False
            exit()
