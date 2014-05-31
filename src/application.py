# ZeroMQ Imports
import zmq

# Local Imports
import settings
from keyvaluemsg import KeyValueMsg


class ApplicationSocket(object):
    """
    Base class for sockets at SOLEDAD.
    """
    def __init__(self, socket, endpoint):
        self.socket = socket
        self.endpoint = endpoint

    def run(self):
        """
        Initiates socket connections. Base class implementations must override
        this method.
        """
        pass

# TODO: zmq.DEALER socket for now. Maybe a PUSH/PULL combo later on. 
# See: IRC logs: http://bit.ly/1tczZJC
# TODO: Or a ROUTER/DEALER combo. 
# See: IRC logs: http://bit.ly/1ijJxNJ
class ServerHandler(ApplicationSocket):
    """
    zmq.DEALER socket.
    Used for handling data from Application Logic to send to zmq.PUB socket
    at the server.
    """
    def __init__(self, endpoint, context):
        ApplicationSocket.__init__(self, context.socket(zmq.DEALER), endpoint)
        
    def run(self):
        """
        Overrides ApplicationSocket.run() method.
        """
        self.socket.connect(self.endpoint)

        poll = zmq.Poller()
        poll.register(self.socket, zmq.POLLIN)

        simulator(self.socket, 5)
        while True:
            sockets = dict(poll.poll(1000))
            if sockets.get(self.socket) == zmq.POLLIN:
                msg = self.socket.recv()
                print msg


class Application(object):
    """
    Application instance. Uses a ServerHandler instance.
    """
    def __init__(self, endpoint):
        self.context = zmq.Context()
        self.updates = ServerHandler(endpoint, self.context)

    def run(self):
        self.updates.run()


def simulator(socket, n):
    """Simulates updates to Publisher. For testing purposes."""
    from random import randint
    key = b"TEST"

    for i in xrange(n):
        request_string = b"Random Update from SOLEDAD side DEALER %d." % (randint(1, 100))
        socket.send(request_string)
        # socket.send_multipart([key, request_string])
        
    print "Updates Sent."


def main():
    application = Application(settings.ENDPOINT_APPLICATION_HANDLER)
    application.run()


if __name__ == "__main__":
    main()

