# ZeroMQ Imports
import zmq
from zmq.eventloop.zmqstream import ZMQStream
from zmq.eventloop.ioloop import IOLoop, PeriodicCallback

# Local Imports
from zmq_transport.config import settings
from zmq_transport.common.message import KeyValueMsg


class ServerSocket(object):
    """
    Base class for sockets at the server.
    """
    def __init__(self, socket, endpoint):
        self.socket = socket
        self.endpoint = endpoint

    def run(self):
        """
        Initiates the socket by binding to self.endpoint;
        Recommended: Override in sub-class.
        """
        self.socket.bind(self.endpoint)


class ApplicationHandler(ServerSocket):
    """
    zmq.ROUTER socket.
    Used for handling application requests/updates from zmq.DEALER socket at
    the Application end and for sending new updates to the Application end.
    """
    def __init__(self, endpoint, context):
        ServerSocket.__init__(self, context.socket(zmq.ROUTER), endpoint)
        self.socket.setsockopt(zmq.RCVTIMEO, 1000)

    def run(self):
        """
        Overrides Serversocket.run() method.
        """
        ServerSocket.run(self)


class ClientHandler(ServerSocket):
    """
    zmq.ROUTER socket.
    Used for handling client requests/updates from zmq.DEALER socket at the
    Client end and for sending updates to slow-joiners.
    """
    def __init__(self, endpoint, context):
        ServerSocket.__init__(self, context.socket(zmq.ROUTER), endpoint)
        self.socket.setsockopt(zmq.RCVTIMEO, 1000)

    def run(self):
        """
        Overridden method from ServerSocket base class.
        """
        ServerSocket.run(self)


class Publisher(ServerSocket):
    """
    zmq.PUB socket.
    Used for publishing a new update to all subscribed clients through a zmq.SUB
    socket on the other side.
    """
    def __init__(self, endpoint, context):
        ServerSocket.__init__(self, context.socket(zmq.PUB), endpoint)

    def run(self):
        """
        Overridden method from ServerSocket base class.
        """
        ServerSocket.run(self)

    def send(self, kvmsg):
        """
        Send updates via zmq.PUB socket.
        :param kvmsg: KeyValueMsg instance.
        """
        assert(isinstance(kvmsg, KeyValueMsg))
        self.socket.send_multipart([ kvmsg.key, kvmsg.body ])


class Server(object):
    """
    Server Instance. Uses Router and Publisher instances.
    """
    def __init__(self, endpoint_backend, endpoint_frontend, endpoint_publisher):
        """
        :param endpoint_backend: Endpoint of ROUTER socket facing Application.
        :type endpoint_: str
        :param endpoint_: Endpoint of ROUTER socekt facing Client.
        :type endpoint_: str
        :param endpoint_: Endpoint of PUB socket facing Client.
        :type endpoint_: str
        """

        self.context = zmq.Context()
        self.frontend = ClientHandler(endpoint_frontend, self.context)
        self.backend = ApplicationHandler(endpoint_backend, self.context)
        self.publisher = Publisher(endpoint_publisher, self.context)
        self.dataset = []
        self.loop = IOLoop.instance()

        # Wrapping zmq sockets in ZMQStream for IOLoop handlers.
        self.frontend.socket = ZMQStream(self.frontend.socket)
        self.backend.socket = ZMQStream(self.backend.socket)
        self.publisher.socket = ZMQStream(self.publisher.socket)

        # Registering callback handlers.
        self.frontend.socket.on_send(self.handle_snd_update_client)
        self.frontend.socket.on_recv(self.handle_rcv_update_client)
        self.publisher.socket.on_send(self.handle_snd_update_client)
        self.backend.socket.on_send(self.handle_snd_update_app)
        self.backend.socket.on_recv(self.handle_rcv_update_app)

    def start(self):
        """
        Method to start the server.
        """
        # Start Router frontend, backend and Publisher instances.
        self.frontend.run()
        self.backend.run()
        self.publisher.run()

        try:
            self.loop.start()
        except KeyboardInterrupt:
            print "<SERVER> Interrupted."

    ########################## Start of callbacks. ############################

    def handle_snd_update_client(self, msg, status):
        """
        Callback function to handle application logic on sending
        updates/requests to clients via both ROUTER and PUB sockets.

        :param msg: Raw/Serialized message that was sent.
        :type msg: list
        :param status: return result of socket.send_multipart(msg)
        :type status: MessageTracker or None ; See: http://zeromq.github.io/pyzmq/api/generated/zmq.eventloop.zmqstream.html#zmq.eventloop.zmqstream.ZMQStream.on_send
        """
        print "<SERVER> Sent_to_Client: ", msg[1]

    def handle_rcv_update_client(self, msg):
        """
        Callback to handle incoming updates on ROUTER socket from clients.
        :param msg: Raw Message received.
        :type msg: list
        """
        print msg
        connection_id, msg = msg
        print "<SERVER> Received_from_Client: ", msg
        self.frontend.socket.send_multipart([connection_id, "PING-OK"])

    def handle_snd_update_app(self, msg, status):
        """
        Callback function to handle application logic on sending
        updates/requests to application via DEALER socket.

        :param msg: Raw/Serialized message that was sent.
        :type msg: list
        :param status: return result of socket.send_multipart(msg)
        :type status: MessageTracker or None ; See: http://zeromq.github.io/pyzmq/api/generated/zmq.eventloop.zmqstream.html#zmq.eventloop.zmqstream.ZMQStream.on_send
        """
        print "<SERVER> Sent_to_App: ", msg

    def handle_rcv_update_app(self, msg):
        """
        Callback to handle incoming updates on ROUTER socket from application.
        :param msg: Raw Message received.
        :type: list
        """
        print "<SERVER> Received_from_App: ", msg
        connection_id, msg = msg
        self.backend.socket.send_multipart([connection_id, "PING-APP-OK"])

    ########################### End of callbacks. #############################

    def stop(self):
        """
        Method to stop the server and make a clean exit.
        """
        # First Disconnect Clients then Application.
        self.frontend.socket.close()
        self.publisher.socket.close()
        self.backend.socket.close()
        self.context.term()
        self.frontend = None
        self.context = None

