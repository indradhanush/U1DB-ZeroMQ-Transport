from zmq_transport.app.zmq_app import ZMQApp
from zmq_transport.config.settings import ENDPOINT_APPLICATION_HANDLER


if __name__ == "__main__":
    application = ZMQApp(ENDPOINT_APPLICATION_HANDLER)
    application.start()




