# ZeroMQ Imports
import zmq

# Local Imports
import settings
from keyvaluemsg import KeyValueMsg


class ServerSocket(object):
    """
    Base class for sockets at the server.
    """
    def __init__(self, socket, endpoint):
        self.socket = socket
        self.endpoint = endpoint

    def run(self):
        """
        Initiates the socket by binding to self.endpoint;
        Recommended: Override in sub-class.
        """
        self.socket.bind(self.endpoint)


class ApplicationHandler(ServerSocket):
    """
    zmq.ROUTER socket.
    Used for handling application requests/updates from zmq.DEALER socket at
    the Application end and for sending new updates to the Application end.
    """
    def __init__(self, endpoint, context):
        ServerSocket.__init__(self, context.socket(zmq.ROUTER), endpoint)
        self.socket.setsockopt(zmq.RCVTIMEO, 1000)

    def run(self):
        """
        Overrides Serversocket.run() method.
        """
        ServerSocket.run(self)


class ClientHandler(ServerSocket):
    """
    zmq.ROUTER socket.
    Used for handling client requests/updates from zmq.DEALER socket at the
    Client end and for sending updates to slow-joiners.
    """
    def __init__(self, endpoint, context):
        ServerSocket.__init__(self, context.socket(zmq.ROUTER), endpoint)
        self.socket.setsockopt(zmq.RCVTIMEO, 1000)

    def run(self):
        """
        Overridden method from ServerSocket base class.
        """
        ServerSocket.run(self)


class Publisher(ServerSocket):
    """
    zmq.PUB socket.
    Used for publishing a new update to all subscribed clients through a zmq.SUB
    socket on the other side.
    """
    def __init__(self, endpoint, context):
        ServerSocket.__init__(self, context.socket(zmq.PUB), endpoint)

    def run(self):
        """
        Overridden method from ServerSocket base class.
        """
        ServerSocket.run(self)

    def send(self, kvmsg):
        """
        Send updates via zmq.PUB socket.
        :param kvmsg: KeyValueMsg instance.
        """
        assert(isinstance(kvmsg, KeyValueMsg))
        self.socket.send_multipart([ kvmsg.key, kvmsg.body ])


class Server(object):
    """
    Server Instance. Uses Router and Publisher instances.
    """
    def __init__(self, endpoint_backend, endpoint_frontend, endpoint_publisher):
        self.context = zmq.Context()
        self.frontend = ClientHandler(endpoint_frontend, self.context)
        self.backend = ApplicationHandler(endpoint_backend, self.context)
        self.publisher = Publisher(endpoint_publisher, self.context)
        
    def start(self):
        """
        Method to start the server.
        """
        # Start Router frontend, backend and Publisher instances.
        self.frontend.run()
        self.backend.run()
        self.publisher.run()

        # Register Pollers.
        poll = zmq.Poller()
        poll.register(self.backend.socket, zmq.POLLIN)
        poll.register(self.frontend.socket, zmq.POLLIN)

        while True:
            sockets = dict(poll.poll(1000))
            # If there are incoming messages.
            if sockets.get(self.backend.socket) == zmq.POLLIN:
                connection_id = self.backend.socket.recv()
                msg = self.backend.socket.recv()
                print "Application: ", msg

                self.backend.socket.send(connection_id, zmq.SNDMORE)
                self.backend.socket.send("Reply to: %s" % (msg))

            if sockets.get(self.frontend.socket) == zmq.POLLIN:
                connection_id = self.frontend.socket.recv()
                msg = self.frontend.socket.recv()
                print "Client: ", msg
                # Send Some reply here or transfer control to
                # application logic.
                # Replying with random messages for now.
                import random
                self.frontend.socket.send(connection_id, zmq.SNDMORE)
                self.frontend.socket.send("Client: Random Response %d" %
                                        (random.randint(1, 100)))

            else:
                print "Now sending via PUB.."
                # Should be converted to a poll to see application logic
                # has any new updates or not.
                kvmsg = KeyValueMsg(b"A", b"Hello World!")
                self.publisher.send(kvmsg)

    def stop(self):
        """
        Method to stop the server and make a clean exit.
        """
        # First Disconnect Clients then Application.
        self.frontend.socket.close()
        self.publisher.socket.close()
        self.backend.socket.close()
        self.context.term()
        self.frontend = None
        self.context = None


if __name__ == "__main__":
    server = Server(settings.ENDPOINT_APPLICATION_HANDLER,
                    settings.ENDPOINT_CLIENT_HANDLER,
                    settings.ENDPOINT_PUBLISHER)
    server.start()

