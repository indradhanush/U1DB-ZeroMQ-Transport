from zmq_transport.server.zmq_server import Server
from zmq_transport.config.settings import *

if __name__ == "__main__":
    server = Server(ENDPOINT_APPLICATION_HANDLER,
                    ENDPOINT_CLIENT_HANDLER,
                    ENDPOINT_PUBLISHER)
    server.start()

