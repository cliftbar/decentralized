"""Server for multithreaded (asynchronous) chat application."""
from socket import AF_INET, socket, SOCK_STREAM
from threading import Thread
import time

class Node:
    def start_server(self, server_addr):
        self.server_addr = server_addr
        HOST, PORT = self.server_addr.split(":")
        PORT = int(PORT)
        self.BUFSIZ = 1024
        self.SERVER_ADDR = (HOST, PORT)

        self.SERVER = socket(AF_INET, SOCK_STREAM)
        self.SERVER.bind(self.SERVER_ADDR)

        Thread(target=self.listen).start()

    def listen(self):
            self.SERVER.listen()
            print("Waiting for connection...")
            ACCEPT_THREAD = Thread(target = self.accept_incoming_connections)
            ACCEPT_THREAD.start()
            ACCEPT_THREAD.join()
            self.SERVER.close()

    # Listen for incomming connections
    def accept_incoming_connections(self):
        while True:
            client, client_address = self.SERVER.accept()
            print("%s:%s has connected." % client_address)

            # Welcome message
            client.send(bytes("Type your name and press enter: ", "utf8"))

            Thread(target=self.handle_client, args=(client,)).start()

    def handle_client(self, client):  # Takes client socket as argument.
        #print(client)
        data = client.recv(self.BUFSIZ).decode("utf8")
        #print("handle string: {0} end".format(data))

        if (data[0] == '\x11'):
            #print("register")
            check, addr, name = data.split('|')
            if (check != "\x11{Register}" and (addr != self.server_addr)):
                client.send(bytes("\x10Bad friend, you have to register yourself.", "utf8"))
                return

            self.register_conn(addr, name)
            welcome = '\x10Welcome %s! If you ever want to quit, type {quit} to exit.' % name
            client.send(bytes(welcome, "utf8"))
            msg = "%s has joined the chat!" % name
            time.sleep(1)
            self.broadcast(bytes(msg, "utf8"))
        elif (data[0] == '\x12'):
            #print("peers: " + str(data))
            check = data.split('|')[0]
            # print(check)
            if (check == "\x12{Peers}"):
                # print("adding peers")
                added = self.update_peers(data)
                if added:
                    self.broadcast(bytes(data, 'utf8'))
            #print("Connections: {0}".format(str(self.connections)))
        x = 10
        while True: # x > 0:
            x = x - 1
            msg = client.recv(self.BUFSIZ)
            #print("RecieveMsg: " + msg.decode('utf8'))
            if msg != bytes("\x13{quit}", "utf8"):
                print(msg.decode('utf8'))
                msgDecode = msg.decode('utf8')
                if (msgDecode.split("|")[0] == "\x12{Peers}"):
                    added = self.update_peers(msgDecode)
                    if added:
                        self.broadcast(msg)
                else:
                    self.broadcast(msg, self.name + ": ")
            else:
                try:
                    client.send(bytes("\x13{quit}", "utf8"))
                except ConnectionResetError:
                    self.userquit(name)
                client.close()
                self.userquit(name)
                break

    def update_peers(self, peer_str):
        #print(peer_str)
        peers_csv = peer_str.split("|")[1]
        peers = list(peers_csv.split(","))
        added = False
        for peer in peers:
            #print(peer)
            name, ip, port = peer.split(":")
            #print("{0}, {1}, {2}".format(name, ip, port))
            addr = ip + ":" + port
            if (name not in self.connections and addr != self.server_addr):
                self.register_conn(addr, name)
                added = True
        return added

    def register_conn(self, addr, name):
        
        ip, port = addr.split(':')
        print("Registering peer {0} at {1}".format(name, addr))
        port = int(port)
        sock = socket(AF_INET, SOCK_STREAM)
        sock.connect((ip, port))
        self.connections[name] = ((ip, port), sock)
        peers = "\x12{Peers}|" + ",".join(list(map(lambda x: x + ":" + self.connections[x][0][0] + ":" + str(self.connections[x][0][1]), self.connections)))
        peers = peers + ",{0}:{1}".format(self.name, self.server_addr)
        self.broadcast(bytes(peers, 'utf8'))

    def broadcast(self, msg, prefix=""):
        sender = msg.decode('utf8').split(":")[0:-1]
        sender = list(map(lambda x: x.strip(), sender))
        for name in self.connections:
            if (self.connections[name][0] != self.SERVER_ADDR and str(name) not in sender):
                #print("Broadcast: {3}|{0}|{1}|{2}|{4}".format(str(self.connections[name][0]), str(self.SERVER_ADDR), sender, name, str(name) not in sender))
                try:
                    self.connections[name][1].send(bytes(prefix, "utf8") + msg)
                except ConnectionResetError:
                    print("Cannot send to ",prefix," Connection has been reset")

    def userquit(self, name):
        # Nodes need to note that a peer has left still, and remove it from their peer store
        print("{0} has quit.".format(name))
        del self.connections[name]
        self.broadcast(bytes("%s has left the chat." % name, "utf8"))

    def input_loop(self):
        """Handles sending of messages."""
        while True:
            msg = input("Get Input: ")
            self.client_sock.send(bytes("\x10" + msg, "utf8"))
            if msg == "\x13{quit}":
                self.client_sock.close()
                break

    def connect_client(self, client_addr):
        ip, port = client_addr.split(':')
        port = int(port)
        self.client_addr = (ip, port)
        self.client_sock = socket(AF_INET, SOCK_STREAM)
        self.client_sock.connect(self.client_addr)
        welcome_msg = self.client_sock.recv(self.BUFSIZ).decode('utf8')
        self.name = input(welcome_msg)
        register_msg = bytes("\x11{Register}" + "|{0}:{1}|{2}".format(self.SERVER_ADDR[0], self.SERVER_ADDR[1], self.name), 'utf8')
        #print("Client Register Msg: " + self.name)
        self.client_sock.send(register_msg)
        self.input_loop()

    def __init__(self, server_addr, client_addr):
        # server = Node.Server(server_addr)
        self.connections = {}
        self.name = ""
        self.start_server(server_addr)
        print("server started")
        
        #client = Node.Client(client_addr)
        if client_addr is not None:
            self.connect_client(client_addr)
            self.input_loop
            print("client started")

server_addr = input("server address (where this server listens): ")

client_addr = input("client address (where this client will send to/recieve from): ")
# connect first client to its own server
if client_addr == "":
    #client_addr = server_addr
    client_addr = None

node = Node(server_addr, client_addr)


