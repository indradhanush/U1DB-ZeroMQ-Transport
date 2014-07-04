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
    server_state,
    Document
)
from zmq_transport.common.utils import (
    serialize_msg,
    deserialize_msg,

    create_ping_msg,
    create_get_sync_info_response_msg,
    create_send_document_response_msg,
    create_all_sent_response_msg,
    create_get_document_response_msg,
    create_put_sync_info_response_msg
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
        """
        Application Logic handler when the source invokes
        get_sync_info() on its end.
        """
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
        """
        Application logic handler when the source invokes
        record_sync_info() on its end.
        """
        sync_target = self.get_target()
        sync_target.record_sync_info(self.source_replica_uid,
                                     generation,
                                     transaction_id)
        return True

    def instantiate_requirements(self, last_known_generation,
                                 last_known_trans_id, ensure=False):
        """
        Instantiates parameters necessary for sync_exchange to take
        place.
        Analogous to http_app.SyncResource.post_args

        :param last_known_generation: The last known generation of
                                      source replica.
        :type last_known_generation: str
        :param last_known_trans_id: The last known transaction id of
                                    source replica.
        :type last_known_trans_id: str
        :param ensure: Flag to indicate that database needs to be created.
        :type ensure: bool
        """
        if ensure:
            db, self.replica_uid = self.state.ensure_database(self.dbname)
        else:
            db = self.state.open_database(self.dbname)
        db.validate_gen_and_trans_id(last_known_generation,
                                     last_known_trans_id)
        self.sync_exch = self.sync_exchange_class(db, self.source_replica_uid,
                                                  last_known_generation)

    def insert_doc(self, id, rev, content, gen, trans_id):
        """
        Applciation logic handler to insert a document into the target
        sent from source. Invoked when send_doc_info is invoked on the
        source.
        Analogous to http_app.SyncResource.post_stream_entry()

        :param id: Document ID.
        :type id: str
        :param rev: Document revision.
        :type rev: str
        :param content: Document content
        :type content: str
        :param gen: Db generation.
        :type gen: int
        :param trans_id: Transaction ID.
        :type trans_id: str
        """
        doc = Document(id, rev, content)
        self.sync_exch.insert_doc_from_source(doc, gen, trans_id)

    def return_changed_docs(self):
        """
        Application logic handler to return docs changed at target to
        psource.
        Analogous to http_app.SyncResource.post_end()

        :return: A tuple containing the docs by generation, the updated
                 target generation and the transaction id.
        :rtype: tuple
        """
        new_gen = self.sync_exch.find_changes_to_return()
        new_trans_id = self.sync_exch.new_trans_id
        changed_doc_ids = [doc_id for doc_id, _, _ in
                           self.sync_exch.changes_to_return]
        docs = self.sync_exch._db.get_doce(
            changed_doc_ids, check_for_conflicts=False, include_deleted=True)

        docs_by_gen = zip(
            docs,
            (gen for _, gen, _ in self.sync_exch.changes_to_return),
            (trans_id for _, _, trans_id in self.sync_exch.changes_to_return)
        )
        return (docs_by_gen, new_gen, new_trans_id)


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


    def _prepare_u1db_action(self, dbname, source_replica_uid):
        """
        Helper function to set up instances of server_state.ServerState
        and zmq_app.SyncResource necessary for completing application logic
        for each request.

        :param dbname: Name of the database
        :type: str
        :param source_replica_uid: The replica id of the source
                                   initiating the sync.
        :type: str

        :return: A SyncResource instance
        :rtype: zmq_transport.u1db.zmq_app.SyncResource
        """
        state = server_state.ServerState()
        return SyncResource(dbname, source_replica_uid, state)

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
                # TODO: Maybe will force message handlers to send
                # response packed in a list for generalization here.
                # Needs to be discussed.
                if type(response) == list:
                    for r in response:
                        try:
                            r = serialize_msg(response)
                        except DecodeError:
                            # Silently fail for now.
                            return
                        else:
                            to_send = [str_client_info, r]
                            self.server_handler.send(to_send)
                else:
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
        sync_resource = _prepare_u1db_action(
            get_sync_info_struct.user_id, get_sync_info_struct.source_replica_uid)

        kwargs = sync_resource.get()

        get_sync_info_struct = create_get_sync_info_response_msg(**kwargs)
        return proto.Identifier(type=proto.Identifier.GET_SYNC_INFO_RESPONSE,
                                get_sync_info_response=get_sync_info_struct)

    def handle_send_doc_request(self, send_doc_req_struct):
        """
        Attempts to insert a document into the database and returns the status
        of the operation.

        :return: SendDocumentResponse message wrapped in an Identifier message.
        :type: zmq_transport.common.message_pb2.Identifier
        """
        sync_resource = _prepare_u1db_action(
            send_doc_req_struct.user_id, send_doc_req_struct.source_replica_uid)
        sync_resource.instantiate_requirements(
            send_doc_req_struct.source_generation,
            send_doc_req_struct.source_transaction_id)
        try:
            sync_resource.insert_doc(
                send_doc_req_struct.doc_id, send_doc_req_struct.doc_rev,
                send_doc_req_struct.doc_content,
                send_doc_req_struct.doc_generation,
                send_doc_req_struct.source_transaction_id)
        except:
            # If sync_exch.insert_doc_from_source raises an exception.
            status = False
        else:
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
            Finds the documents changed at target.

            :return: A tuple containing a list of document id and
                     generations that needs to be sent to the source,
                     the updated target generation and the target
                     transaction id.
            :rtype: tuple
            """
            sync_resource = _prepare_u1db_action(
                all_sent_req_struct.user_id,
                all_sent_req_struct.source_replica_uid)

            sync_resource.instantiate_requirements(
                all_sent_req_struct.target_last_known_generation,
                all_sent_req_struct.target_last_known_trans_id)

            new_gen = sync_resource.sync_exch.find_changes_to_return()
            new_trans_id = sync_resource.sync_exch.new_trans_id
            docs_to_send = zip((doc_id for doc_id, _, _ in
                                sync_resource.sync_exch.changes_to_return),
                               (gen for _, gen, _ in
                                sync_resource.sync_exch.changes_to_return))
            return (docs_to_send, new_gen, new_trans_id)

        # TODO: First check if the last doc has been successfully
        # inserted. Or else wait. or timeout maybe? or send some error
        # signal to source ?
        # On Second thoughts this may not be required. Needs discussion.

        docs_to_send, new_gen, new_trans_id = get_docs_to_send()
        all_sent_resp_struct = create_all_sent_response_msg(
            items=docs_to_send,
            target_generation=new_gen, target_trans_id=new_trans_id)

        return proto.Identifier(type=proto.Identifier.ALL_SENT_RESPONSE,
                                all_sent_response=all_sent_resp_struct)

    def handle_get_doc_request(self, get_doc_req_struct):
        """
        Returns a list of documents changed at target.

        :return: A List of GetDocumentResponse message wrapped in an
                 Identifier message.
        :rtype: list
        """
        sync_resource = _prepare_u1db_action(
            get_doc_req_struct.user_id,
            get_doc_req_struct.source_replica_uid)

        sync_resource.instantiate_requirements(
            get_doc_req_struct.target_last_known_genberation,
            get_doc_req_struct.target_last_known_trans_id)

        docs_by_gen, new_gen, new_trans_id = sync_resource.return_changed_docs()

        doc_structs = []
        for doc in docs_by_gen:
            get_doc_resp_struct = create_get_document_response_msg(
                doc_id=doc.doc_id, doc_rev=doc.doc_rev,
                doc_generation=doc.doc_generation, doc_content=doc.doc_content,
                target_generation=new_gen, target_trans_id=new_trans_id)
            iden_struct = proto.Identifier(
                type=proto.Identifier.GET_DOCUMENT_RESPONSE,
                get_document_response=get_doc_resp_struct)
            doc_structs.append(iden_struct)

        return doc_structs

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





