# ZeroMQ Imports
import zmq

# Local Imports
import settings
from keyvaluemsg import KeyValueMsg


class ClientSocket(object):
    """
    Base class for sockets at the client.
    """
    def __init__(self, socket, endpoint):
        self.socket = socket
        self.socket.setsockopt(zmq.RCVTIMEO, 10)
        self.endpoint = endpoint

    def run(self):
        """
        Initiates the socket connection to the server at self.endpoint;
        Recommended: Override in sub-class.
        """
        self.socket.connect(self.endpoint)


class Speaker(ClientSocket):
    """
    zmq.DEALER socket.
    Used for sending requests/updates to zmq.ROUTER socket on the server side.
    This is the only component in the client that speaks to the Server.Others
    just listen.
    """
    def __init__(self, endpoint, context):
        ClientSocket.__init__(self, context.socket(zmq.DEALER), endpoint)

    def run(self):
        """
        Overridden method from ClientSocket base class.
        """
        ClientSocket.run(self)


class Subscriber(ClientSocket):
    """
    zmq.SUB socket.
    Used for receiving updates from server through a zmq.PUB socket on the
    server side.
    """
    def __init__(self, endpoint, context):
        ClientSocket.__init__(self, context.socket(zmq.SUB), endpoint)

    def run(self):
        """
        Overridden method from ClientSocket base class.
        """
        ClientSocket.run(self)

    def subscribe(self, msg_type=b''):
        """
        Subscribes the client to msg_type.

        :param msg_type: <type: binary string> <default: b''> - Type of message
        to subscribe to.
        """
        self.socket.setsockopt(zmq.SUBSCRIBE, b"%s" % (msg_type))

    def unsubscribe(self, msg_type):
        """
        Unsubscribes the client from msg_type.

        :param msg_type: <type: binary string> - Type of message to subscribe to.
        """
        self.socket.setsockopt(zmq.UNSUBSCRIBE, msg_type)

    def recv(self):
        """
        Receive Updates from zmq.PUB socket.
        """
        return self.socket.recv_multipart()


class Client(object):
    """
    Client Instance. Uses zmq.DEALER socket.
    """
    def __init__(self, endpoint_client_handler, endpoint_publisher):
        self.context = zmq.Context()
        self.speaker = Speaker(endpoint_client_handler, self.context)
        self.updates = Subscriber(endpoint_publisher, self.context)

    def run(self):
        """
        Method to start the client.
        """
        # Start Dealer and Subscriber instances.
        self.speaker.run()
        self.updates.run()
        self.updates.subscribe(b"A")
        # ZMQ Event Poller
        poll = zmq.Poller()
        poll.register(self.speaker.socket, zmq.POLLIN)

        for i in xrange(10):
            # Simulating different requests for now. Will be removed.
            import random
            self.speaker.socket.send("Test Request %d." % (i+1))
        print "Requests sent."

        while True:
            sockets = dict(poll.poll(1000))
            # If there are incoming messages.
            if sockets.get(self.speaker.socket) == zmq.POLLIN:
                print self.speaker.socket.recv()
            try:
                msg = self.updates.recv()
                # self.updates.unsubscribe(b"A")
            except:
                continue # Interrupted or Timeout
            if msg:
                print msg

    def tearDown(self):
        """
        Method to stop the client and make a clean exit.
        """
        self.speaker.socket.close()
        self.updates.socket.close()
        self.context.term()
        self.speaker = None
        self.context = None


if __name__ == "__main__":
    client = Client(settings.ENDPOINT_CLIENT_HANDLER,
                    settings.ENDPOINT_PUBLISHER)
    client.run()

