# ZeroMQ Imports
import zmq

# Local Imports
import settings


class Client():
    """
    Client Instance. Uses zmq.DEALER socket.
    """
    def __init__(self, endpoint):
        self.endpoint = endpoint
        self.context = zmq.Context()
        self.frontend = None
        self.backend = None

    def run(self):
        self.frontend = self.context.socket(zmq.DEALER)
        self.frontend.connect(self.endpoint)

        poll = zmq.Poller()
        poll.register(self.frontend, zmq.POLLIN )

        for i in xrange(10):
            # Simulating different requests for now. Will be removed.
            import random
            self.frontend.send("Some request %d." % (random.randint(1, 10)))
        
        while True:
            sockets = dict(poll.poll(1000))
            # If there are incoming messages.
            if sockets.get(self.frontend) == zmq.POLLIN:
                print self.frontend.recv()
            
    def tearDown(self):
        self.frontend.close()
        self.context.term()
        self.frontend = None
        self.context = None


if __name__ == "__main__":
    client = Client(settings.ENDPOINT)
    client.run()

