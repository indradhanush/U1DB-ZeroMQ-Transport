# System imports
import sys
import os.path

# Third party imports
import u1db

# Local imports
from zmq_transport.client.sync import ZMQSynchronizer
from zmq_transport.common.errors import UserIDNotSet
from zmq_transport.config import settings
from zmq_transport.u1db.zmq_target import ZMQSyncTarget


if __name__ == "__main__":
    sync_client = ZMQSyncTarget([
        settings.ENDPOINT_CLIENT_HANDLER, settings.ENDPOINT_PUBLISHER
    ])

    sync_client.set_user_id("USER-1")

    try:
        sync_client.start()
    except UserIDNotSet as e:
        print "Aborting:", e
        sys.exit()

    source = u1db.open(
        os.path.join(settings.DATABASE_ROOT, "source-USER-1.u1db"),
        create=False
    )

    synchronizer = ZMQSynchronizer(source, sync_client)
    import time
    start = time.time()
    source_current_gen = synchronizer.sync()
    end = time.time()
    print "Sync Completed: ", source_current_gen
    print "Total time: ", end - start
