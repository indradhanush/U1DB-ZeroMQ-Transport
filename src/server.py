# ZeroMQ Imports
import zmq

# Local Imports
import settings


class Server():
    """
    Server Instance. Uses zmq.ROUTER socket in the frontend.
    """
    def __init__(self, endpoint):
        self.endpoint = endpoint
        self.context = zmq.Context()
        self.frontend = None
        self.backend = None
        
    def run(self):
        self.frontend = self.context.socket(zmq.ROUTER)
        self.frontend.bind(self.endpoint)
        
        poll = zmq.Poller()
        poll.register(self.frontend, zmq.POLLIN)
        
        while True:
            sockets = dict(poll.poll())
            # If there are incoming messages.
            if sockets.get(self.frontend) == zmq.POLLIN:
                connection_id = self.frontend.recv()
                msg = self.frontend.recv()
                print msg
                # Send Some reply here.
                import random
                self.frontend.send(connection_id, zmq.SNDMORE)
                self.frontend.send("Some Response %d" % (random.randint(1, 10)))

    def tearDown(self):
        self.frontend.close()
        self.context.term()
        self.frontend = None
        self.context = None


if __name__ == "__main__":
    server = Server(settings.ENDPOINT)
    server.run()

