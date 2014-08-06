"""
ZeroMQ Server.
"""
# ZeroMQ Imports
import zmq
from zmq.eventloop.zmqstream import ZMQStream
from zmq.eventloop.ioloop import IOLoop, PeriodicCallback

# Protobuf Imports
from google.protobuf.message import DecodeError

# Local Imports
from zmq_transport.config import settings
from zmq_transport.config.protobuf_settings import (
    MSG_TYPE_PING,
    MSG_TYPE_SYNC_TYPE,
    MSG_TYPE_ZMQ_VERB,
    MSG_TYPE_GET_SYNC_INFO_REQUEST,
    MSG_TYPE_SEND_DOCUMENT_REQUEST,
    MSG_TYPE_ALL_SENT_REQUEST,
    MSG_TYPE_GET_DOCUMENT_REQUEST,
    MSG_TYPE_PUT_SYNC_INFO_REQUEST
)
from zmq_transport.common.zmq_base import ZMQBaseSocket, ZMQBaseComponent
from zmq_transport.common import message_pb2 as proto
from zmq_transport.common.utils import (
    serialize_msg,
    deserialize_msg,
    create_get_sync_info_response_msg,
    create_put_sync_info_response_msg,
    create_send_document_response_msg,
    create_get_document_response_msg,
    create_all_sent_response_msg,
    create_client_info_msg,
)
from zmq_transport.common.errors import ConnectionIDNotSet


class ServerSocket(ZMQBaseSocket):
    """
    Base class for sockets at the server. Derived from ZMQBaseSocket.
    """
    def __init__(self, socket, endpoint):
        """
        Initialize a ServerSocket instance. Derived from ZMQBaseSocket.

        :param socket: ZeroMQ socket.
        :type socket: zmq.Context.socket
        :param endpoint: Endpoint of socket to which it will connect or bind.
        :type endpoint: str
        """
        ZMQBaseSocket.__init__(self, socket, endpoint)

    def run(self):
        """
        Initiates the socket by binding to self._endpoint;
        """
        self._socket.bind(self._endpoint)


class ApplicationHandler(ServerSocket):
    """
    zmq.ROUTER socket.
    Used for handling application requests/updates from zmq.DEALER socket at
    the Application end and for sending new updates to the Application end.
    """
    def __init__(self, endpoint, context):
        """
        Initialize an ApplicationHandler instance.

        :param endpoint: Endpoint of socket to which it will connect or bind.
        :type endpoint: str
        :param context: ZeroMQ context.
        :type context: zmq.Context
        """
        ServerSocket.__init__(self, context.socket(zmq.ROUTER), endpoint)
        self._socket.setsockopt(zmq.RCVTIMEO, 1000)
        self._connection_id = None

    def set_connection_id(self, connection_id, force_update=False):
        """
        Sets the connection_id of the ZMQApp DEALER socket.

        :param connection_id: Unique connection id of the connection.
        :type connection_id: str
        :param force_update: Flag to force update connection id.
        """
        if not self._connection_id or force_update:
            self._connection_id = connection_id

    def get_connection_id(self):
        """
        Returns the connection_id of the associated ZMQApp DEALER socket.

        :return: connection_id
        :rtype: str
        """
        return self._connection_id

    def send(self, msg):
        """
        Overridden method of zmq_transport.common.zmq_base.ZMQBaseSocket
        to insert connection_id before sending a message to ZMQApp.
        Raises ConnectionIDNotSet if self._connection_id is None.

        :param msg: Message to be sent.
        :type msg: str or list
        """
        connection_id = self.get_connection_id()
        if not connection_id:
            raise ConnectionIDNotSet
        if isinstance(msg, list):
            msg.insert(0, connection_id)
        else:
            msg = [connection_id, msg]

        # Frame 1: ZMQApp Connection ID, Frame 2: ClientInfo, Frame3: msg
        ServerSocket.send(self, msg)


class ClientHandler(ServerSocket):
    """
    zmq.ROUTER socket.
    Used for handling client requests/updates from zmq.DEALER socket at the
    Client end and for sending updates to slow-joiners.
    """
    def __init__(self, endpoint, context):
        """
        Initialize an ClientHandler instance.

        :param endpoint: Endpoint of socket to which it will connect or bind.
        :type endpoint: str
        :param context: ZeroMQ context.
        :type context: zmq.Context
        """
        ServerSocket.__init__(self, context.socket(zmq.ROUTER), endpoint)
        self._socket.setsockopt(zmq.RCVTIMEO, 1000)


class Publisher(ServerSocket):
    """
    zmq.PUB socket.
    Used for publishing a new update to all subscribed clients through a zmq.SUB
    socket on the other side.
    """
    def __init__(self, endpoint, context):
        """
        Initialize an Publisher instance.

        :param endpoint: Endpoint of socket to which it will connect or bind.
        :type endpoint: str
        :param context: ZeroMQ context.
        :type context: zmq.Context
        """
        ServerSocket.__init__(self, context.socket(zmq.PUB), endpoint)


