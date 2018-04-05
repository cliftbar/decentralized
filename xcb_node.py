"""Server for multithreaded (asynchronous) chat application."""
from socket import AF_INET, socket, SOCK_STREAM
from threading import Thread

class Node:
    # peer store class to hold all peers of the node
    class p2p:
        peers = set()
        clients = {}

        @classmethod
        def addPeer(self, peer):
            self.peers.add(peer)
        @classmethod
        def removePeer(self, peer):
            self.peers.remove(peer)

    class Server:
        def accept_incoming_connections(self):
            """Sets up handling for incoming clients."""
            while True:
                client, client_address = self.SERVER.accept()
                print("%s:%s has connected." % client_address)
                # send peer list with every welcome message, to get new client up to date
                client.send(bytes("Greetings from the cave! Now type your name and press enter!|Peers;{0}".format(",".join(Node.p2p.peers)), "utf8"))
                # add peer to peer store
                print(client_address)
                #Node.p2p.addPeer(client_address[0] + ":" + str(client_address[1]))
                Thread(target=self.handle_client, args=(client,)).start()

        def handle_client(self, client):  # Takes client socket as argument.
            """Handles a single client connection."""

            name = client.recv(self.BUFSIZ).decode("utf8")
            welcome = 'Welcome %s! If you ever want to quit, type {quit} to exit.' % name
            client.send(bytes(welcome, "utf8"))
            msg = "%s has joined the chat!" % name
            print("server: " + msg)
            self.broadcast(bytes(msg, "utf8"))
            self.broadcast_peers(bytes(msg, "utf8"))
            Node.p2p.clients[client] = name

            while True:
                msg = client.recv(self.BUFSIZ)
                if msg != bytes("{quit}", "utf8"):
                    self.broadcast(msg, name + ": ")
                    self.broadcast_peers(msg, name + ": ")
                else:
                    # Will need to delete peer here from peer store
                    try:
                        client.send(bytes("{quit}", "utf8"))
                    except ConnectionResetError:
                        self.userquit(name)
                    client.close()
                    del Node.p2p.clients[client]
                    self.userquit(name)
                    break

        def userquit(self, name):
            # Nodes need to note that a peer has left still, and remove it from their peer store
            self.broadcast(bytes("%s has left the chat." % name, "utf8"))
            self.broadcast_peers(bytes("%s has left the chat." % name, "utf8"))
            print("{0} has quit.".format(name))

        def broadcast(self, msg, prefix=""):
            # prefix is for name identification.
            msg = prefix + msg.decode('utf8') + "|Peers;{0}".format(",".join(Node.p2p.peers))
            print("broadcasting to clients {0}".format(str(Node.p2p.clients)))
            for sock in Node.p2p.clients:
                try:
                    sock.send(bytes(msg, "utf8"))
                except ConnectionResetError:
                    print("Cannot send to ",prefix," Connection has been reset")
        
        def broadcast_peers(self, msg, prefix=""):
            # prefix is for name identification.
            send_peers = list(Node.p2p.peers) + [self.ADDR[0] + ":" + str(self.ADDR[1])]
            msg = prefix + msg.decode('utf8') + "|Peers2;{0}".format(",".join(send_peers))
            print("broadcasting to peers {0}".format(str(send_peers)))
            for addr in Node.p2p.peers:
                try:
                    ip, port = addr.split(':')
                    port = int(port)
                    sock = socket(AF_INET, SOCK_STREAM)
                    sock.connect((ip, port))
                    sock.send(bytes(msg, "utf8"))
                    sock.close()
                except ConnectionResetError:
                    print("Cannot send to ",prefix," Connection has been reset")

        def listen(self):
            self.SERVER.listen()
            print("Waiting for connection...")
            ACCEPT_THREAD = Thread(target = self.accept_incoming_connections)
            ACCEPT_THREAD.start()
            ACCEPT_THREAD.join()
            self.SERVER.close()

        def __init__(self, server_addr):
            #self.clients = {}
            self.addresses = {}

            HOST, PORT = server_addr.split(":")
            PORT = int(PORT)
            self.BUFSIZ = 1024
            self.ADDR = (HOST, PORT)

            self.SERVER = socket(AF_INET, SOCK_STREAM)
            self.SERVER.bind(self.ADDR)

            Thread(target=self.listen).start()

    class Client:
        def receive(self):
            """Handles receiving of messages."""
            while True:
                try:
                    # client, client_addr = self.client_socket.accept()
                    # if not Node.p2p.clients.contains(client):
                    #     Node.p2p.clients[client] = client_addr
                    msg = self.client_socket.recv(self.BUFSIZ).decode("utf8")
                    
                    # Parse out the peer list from the first message.  this could be cleaned up to check less ofter
                    print(msg)
                    fcon = msg.split("|")
                    if(len(fcon) > 1):
                        pcon = fcon[1].split(';')
                        if (len(pcon) > 0 and pcon[0] == "Peers"):
                            peers = pcon[1].split(",")
                            for p in peers:
                                if p != '':
                                    #print("adding peer {0}".format(str(p)))
                                    Node.p2p.addPeer(p)
                    print(fcon[0])
                    print(Node.p2p.peers)
                except OSError:  # Possibly client has left the chat.
                    break


        def send(self, event=None):  # event is passed by binders.
            """Handles sending of messages."""
            while True:
                msg = input("Get Input: ")
                self.client_socket.send(bytes(msg, "utf8"))
                if msg == "{quit}":
                    self.client_socket.close()
                    break

        #----Now comes the sockets part----
        #HOST = input('Enter host: ')
        def __init__(self, client_addr):
            self.client_socket = None
            
            self.BUFSIZ = 1024
            self.addSocket(client_addr)

        def addSocket(self, client_addr):
            HOST, PORT = client_addr.split(":")
            PORT = int(PORT)
            ADDR = (HOST, PORT)
            self.client_socket = socket(AF_INET, SOCK_STREAM)
            self.client_socket.connect(ADDR)

            Thread(target=self.send).start()
            receive_thread = Thread(target=self.receive)
            receive_thread.start()

    def __init__(self, server_addr, client_addr):
        server = Node.Server(server_addr)
        print("server started")
        client = Node.Client(client_addr)
        print("client started")


server_addr = input("server address (where this server listens): ")

client_addr = input("client address (where this client will send to/recieve from): ")
# connect first client to its own server
if client_addr == "":
    client_addr = server_addr

node = Node(server_addr, client_addr)


