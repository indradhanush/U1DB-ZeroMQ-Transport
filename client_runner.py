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


    sync_client = ZMQSyncTarget([ENDPOINT_CLIENT_HANDLER,
                                 ENDPOINT_PUBLISHER])

    sync_client.set_user_id("USER-1")

    try:
        import pdb
        sync_client.start()
    except UserIDNotSet as e:
        print "Aborting:", e
        sys.exit()

    source = u1db.open(
        os.path.join(DATABASE_ROOT, "source-USER-1.u1db"), create=False)

    synchronizer = ZMQSynchronizer(source, sync_client)
    import time
    start = time.time()
    source_current_gen = synchronizer.sync()
    end = time.time()
    print "Sync Completed: ", source_current_gen
    print "Total time: ", end - start
