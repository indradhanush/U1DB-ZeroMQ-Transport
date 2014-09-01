# Dependencies' imports
from wsgiref import simple_server

from zmq_transport.app.zmq_app import ZMQApp
from zmq_transport.config.settings import PROJECT_ROOT, DATABASE_ROOT
from u1db.remote import server_state

if __name__ == "__main__":
    state = server_state.ServerState()
    state.set_workingdir(DATABASE_ROOT)
    application = ZMQApp(state)
    application.start()
