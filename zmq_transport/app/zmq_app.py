"""
Application/Tier 1 Implementation
"""

# ZeroMQ Imports
import zmq
from zmq.eventloop.zmqstream import ZMQStream
from zmq.eventloop.ioloop import IOLoop, PeriodicCallback

# Protobuf Imports
from google.protobuf.message import DecodeError

# Local Imports
from zmq_transport.config.settings import ENDPOINT_APPLICATION_HANDLER
from zmq_transport.common.zmq_base import ZMQBaseSocket, ZMQBaseComponent
from zmq_transport.common import message_pb2 as proto
from zmq_transport.u1db import (
    sync,
    server_state
)
from zmq_transport.common.utils import (
    serialize_msg,
    deserialize_msg,

    create_ping_msg,
    create_get_sync_info_response_msg,
    create_send_document_response_msg,
    create_all_sent_response_msg,
    create_get_document_response_msg,
    create_put_sync_info_response_msg,

    get_target_info,
    get_source_info,
    get_doc_info

)
from zmq_transport.config.protobuf_settings import (
    MSG_TYPE_GET_SYNC_INFO_REQUEST,
    MSG_TYPE_SEND_DOCUMENT_REQUEST,
    MSG_TYPE_ALL_SENT_REQUEST,
    MSG_TYPE_GET_DOCUMENT_REQUEST,
    MSG_TYPE_PUT_SYNC_INFO_REQUEST
)


class SyncResource(object):
    """
    Sync endpoint resource

    Not really an endpoint in the zmq implementation. Maintaining
    similar names for easier follow up.
    """

    sync_exchange_class = sync.SyncExchange

    def __init__(self, dbname, source_replica_uid, state):
        """
        Initiallizes an object of type SyncResource.
        :param dbname: Name of the database
        :type: str
        :param sournce_replica_uid: The replica id of the source
                                   initiating the sync.
        :type: str
        :param state: A ServerState object
        :type: zmq_transport.u1db.server_state.ServerState
        """
        self.dbname = dbname
        self.source_replica_uid = source_replica_uid
        self.state = state
        self.replica_uid = None

    def get_target(self):
        return self.state.open_database(self.dbname).get_sync_target()

    def get(self):
        sync_target = self.get_target()
        result = sync_target.get_sync_info(self.source_replica_uid)
        return {
            TARGET_REPLICA_UID_KEY: result[0],
            TARGET_REPLICA_TRANS_ID_KEY: result[1],
            SOURCE_REPLICA_UID_KEY: result[2],
            SOURCE_LAST_KNOWN_GEN_KEY: result[3],
            SOURCE_LAST_KNOWN_TRANS_ID: result[4]
        }

    def put(self, generation, transaction_id):
        sync_target = self.get_target()
        sync_target.record_sync_info(self.source_replica_uid,
                                     generation,
                                     transaction_id)
        return True

class ZMQAppSocket(ZMQBaseSocket):
    """
    Base class for sockets at SOLEDAD. Derived from ZMQBaseSocket.
    """
    def __init__(self, socket, endpoint):
        """
        Initialize a ZMQAppSocket instance.

        :param socket: ZeroMQ socket.
        :type socket: zmq.Context.socket instance.
        :param endpoint: Endpoint to bind or connect the socket to.
        :type endpoint: str
        """
        ZMQBaseSocket.__init__(self, socket, endpoint)

    def run(self):
        """
        Initiates socket connections. Base class implementations must over
        ride this method.
        """
        raise NotImplementedError(self.run)


# TODO: zmq.DEALER socket for now. Maybe a PUSH/PULL combo later on.
# See: IRC logs: http://bit.ly/1tczZJC
# TODO: Or a ROUTER/DEALER combo.
# See: IRC logs: http://bit.ly/1ijJxNJ
class ServerHandler(ZMQAppSocket):
    """
    zmq.DEALER socket.
    Used for handling data from Application Logic to send to zmq.PUB socket
    at the server.
    """
    def __init__(self, endpoint, context):
        """
        :param endpoint: Endpoint to bind or connect the socket to.
        :type endpoint: str
        :param context: ZeroMQ Context.
        :type context: zmq.Context instance.
        """
        ZMQAppSocket.__init__(self, context.socket(zmq.DEALER), endpoint)

    def run(self):
        """
        Overrides ZMQAppSocket.run() method.
        """
        self._socket.connect(self._endpoint)


