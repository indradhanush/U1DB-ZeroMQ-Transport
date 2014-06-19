# ZeroMQ Imports
import zmq
from zmq.eventloop.zmqstream import ZMQStream
from zmq.eventloop.ioloop import IOLoop, PeriodicCallback

# Local Imports
from zmq_transport.config import settings
from zmq_transport.common.zmq_base import ZMQBaseSocket, ZMQBaseComponent
from zmq_transport.common import message_pb2 as proto
from zmq_transport.common.utils import create_subscribe_request_msg, serialize_msg, deserialize_msg


class ClientSocket(ZMQBaseSocket):
    """
    Base class for sockets at the client. Derived from ZMQBaseSocket.
    """
    def __init__(self, socket, endpoint):
        """
        Initialize a ClientSocket instance.

        :param socket: ZeroMQ socket.
        :type socket: zmq.Context.socket
        :param endpoint: Endpoint of socket to which it will connect or bind.
        :type endpoint: str
        """

        ZMQBaseSocket.__init__(self, socket, endpoint)
        # self._socket.setsockopt(zmq.RCVTIMEO, 1000)

    def run(self):
        """
        Initiates the socket connection to the server at self.endpoint;
        """
        self._socket.connect(self._endpoint)


class Speaker(ClientSocket):
    """
    zmq.DEALER socket.
    Used for sending requests/updates to zmq.ROUTER socket on the server side.
    This is the only component in the client that speaks to the Server.Others
    just listen.
    """
    def __init__(self, endpoint, context):
        """
        Initialize an Speaker instance.

        :param endpoint: Endpoint of socket to which it will connect or bind.
        :type endpoint: str
        :param context: ZeroMQ context.
        :type context: zmq.Context
        """
        ClientSocket.__init__(self, context.socket(zmq.REQ), endpoint)
        self._socket.setsockopt(zmq.REQ_CORRELATE, 1)
        self._socket.setsockopt(zmq.REQ_RELAXED, 1)

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
        """
        Initialize an Speaker instance.

        :param endpoint: Endpoint of socket to which it will connect or bind.
        :type endpoint: str
        :param context: ZeroMQ context.
        :type context: zmq.Context
        """
        ClientSocket.__init__(self, context.socket(zmq.SUB), endpoint)

    def run(self):
        """
        Overridden method from ClientSocket base class.
        """
        ClientSocket.run(self)

    def subscribe(self, msg_type):
        """
        Subscribes the client to msg_type.

        :param msg_type: Subscription Message Key
        :type msg_type: str
        """
        msg_struct = create_subscribe_request_msg(key=msg_type)
        str_msg = serialize_msg(msg_struct)
        self._socket.setsockopt(zmq.SUBSCRIBE, str_msg)


    def unsubscribe(self, msg_type):
        """
        Unsubscribes the client from msg_type.

        :param msg_type: <type: binary string> - Type of message to subscribe to.
        """
        msg = serialize_msg("UnsubscribeRequest", key="msg_type")
        self._socket.setsockopt(zmq.UNSUBSCRIBE, msg)

    def recv(self):
        """
        Receive Updates from zmq.PUB socket.
        """
        return self._socket.recv_multipart()


class ZMQClientBase(ZMQBaseComponent):
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
        ZMQBaseComponent.__init__(self)
        self.speaker = Speaker(endpoint_client_handler, self._context)
        self.updates = Subscriber(endpoint_publisher, self._context)

    def _prepare_reactor(self):
        """
        Prepares the reactor by wrapping sockets over ZMQStream and registering
        handlers.
        """
        self._loop = IOLoop.instance()
        self.speaker.wrap_zmqstream()
        self.updates.wrap_zmqstream()
        self.speaker.register_handler("on_send", self.handle_snd_update)
        self.speaker.register_handler("on_recv", self.handle_rcv_update)
        self.updates.register_handler("on_recv", self.handle_pub_update)
        self.check_updates_callback = PeriodicCallback(self.check_updates, 1000)

    def start(self):
        """
        Method to start the client.
        """
        # Start Dealer and Subscriber instances.
        self._prepare_reactor()
        self.speaker.run()
        self.speaker.send(["PING"])
        self.updates.run()
        self.updates.subscribe("USER1")

        self.check_updates_callback.start()
        try:
            self._loop.start()
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
        print "<CLIENT> Sent: ", msg, status

    def handle_rcv_update(self, msg):
        """
        Callback to handle incoming updates both DEALER and SUB sockets.

        :param msg: Raw Message received.
        :type msg: list
        """
        print "<CLIENT> Received: ", msg
        self.dataset.append(msg[0])

    def handle_pub_update(self, msg):
        """
        Callback after updates have been revieved from PUB socket.
        """
        print msg
        key, msg = msg
        subscription = proto.SubscribeRequest()
        subscription.ParseFromString(key)
        print "<PUBLISHER> Key: ", subscription.key, msg

    def check_updates(self):
        """
        Method to regularly check new updates in self.dataset
        """
        if self.dataset:
            for data in self.dataset:
                # TODO: Converting to str now. Will do some
                # serialization with message structures later.
                self.speaker.send([data])
                self.dataset.remove(data)

    ########################### End of callbacks. #############################

    def stop(self):
        """
        Method to stop the client and make a clean exit.
        """
        self.speaker.close()
        self.updates.close()
        self._context.term()
        self.speaker = None
        self._context = None

