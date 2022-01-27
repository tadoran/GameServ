from server.socks_server import SocketClient, Proxy
from time import sleep, localtime, strftime
import sys

proxy = Proxy(name="Client3 Proxy")
cl3 = SocketClient(proxy=proxy, port=8080)

connected = True
while True:
    connected = cl3.connected
    curr_time = localtime()
    curr_clock = strftime("%H:%M:%S", curr_time)
    print(curr_clock)


    if connected:
        try:
            msg = curr_clock
            cl3.send_message(cl3.ADDR, msg)
            sleep(2)
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