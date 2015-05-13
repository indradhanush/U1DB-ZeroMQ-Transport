"""
Script to benchmark the reference impelementation.
"""
# System imports
import os
import time
import threading

# Dependencies' imports
import u1db
from u1db.commandline.serve import make_server

# Local imports
from reset_env import BASE_DB_PATH
from zmq_transport.config.settings import DATABASE_ROOT


class ServerThread(threading.Thread):
    """
    Thread to run the http server.
    """
    def __init__(self, host, port, working_dir, accept_cors_connection=None):
        threading.Thread.__init__(self)
        self.server = make_server(host, port, working_dir,
                                  accept_cors_connection)

    def run(self):
        self.server.serve_forever()

    def stop(self):
        if self.isAlive():
            self.server.shutdown()
            self.join()


if __name__ == "__main__":
    server_thread = ServerThread("127.0.0.1", 9999, DATABASE_ROOT)
    server_thread.start()

    source_db = u1db.open(os.path.join(BASE_DB_PATH, "source-USER-1.u1db"),
                                       False)
    start = time.time()
    source_db.sync("http://127.0.0.1:9999/user-USER-1.u1db")
    print "Total time: ", time.time() - start
    server_thread.stop()
