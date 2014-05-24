# ZeroMQ Imports
import zmq

# Local Imports
import settings


class Router():
    """
    zmq.ROUTER socket.
    Used for handling client requests/updates from zmq.DEALER socket on the
    other side.
    """
    def __init__(self, endpoint, context):
        self.socket = context.socket(zmq.ROUTER)
        self.endpoint = endpoint

    def run(self):
        self.socket.bind(self.endpoint)


class Publisher():
    """
    zmq.PUB socket.
    Used for publishing a new update to all subscribed clients through a zmq.SUB
    socket on the other side.
    """
    def __init__(self, endpoint, context):
        self.socket = context.socket(zmq.PUB)
        self.endpoint = endpoint

    def run(self):
        self.socket.bind(self.endpoint)


class Server():
    """
    Server Instance. Uses Router and Publisher instances.
    """
    def __init__(self, endpoint_router, endpoint_pub):
        self.context = zmq.Context()
        self.router = Router(endpoint_router, self.context)
        self.pub = Publisher(endpoint_pub, self.context)
        
    def run(self):
        # Initialize Router and Publisher Instances.
        self.router.run()
        self.pub.run()

        poll = zmq.Poller()
        poll.register(self.router.socket, zmq.POLLIN)

        while True:
            sockets = dict(poll.poll())
            # If there are incoming messages.
            if sockets.get(self.router.socket) == zmq.POLLIN:
                connection_id = self.router.socket.recv()
                msg = self.router.socket.recv()
                print msg
                # Send Some reply here.
                import random
                self.router.socket.send(connection_id, zmq.SNDMORE)
                self.router.socket.send("Some Response %d" % (random.randint(1, 10)))

    def tearDown(self):
        self.router.socket.close()
        self.pub.socket.close()
        self.context.term()
        self.router = None
        self.context = None


if __name__ == "__main__":
    server = Server(settings.ENDPOINT_ROUTER, settings.ENDPOINT_PUB)
    server.run()

