from zmq_transport.u1db.zmq_target import ZMQSyncTarget
from zmq_transport.config.settings import *

if __name__ == "__main__":
    sync_client = ZMQSyncTarget([ENDPOINT_CLIENT_HANDLER,
                                         ENDPOINT_PUBLISHER])

    sync_client.start()

