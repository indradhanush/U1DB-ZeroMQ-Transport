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
            if sockets.get(self.frontend):
                connection_id = self.frontend.recv()
                print connection_id
                # Send Some reply here.


if __name__ == "__main__":
    server = Server(settings.ENDPOINT)
    server.run()

