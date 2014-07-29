import os
import time

import u1db

from reset_env import BASE_DB_PATH

if __name__ == "__main__":
    source_db = u1db.open(os.path.join(BASE_DB_PATH, "source-USER-1.u1db"),
                                       False)
    target_db = u1db.open(os.path.join(BASE_DB_PATH, "user-USER-1.u1db"),
                                       False)
    sync_target = target_db.get_sync_target()
    synchronizer = u1db.sync.Synchronizer(source_db, sync_target)

    start = time.time()
    synchronizer.sync()
    print "Total time: ", time.time() - start
