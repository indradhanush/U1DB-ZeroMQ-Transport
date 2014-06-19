# ZeroMQ Imports
import zmq
from zmq.eventloop.zmqstream import ZMQStream
from zmq.eventloop.ioloop import IOLoop, PeriodicCallback

# Protobuf Imports
from google.protobuf.message import DecodeError

# Local Imports
from zmq_transport.config import settings
from zmq_transport.common.zmq_base import ZMQBaseSocket, ZMQBaseComponent
from zmq_transport.common import message_pb2 as proto
from zmq_transport.common.utils import serialize_msg, deserialize_msg,\
    get_target_info, get_source_info, create_get_sync_info_response_msg,\
    create_put_sync_info_response_msg

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
        Recommended: Override in sub-class.
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
        """
        Initialize an ClientHandler instance.

        :param endpoint: Endpoint of socket to which it will connect or bind.
        :type endpoint: str
        :param context: ZeroMQ context.
        :type context: zmq.Context
        """
        ServerSocket.__init__(self, context.socket(zmq.ROUTER), endpoint)
        self._socket.setsockopt(zmq.RCVTIMEO, 1000)

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
        """
        Initialize an Publisher instance.

        :param endpoint: Endpoint of socket to which it will connect or bind.
        :type endpoint: str
        :param context: ZeroMQ context.
        :type context: zmq.Context
        """
        ServerSocket.__init__(self, context.socket(zmq.PUB), endpoint)

    def run(self):
        """
        Overridden method from ServerSocket base class.
        """
        ServerSocket.run(self)


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
        self.publisher.register_handler("on_send", self.handle_snd_update_client)
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
        :type status: MessageTracker or None ; See: http://zeromq.github.io/pyzmq/api/generated/zmq.eventloop.zmqstream.html#zmq.eventloop.zmqstream.ZMQStream.on_send
        """
        print "<SERVER> Sent_to_Client: ", msg

    def handle_rcv_update_client(self, msg):
        """
        Callback to handle incoming updates on ROUTER socket from clients.
        :param msg: Raw Message received.
        :type msg: list
        """
        print "<SERVER> Received_from_Client: ", msg
        # Message Format: [connection_id, request_id, delimiter_frame, msg]
        # msg: [ZMQVerb, SyncType, Identifier(Action Message)]
        connection_id, request_id, _, msg = msg[0], msg[1], msg[2], msg[3:]
        response = []

        zmq_verb_str, sync_type_str, iden_str = msg
        # Do something with zmq_verb_str and sync_type_str later.
        try:
            iden_struct = deserialize_msg("Identifier", iden_str)
        except DecodeError:
            # Silently fail.
            return
        else:
            frame_response = identify_msg(iden_struct)
            if frame_response:
                try:
                    response = serialize_msg(frame_response)
                except DecodeError:
                    # Silently fail.
                    return

        to_send = [connection_id, request_id, "", response]
        self.frontend.send(to_send)

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
        :type msg: list
        """
        print "<SERVER> Received_from_App: ", msg
        connection_id, msg = msg
        self.backend.send([connection_id, "PING-APP-OK"])

    ########################### End of callbacks. #############################

    def stop(self):
        """
        Method to stop the server and make a clean exit.
        """
        # TODO: First complete any pending tasks in self.dataset and
        # send "TERM" signal to connected components.

        # First Disconnect Clients then Application.
        self._loop.stop()
        self.frontend.close()
        self.publisher.close()
        self.backend.close()
        self._context.destroy()
        self.frontend = None
        self._context = None
        self.dataset = []


############## Start of Application logic server side utilities. ##############

def identify_msg(iden_struct):
    """
    Identifies the type of message packed in Identifier message structure and
    routes to the specific handler.
    :param iden_struct: Identifier message structure.
    :type iden_struct: zmq_transport.common.message_pb2.Identifier
    """
    if iden_struct.type == 3: # SyncType
        return handle_sync_type(iden_struct.sync_type)
    elif iden_struct.type == 4: # ZMQVerb
        return handle_zmq_verb(iden_struct.zmq_verb)
    elif iden_struct.type == 5: # GetSyncInfoRequest
        return handle_get_sync_info_request(iden_struct.subscribe_request)
    elif iden_struct.type == 7: # SendDocumentRequest
        return handle_send_doc_request(iden_struct.send_document_request)
    elif iden_struct.type == 11: # PutSyncInfoRequest
        return handle_put_sync_info_request(iden_struct.put_sync_info_request)


def handle_sync_type(sync_type_struct):
    pass


def handle_zmq_verb(zmq_verb_struct):
    pass


def handle_get_sync_info_request(get_sync_info_struct):
    """
    Returns a GetSyncInfoResponse message.

    :returns: zmq_transport.common.message_pb2.GetSyncInfoResponse wrapped in a
    zmq_transport.common.message_pb2.Identifier message.
    """
    target_info = get_target_info()
    source_info = get_source_info()

    kwargs = {}
    for key, value in target_info.items():
        kwargs[key] = value

    for key, value in source_info.items():
        kwargs[key] = value

    get_sync_info_struct = create_get_sync_info_response_msg(**kwargs)
    return proto.Identifier(type=proto.Identifier.GET_SYNC_INFO_RESPONSE,
                            get_sync_info_response=get_sync_info_struct)


def handle_send_doc_request(send_doc_req_struct):
    pass


def handle_put_sync_info_request(put_sync_info_struct):
    """
    Returns a PutSyncInfoResponse message.

    :returns: zmq_transport.common.message_pb2.PutSyncInfoResponse wrapped in a
    zmq_transport.common.message_pb2.Identifier message.
    """
    # Do some db transaction here.
    inserted = True
    response_struct = create_put_sync_info_response_msg(
        source_transaction_id=put_sync_info_struct.source_transaction_id,
        inserted=inserted)
    return proto.Identifier(type=proto.Identifier.PUT_SYNC_INFO_RESPONSE,
                            put_sync_info_response=response_struct)

############### End of Application logic server side utilities. ###############