class ZMQApp(ZMQBaseComponent):
    """
    ZMQApp instance. Uses a ServerHandler instance.
    """
    def __init__(self, state):
        """
        Initialize instance of type ZMQApp.

        :param state: A ServerState instance.
        :type endpoint: zmq_transport.u1db.server_state.ServerState
        """
        ZMQBaseComponent.__init__(self)
        self.state = state
        self.server_handler = ServerHandler(ENDPOINT_APPLICATION_HANDLER,
                                            self._context)

    def _prepare_reactor(self):
        """
        Prepares the reactor by wrapping sockets over ZMQStream and registering
        handlers.
        """
        self._loop = IOLoop.instance()
        self.server_handler.wrap_zmqstream()
        self.server_handler.register_handler("on_send", self.handle_snd_update)
        self.server_handler.register_handler("on_recv", self.handle_rcv_update)
        # self.check_updates_callback = PeriodicCallback(self.check_updates, 1000)

    def _ping(self):
        """
        Pings the server.
        """
        ping_struct = create_ping_msg()
        iden_ping_struct = proto.Identifier(type=proto.Identifier.PING,
                                            ping=ping_struct)
        str_iden_ping = serialize_msg(iden_ping_struct)
        self.server_handler.send([str_iden_ping])

    def start(self):
        """
        Method to start the application.
        """
        self._prepare_reactor()
        self.server_handler.run()
        # self.check_updates_callback.start()
        self._ping()

        try:
            self._loop.start()
        except KeyboardInterrupt:
            print "<APPLICATION> Interrupted."

    ###################### Start of callbacks. ########################

    def handle_snd_update(self, msg, status):
        """
        Callback function to make any application level changes after Update/Request has been
        sent via DEALER socket to Server.

        :param msg: Raw/Serialized message that was sent.
        :type msg: list
        :param status: return result of socket.send_multipart(msg)
        :type status: MessageTracker or None ; See: http://zeromq.github.io/pyzmq/api/generated/zmq.eventloop.zmqstream.html#zmq.eventloop.zmqstream.ZMQStream.on_send
        """
        print "<APPLICATION> Sent: ", msg

    def handle_rcv_update(self, msg):
        """
        Callback to handle incoming updates on DEALER sockets.

        :param msg: Raw Message received.
        :type msg: list
        """
        print "<APPLICATION> Received: ", msg

        # Message Format: [str_client_info, msg]
        str_client_info, msg = msg[0], msg[1:]

        response = []
        if len(msg) == 3:
            zmq_verb_str, sync_type_str, iden_str = msg
            # TODO: Do something with zmq_verb_str and sync_type_str
            # later.
        elif len(msg) == 1:
            iden_str = msg[0]
        else:
            # TODO: Maybe send server an error.
            return

        try:
            iden_struct = deserialize_msg("Identifier", iden_str)
        except DecodeError:
            # Silently fail for now. Implementation of recover sync
            # could go here.
            return
        else:
            response = self.identify_msg(iden_struct)

            if response:
                try:
                    response = serialize_msg(response)
                except DecodeError:
                    # Silently fail for now.
                    return
                else:
                    to_send = [str_client_info, response]
                    self.server_handler.send(to_send)

    # def check_updates(self):
    #     """
    #     Method to regularly check new updates in self.dataset
    #     """
    #     while not self.dataset.empty():
    #         data = self.dataset.get()
    #         self.server_handler.send(data)

    ####################### End of callbacks. #########################

    ############ Start of Application logic server side utilities. ###########

    def identify_msg(self, iden_struct):
        """
        Identifies the type of message packed in Identifier message structure and
        routes to the specific handler.
        :param iden_struct: Identifier message structure.
        :type iden_struct: zmq_transport.common.message_pb2.Identifier
        """
        if iden_struct.type == MSG_TYPE_GET_SYNC_INFO_REQUEST:
            return self.handle_get_sync_info_request(
                iden_struct.subscribe_request)
        elif iden_struct.type == MSG_TYPE_SEND_DOCUMENT_REQUEST:
            return self.handle_send_doc_request(
                iden_struct.send_document_request)
        elif iden_struct.type == MSG_TYPE_ALL_SENT_REQUEST:
            return self.handle_all_sent_request(
                iden_struct.all_sent_request)
        elif iden_struct.type == MSG_TYPE_GET_DOCUMENT_REQUEST:
            return self.handle_get_doc_request(
                iden_struct.get_document_request)
        elif iden_struct.type == MSG_TYPE_PUT_SYNC_INFO_REQUEST:
            return self.handle_put_sync_info_request(
                iden_struct.put_sync_info_request)

    def handle_get_sync_info_request(self, get_sync_info_struct):
        """
        Returns a GetSyncInfoResponse message.

        :return: GetSyncInfoResponse message wrapped in an Identifier message.
        :rtype: zmq_transport.common.message_pb2.Identifier
        """
        state = server_state.ServerState()
        sync_resource = SyncResource(self.dbname,
                                     get_sync_info_struct.source_replica_uid,
                                     state)
        kwargs = sync_resource.get()

        get_sync_info_struct = create_get_sync_info_response_msg(**kwargs)
        return proto.Identifier(type=proto.Identifier.GET_SYNC_INFO_RESPONSE,
                                get_sync_info_response=get_sync_info_struct)

    def handle_send_doc_request(self, send_doc_req_struct):
        """
        Attempts to insert a document into the database and returns the status
        of the operation.

        :return: PutSyncInfoResponse message wrapped in an Identifier message.
        :type: zmq_transport.common.message_pb2.Identifier
        """
        # TODO: Some DB operation.
        # status = insert_doc()
        status = True
        send_doc_resp_struct = create_send_document_response_msg(
            source_transaction_id=send_doc_req_struct.source_transaction_id,
            inserted=status)
        return proto.Identifier(type=proto.Identifier.SEND_DOCUMENT_RESPONSE,
                                send_document_response=send_doc_resp_struct)


    def handle_all_sent_request(self, all_sent_req_struct):
        """
        Returns an AllSentResponse message.

        :return: AllSentResponse message wrapped in an Identifier message.
        :rtype: zmq_transport.common.message_pb2.Identifier
        """
        def get_docs_to_send():
            """
            Returns a list of document id and generations that needs to be sent
            to the source.

            TODO: Implement functionality to return docs. Arbit for now.
            """
            return [("D1", 2), ("D2", 6), ("D3", 13), ("D4", 9)]

        # TODO: First check if the last doc has been successfully
        # inserted. Or else wait. or timeout maybe? or send some error
        # signal to source ?

        target_info = get_target_info()
        docs_to_send = get_docs_to_send()
        all_sent_resp_struct = create_all_sent_response_msg(
            items=docs_to_send,
            target_generation=target_info["target_replica_generation"],
            target_trans_id=target_info["target_replica_trans_id"]
        )
        return proto.Identifier(type=proto.Identifier.ALL_SENT_RESPONSE,
                                all_sent_response=all_sent_resp_struct)


    def handle_get_doc_request(self, get_doc_req_struct):
        """
        Returns a requested document.

        :return: GetDocumentResponse message wrapped in an Identifier message.
        :rtype: zmq_transport.common.message_pb2.Identifier
        """
        # TODO: Fetch doc from db.
        doc_id, doc_rev, doc_generation, doc_content = get_doc_info()
        target_generation = 25
        target_trans_id = "TARGET-ID"
        get_doc_resp_struct = create_get_document_response_msg(
            doc_id=doc_id, doc_rev=doc_rev,  doc_generation=doc_generation,
            doc_content=doc_content, target_generation=target_generation,
            target_trans_id=target_trans_id)
        return proto.Identifier(type=proto.Identifier.GET_DOCUMENT_RESPONSE,
                                get_document_response=get_doc_resp_struct)


    def handle_put_sync_info_request(self, put_sync_info_struct):
        """
        Returns a PutSyncInfoResponse message.

        :return: PutSyncInfoResponse message wrapped in an Identifier message.
        :rtype: zmq_transport.common.message_pb2.Identifier
        """
        # TODO: Do some db transaction here.

        state = server_state.ServerState()
        sync_resource = SyncResource(self.dbname,
                                     put_sync_info_struct.source_replica_uid,
                                     state)
        inserted = sync_resource.put(
            put_sync_info_struct.source_replica_generation,
            put_sync_info_struct.source_transaction_id)

        response_struct = create_put_sync_info_response_msg(
            source_transaction_id=put_sync_info_struct.source_transaction_id,
            inserted=inserted)
        return proto.Identifier(type=proto.Identifier.PUT_SYNC_INFO_RESPONSE,
                                put_sync_info_response=response_struct)

    ######### End of Application logic server side utilities. #########

    def stop(self):
        """
        :param socket: ZeroMQ socket.
        :type socket: zmq.context.socket instance.
        :param endpoint: Endpoint to bind or connect the socket to.
        :type endpoint: str
        """
        # TODO: First complete any pending tasks in self.dataset and
        # send "TERM" signal to connected components.
        self._loop.stop()
        self.server_handler.close()
        self._context.destroy()
        self.server_handler = None
        self._context = None





