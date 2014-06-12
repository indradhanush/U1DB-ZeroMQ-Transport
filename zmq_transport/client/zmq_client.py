# ZeroMQ Imports
import zmq
from zmq.eventloop.zmqstream import ZMQStream
from zmq.eventloop.ioloop import IOLoop, PeriodicCallback

# Local Imports
from zmq_transport.config import settings
from zmq_transport.common.message import KeyValueMsg
from zmq_transport.common.message import SourceRequestMsg, TargetResponseMsg


class ClientSocket(object):
    """
    Base class for sockets at the client.
    """
    def __init__(self, socket, endpoint):
        self.socket = socket
        self.socket.setsockopt(zmq.RCVTIMEO, 10)
        self.endpoint = endpoint

    def run(self):
        """
        Initiates the socket connection to the server at self.endpoint;
        Recommended: Override in sub-class.
        """
        self.socket.connect(self.endpoint)


class Speaker(ClientSocket):
    """
    zmq.DEALER socket.
    Used for sending requests/updates to zmq.ROUTER socket on the server side.
    This is the only component in the client that speaks to the Server.Others
    just listen.
    """
    def __init__(self, endpoint, context):
        ClientSocket.__init__(self, context.socket(zmq.DEALER), endpoint)

    def run(self):
        """
        Overridden method from ClientSocket base class.
        """
        ClientSocket.run(self)


class Subscriber(ClientSocket):
    """
    zmq.SUB socket.
    Used for receiving updates from server through a zmq.PUB socket on the
    server side.
    """
    def __init__(self, endpoint, context):
        ClientSocket.__init__(self, context.socket(zmq.SUB), endpoint)

    def run(self):
        """
        Overridden method from ClientSocket base class.
        """
        ClientSocket.run(self)

    def subscribe(self, msg_type=b''):
        """
        Subscribes the client to msg_type.

        :param msg_type: <type: binary string> <default: b''> - Type of message
        to subscribe to.
        """
        self.socket.setsockopt(zmq.SUBSCRIBE, b"%s" % (msg_type))

    def unsubscribe(self, msg_type):
        """
        Unsubscribes the client from msg_type.

        :param msg_type: <type: binary string> - Type of message to subscribe to.
        """
        self.socket.setsockopt(zmq.UNSUBSCRIBE, msg_type)

    def recv(self):
        """
        Receive Updates from zmq.PUB socket.
        """
        return self.socket.recv_multipart()


class ZMQClientBase(object):
    """
    Client Instance. Uses zmq.DEALER socket and zmq.SUB socket.
    """
    def __init__(self, endpoint_client_handler, endpoint_publisher):
        """
        Initialize instance of type ZMQClientBase.

        :param endpoint_client_handler: Endpoint of ROUTER socket on Server.
        :type endpoint_client_handler: str
        :param endpoint_publisher: Endpoint of PUB socket on Server.
        :type endpoint_publisher: str
        :returns: zmq_transport.client.ZMQClientBase instance.
        """
        self.context = zmq.Context()
        self.speaker = Speaker(endpoint_client_handler, self.context)
        self.updates = Subscriber(endpoint_publisher, self.context)
        self.dataset = []
        self.loop = IOLoop.instance()

        # Wrapping zmq sockets in ZMQStream for IOLoop handlers.
        self.speaker.socket = ZMQStream(self.speaker.socket)
        self.updates.socket = ZMQStream(self.updates.socket)

        # Registering callback handlers.
        self.speaker.socket.on_send(self.handle_snd_update)
        self.speaker.socket.on_recv(self.handle_rcv_update)
        self.updates.socket.on_recv(self.handle_rcv_update)
        self.check_updates_callback = PeriodicCallback(self.check_updates, 1000)

    def start(self):
        """
        Method to start the client.
        """
        # Start Dealer and Subscriber instances.
        self.speaker.run()
        self.speaker.socket.send("PING")
        self.updates.run()
        self.updates.subscribe(b"A")

        self.check_updates_callback.start()
        try:
            self.loop.start()
        except KeyboardInterrupt:
            print "<CLIENT> Interrupted."

    ########################## Start of callbacks. ############################

    def handle_snd_update(self, msg, status):
        """
        Callback function to make any application level changes after Update/Request has been
        sent via DEALER socket to Server.

        :param msg: Raw/Serialized message that was sent.
        :type msg: list
        :param status: return result of socket.send_multipart(msg)
        :type status: MessageTracker or None ; See: http://zeromq.github.io/pyzmq/api/generated/zmq.eventloop.zmqstream.html#zmq.eventloop.zmqstream.ZMQStream.on_send
        """
        print "<CLIENT> Sent: ", msg[0]

    def handle_rcv_update(self, msg):
        """
        Callback to handle incoming updates both DEALER and SUB sockets.

        :param msg: Raw Message received.
        :type: list
        """
        print "<CLIENT> Received: ", msg[0]
        self.dataset.append(msg[0])

    def check_updates(self):
        """
        Method to regularly check new updates in self.dataset
        """
        if self.dataset:
            for data in self.dataset:
                # TODO: Converting to str now. Will do some
                # serialization with message structures later.
                self.speaker.socket.send_multipart([data])
                self.dataset.remove(data)

    ########################### End of callbacks. #############################

    def stop(sel):
        """
        Method to stop the client and make a clean exit.
        """
        self.speaker.socket.close()
        self.updates.socket.close()
        self.context.term()
        self.speaker = None
        self.context = None

