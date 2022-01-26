from server.socks_server import SocksServer, Proxy, SocksRole

proxy = Proxy(name="Client3 Proxy")
cl3 = SocksServer(role=SocksRole.CLIENT, proxy=proxy, port=5050)

cl3.send_message(cl3.ADDR, "client3 Hi1")
cl3.send_message(cl3.ADDR, "client3 Hi2")
cl3.send_message(cl3.ADDR, "client3 Hi3")
cl3.send_message(cl3.ADDR, "client3 Hi4")
cl3.send_message(cl3.ADDR, "client3 Hi5")
cl3.send_message(cl3.ADDR, "client3 Hi6")