class Server(ZMQBaseComponent):
    """
    Server Instance. Uses Router and Publisher instances.
    """
    def __init__(self, endpoint_backend, endpoint_frontend, endpoint_publisher):
        """
        Initiates a Server instance. Derived from ZMQBaseComponent.

        :param endpoint_backend: Endpoint of ROUTER socket facing Application.
        :type endpoint_backend: str
        :param endpoint_frontend: Endpoint of ROUTER socket facing Client.
        :type endpoint_frontend: str
        :param endpoint_publisher: Endpoint of PUB socket facing Client.
        :type endpoint_publisher: str
        """
        ZMQBaseComponent.__init__(self)
        self.frontend = ClientHandler(endpoint_frontend, self._context)
        self.backend = ApplicationHandler(endpoint_backend, self._context)
        self.publisher = Publisher(endpoint_publisher, self._context)

    def _prepare_reactor(self):
        """
        Prepares the reactor by instantiating the reactor loop, wrapping sockets
        over ZMQStream and registering handlers.
        """
        self._loop = IOLoop.instance()
        self.frontend.wrap_zmqstream()
        self.publisher.wrap_zmqstream()
        self.backend.wrap_zmqstream()
        self.frontend.register_handler("on_send", self.handle_snd_update_client)
        self.frontend.register_handler("on_recv", self.handle_rcv_update_client)
        self.publisher.register_handler("on_send",
                                        self.handle_snd_update_client)
        self.backend.register_handler("on_send", self.handle_snd_update_app)
        self.backend.register_handler("on_recv", self.handle_rcv_update_app)

    def start(self):
        """
        Method to start the server.
        """
        # Start Router frontend, backend and Publisher instances.
        self._prepare_reactor()
        self.frontend.run()
        self.backend.run()
        self.publisher.run()
        try:
            self._loop.start()
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
        :type status: MessageTracker or None ;
                      See: http://zeromq.github.io/pyzmq/api/generated/\
                      zmq.eventloop.zmqstream.html#zmq.eventloop.zmqstream.\
                      ZMQStream.on_send
        """
        pass

    def handle_rcv_update_client(self, msg):
        """
        Callback to handle incoming updates on ROUTER socket from clients.
        :param msg: Raw Message received.
        :type msg: list
        """
        # Message Format: [connection_id, request_id, delimiter_frame, msg]
        # msg: [ZMQVerb, SyncType, Identifier(Action Message)]
        # Note: msg becomes a list after unpacking. Before that, they
        # are all elements of the original msg list.

        client_id, request_id, _, msg = msg[0], msg[1], msg[2], msg[3:]

        # TODO: Store the client_id and request_id in a hash table
        # maybe instead of sending both client_id and request_id. Just
        # send the request_id and match it up when it comes back from
        # tha hash table.n
        client_info_struct = create_client_info_msg(
            client_id=client_id, request_id=request_id)

        str_client_info = serialize_msg(client_info_struct)
        to_send = [str_client_info]
        to_send.extend(msg)
        self.backend.send(to_send)

    def handle_snd_update_app(self, msg, status):
        """
        Callback function to handle application logic on sending
        updates/requests to application via DEALER socket.

        :param msg: Raw/Serialized message that was sent.
        :type msg: list
        :param status: return result of socket.send_multipart(msg)
        :type status: MessageTracker or None ; See: http://zeromq.github.io/pyzmq/api/generated/zmq.eventloop.zmqstream.html#zmq.eventloop.zmqstream.ZMQStream.on_send
        """
        pass

    def handle_rcv_update_app(self, msg):
        """
        Callback to handle incoming updates on ROUTER socket from application.
        :param msg: Raw Message received.
        :type msg: list
        """
        connection_id, msg = msg[0], msg[1:]

        if len(msg) == 1:
            # Probably a PING message.
            iden_struct = deserialize_msg("Identifier", msg[0])
            if iden_struct.type == MSG_TYPE_PING:
                self.backend.set_connection_id(connection_id)
        elif len(msg) == 2:
            str_client_info, update_str = msg
            client_info_struct = deserialize_msg("ClientInfo", str_client_info)
            to_send = [client_info_struct.client_id,
                       client_info_struct.request_id, "", update_str]

            self.frontend.send(to_send)

    # def check_to_app(self):
    #     # Check to see if Application Tier is online.
    #     if not self.backend.get_connection_id():
    #         return
    #     while not self.to_app.empty():
    #         data = self.to_app.get()
    #         self.backend.send(data)

    # def check_to_client(self):
    #     # TODO: Check to see if the particulat client is online. Else
    #     # move to next data in Queue. However, might have to implement
    #     # a custom queue for this ourselves.
    #     while not self.to_client.empty():
    #         data = self.to_client.get()
    #         self.frontend.send(data)

    ###################### End of callbacks. #########################

    def stop(self):
        """
        Method to stop the server and make a clean exit.
        """
        # TODO: First complete any pending tasks in self.dataset and
        # send "TERM" signal to connected components. On receiving a
        # "TERM", components must stop sending.

        # First Disconnect Clients then Application.
        self._loop.stop()
        self.frontend.close()
        self.publisher.close()
        self.backend.close()
        self._context.destroy()
        self.frontend = None
        self._context = None

