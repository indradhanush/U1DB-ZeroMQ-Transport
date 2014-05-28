# ZeroMQ Imports
import zmq

# Local Imports
import settings
from keyvaluemsg import KeyValueMsg


class SoledadSocket(object):
    """
    Base class for sockets at SOLEDAD.
    """
    def __init__(self, socket, endpoint):
        self.socket = socket
        self.endpoint = endpoint

    def run(self):
        pass

# TODO: zmq.DEALER socket for now. Maybe a PUSH/PULL combo later on. 
# See: IRC logs: http://bit.ly/1tczZJC
# TODO: Or a ROUTER/DEALER combo. 
# See: IRC logs: http://bit.ly/1ijJxNJ
class Dealer(SoledadSocket):
    """
    zmq.DEALER socket.
    Used for handling data from Application Logic to send to zmq.PUB socket
    at the server.
    """
    def __init__(self, endpoint, context):
        SoledadSocket.__init__(self, context.socket(zmq.DEALER), endpoint)
        
    def run(self):
        self.socket.connect(self.endpoint)


def simulator(socket, n):
    """Simulates updates to Publisher. For testing purposes."""
    from random import randint
    key = b"TEST"

    for i in xrange(n):
        request_string = b"Random Update from SOLEDAD side DEALER %d." % (randint(1, 100))
        socket.send_multipart([key, request_string])
        
    print "Updates Sent."


def main():
    context = zmq.Context()
    updates = Dealer(settings.ENDPOINT_PUB, context)
    updates.run()
    simulator(updates.socket, 5)


if __name__ == "__main__":
    main()

