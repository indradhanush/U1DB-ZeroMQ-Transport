from zmq_transport.application.zmq_application import Application
from zmq_transport.config.settings import *


if __name__ == "__main__":
    application = Application(ENDPOINT_APPLICATION_HANDLER)
    application.start()




