from zmq_transport.application.zmq_application import Application
from zmq_transport.config.settings import ENDPOINT_APPLICATION_HANDLER


if __name__ == "__main__":
    application = Application(ENDPOINT_APPLICATION_HANDLER)
    application.start()




