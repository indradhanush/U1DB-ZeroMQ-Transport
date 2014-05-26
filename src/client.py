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
        self.socket.connect(self.endpoint)


class Dealer(ClientSocket):
    """
    zmq.DEALER socket.
    Used for sending requests/updates to zmq.ROUTER socket on the server side.
    """
    def __init__(self, endpoint, context):
        self.socket = context.socket(zmq.DEALER)
        super(Dealer, self).__init__(self.socket, endpoint)

    def run(self):
        super(Dealer, self).run()


class Subscriber(ClientSocket):
    """
    zmq.SUB socket.
    Used for receiving updates from server through a zmq.PUB socket on the
    server side.
    """
    def __init__(self, endpoint, context):
        self.socket = context.socket(zmq.SUB)
        super(Subscriber, self).__init__(self.socket, endpoint)

    def run(self):
        super(Subscriber, self).run()

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


class Client():
    """
    Client Instance. Uses zmq.DEALER socket.
    """
    def __init__(self, endpoint_router, endpoint_pub):
        self.context = zmq.Context()
        self.dealer = Dealer(endpoint_router, self.context)
        self.sub = Subscriber(endpoint_pub, self.context)

    def run(self):
        # Start Dealer and Subscriber instances.
        self.dealer.run()
        self.sub.run()
        self.sub.subscribe(b"A")
        # ZMQ Event Poller
        poll = zmq.Poller()
        poll.register(self.dealer.socket, zmq.POLLIN)

        for i in xrange(10):
            # Simulating different requests for now. Will be removed.
            import random
            self.dealer.socket.send("Test Request %d." % (i+1))
        print "Requests sent."

        while True:
            sockets = dict(poll.poll(1000))
            # If there are incoming messages.
            if sockets.get(self.dealer.socket) == zmq.POLLIN:
                print self.dealer.socket.recv()
            try:
                msg = self.sub.recv()
                self.sub.unsubscribe(b"A")
            except:
                continue # Interrupted or Timeout
            if msg:
                print msg

    def tearDown(self):
        self.dealer.socket.close()
        self.sub.socket.close()
        self.context.term()
        self.dealer = None
        self.context = None


if __name__ == "__main__":
    client = Client(settings.ENDPOINT_ROUTER, settings.ENDPOINT_PUB)
    client.run()

