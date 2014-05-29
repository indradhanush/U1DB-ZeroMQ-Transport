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
    def __init__(self, endpoint_application_handler, endpoint_client_handler,
                 endpoint_publisher):
        self.context = zmq.Context()
        self.application_handler = ApplicationHandler(endpoint_application_handler,
                                                      self.context)
        self.client_handler = ClientHandler(endpoint_client_handler,
                                            self.context)
        self.publisher = Publisher(endpoint_publisher, self.context)
        
    def run(self):
        """
        Method to start the server.
        """
        # Start Router and Publisher instances.
        self.client_handler.run()
        self.publisher.run()

        poll = zmq.Poller()
        poll.register(self.client_handler.socket, zmq.POLLIN)

        while True:
            sockets = dict(poll.poll(1000))
            # If there are incoming messages.
            # if self.application_handler.socket in sockets:
            if sockets.get(self.application_handler.socket) == zmq.POLLIN:
                msg = self.application_handler.socket.recv_multipart()
                print msg

            if sockets.get(self.client_handler.socket) == zmq.POLLIN:
                connection_id = self.client_handler.socket.recv()
                msg = self.client_handler.socket.recv()
                print msg
                # Send Some reply here or transfer control to
                # application logic.
                # Replying with random messages for now.
                import random
                self.client_handler.socket.send(connection_id, zmq.SNDMORE)
                self.client_handler.socket.send("Random Response %d" %
                                        (random.randint(1, 100)))

            # else:
            #     print "Now sending via PUB.."
            #     # Should be converted to a poll to see application logic
            #     # has any new updates or not.
            #     kvmsg = KeyValueMsg(b"A", b"Hello World!")
            #     self.publisher.send(kvmsg)

    def tearDown(self):
        """
        Method to stop the server and make a clean exit.
        """
        # First Disconnect Clients then Application.
        self.client_handler.socket.close()
        self.publisher.socket.close()
        self.application_handler.socket.close()
        self.context.term()
        self.client_handler = None
        self.context = None


if __name__ == "__main__":
    server = Server(settings.ENDPOINT_APPLICATION_HANDLER,
                    settings.ENDPOINT_CLIENT_HANDLER,
                    settings.ENDPOINT_PUBLISHER)
    server.run()

