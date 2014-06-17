from zmq_transport.client.zmq_client import ZMQClientBase
from zmq_transport.config.settings import *

if __name__ == "__main__":
    client = ZMQClientBase(ENDPOINT_CLIENT_HANDLER,
                    ENDPOINT_PUBLISHER)

