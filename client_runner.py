import os.path

import u1db
import leap

from zmq_transport.u1db.zmq_target import ZMQSyncTarget
from zmq_transport.config.settings import (
    ENDPOINT_CLIENT_HANDLER,
    ENDPOINT_PUBLISHER,
    DATABASE_ROOT
)
from zmq_transport.client.sync import ZMQSynchronizer

if __name__ == "__main__":
    import logging
    logging.basicConfig()

    sync_client = ZMQSyncTarget([ENDPOINT_CLIENT_HANDLER,
                                         ENDPOINT_PUBLISHER])

    sync_client.set_user_id("USER-1")
    sync_client.start()

    source = u1db.open(os.path.join(DATABASE_ROOT, "source-USER-1.u1db"), create=False)

    synchronizer = ZMQSynchronizer(source, sync_client)
    source_current_gen = synchronizer.sync()
    print "Sync Completed: ", source_current_gen
