"""
Application/Tier 1 Implementation
"""
# System Imports
from itertools import izip
import functools
import pdb

# Project dependency imports
import zmq
from zmq.eventloop.ioloop import IOLoop
from u1db.remote import server_state
from u1db.errors import InvalidTransactionId
from u1db import Document
from google.protobuf.message import DecodeError
from leap.soledad.common import USER_DB_PREFIX


# Local Imports
from zmq_transport.u1db import sync
from zmq_transport.config.settings import (
    ENDPOINT_APPLICATION_HANDLER,
    DATABASE_EXTENSION
)
from zmq_transport.config.protobuf_settings import (
    MSG_TYPE_GET_SYNC_INFO_REQUEST,
    MSG_TYPE_SEND_DOCUMENT_REQUEST,
    MSG_TYPE_ALL_SENT_REQUEST,
    MSG_TYPE_GET_DOCUMENT_REQUEST,
    MSG_TYPE_PUT_SYNC_INFO_REQUEST
)
from zmq_transport.config.u1db_settings import (
    TARGET_REPLICA_UID_KEY,
    TARGET_REPLICA_GEN_KEY,
    TARGET_REPLICA_TRANS_ID_KEY,
    SOURCE_REPLICA_UID_KEY,
    SOURCE_LAST_KNOWN_GEN_KEY,
    SOURCE_LAST_KNOWN_TRANS_ID_KEY,
    SOURCE_TRANSACTION_ID_KEY,
    INSERTED_KEY
)
from zmq_transport.common import message_pb2 as proto
from zmq_transport.common.zmq_base import (
    ZMQBaseSocket,
    ZMQBaseComponent
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
)
from zmq_transport.common.errors import (
    SyncError,
    DocumentNotInCache,
    SyncNotRegistered
)


def return_list(f):
    """
    Decorator that type casts the return value to a list. It will just
    check if the return type is a None, so as to avoid returning [None],
    it will return None otherwise, whatever be the return type it will
    wrap it in a list. Therefore use with CAUTION. You know what you are
    doing if you are using this to decorate your functions.
    """
    functools.wraps(f)
    def wrapper(*args, **kwargs):
        ret = f(*args, **kwargs)
        if ret is None or ret == []:
            return None
        return [ret]
    return wrapper


class SeenDocsIndex(object):
    """
    An Index to maintain the docs that have changed at source and have
    been successfully inserted into the target replica.

    This is a mapping between sync_id and seen_ids, where seen_ids
    itself is a dictionary and sync_id is a string.
    """
    def __init__(self):
        """
        Initializes a SeenDocsIndex instance.
        """
        self.index = {}

    def add_sync_id(self, sync_id):
        """
        Adds a new sync_id.
        """
        if self.index.get(sync_id) is not None:
            raise SyncError("Sync is already in session.")
        self.index[sync_id] = {}

    def update_seen_ids(self, sync_id, seen_ids):
        if self.index.get(sync_id) is None:
            raise SyncError(
              "No sync information available for sync_id:{0}".format(sync_id))
        for doc_id, gen in seen_ids.items():
            (self.index[sync_id])[doc_id] = gen


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
        :type: u1db.remote.server_state.ServerState
        """
        self._dbname = dbname
        self._source_replica_uid = source_replica_uid
        self._state = state
        self._replica_uid = None

    def get_target(self):
        return self._state.open_database(self._dbname).get_sync_target()

    def get(self):
        """
        Application Logic handler when the source invokes
        get_sync_info() on its end.
        """
        sync_target = self.get_target()
        result = sync_target.get_sync_info(self._source_replica_uid)
        return {
            TARGET_REPLICA_UID_KEY: result[0],
            TARGET_REPLICA_GEN_KEY: result[1],
            TARGET_REPLICA_TRANS_ID_KEY: result[2],
            SOURCE_REPLICA_UID_KEY: self._source_replica_uid,
            SOURCE_LAST_KNOWN_GEN_KEY: result[3],
            SOURCE_LAST_KNOWN_TRANS_ID_KEY: result[4]
        }

    def put(self, generation, transaction_id):
        """
        Application logic handler when the source invokes
        record_sync_info() on its end.
        """
        sync_target = self.get_target()
        sync_target.record_sync_info(self._source_replica_uid,
                                     generation,
                                     transaction_id)
        return True

    def prepare_for_sync_exchange(self, last_known_generation,
                                  last_known_trans_id, ensure=False):
        """
        Instantiates parameters necessary for sync_exchange to take
        place.
        Analogous to u1db.remote.http_app.SyncResource.post_args

        :param last_known_generation: The last known generation of
                                      source replica.
        :type last_known_generation: str
        :param last_known_trans_id: The last known transaction id of
                                    source replica.
        :type last_known_trans_id: str
        :param ensure: Flag to indicate that database needs to be created.
        :type ensure: bool
        """
        # TODO: ensure is not needed in this implementation. Ideally
        # the database should exist. Should be removed once sync works
        # completely.
        if ensure:
            db, self._replica_uid = self._state.ensure_database(self._dbname)
        else:
            db = self._state.open_database(self._dbname)
        db.validate_gen_and_trans_id(last_known_generation,
                                     last_known_trans_id)
        self.sync_exch = self.sync_exchange_class(db, self._source_replica_uid,
                                                  last_known_generation)

    def insert_doc(self, id, rev, content, gen, trans_id):
        """
        Applciation logic handler to insert a document into the target
        sent from source. Invoked when send_doc_info is invoked on the
        source.
        Analogous to u1db.remote.http_app.SyncResource.post_stream_entry()

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

        :return: The new generation and transaction_id after inserting
                 the document.
        :rtype: tuple
        """
        doc = Document(id, rev, content)
        self.sync_exch.insert_doc_from_source(doc, gen, trans_id)
        return self.sync_exch.get_generation_info()

    def return_changed_docs(self):
        """
        Application logic handler to return docs changed at target to
        source.
        Analogous to u1db.remote.http_app.SyncResource.post_end()

        :return: A tuple containing the docs by generation, the updated
                 target generation and the transaction id.
        :rtype: tuple
        """
        # Need to find out the changes again, as the previous instance
        # was killed within the scope of the function that called it.
        # TODO: Might consider doing something about this.
        new_gen = self.sync_exch.find_changes_to_return()
        new_trans_id = self.sync_exch.new_trans_id
        changed_doc_ids = [doc_id for doc_id, _, _ in
                           self.sync_exch.changes_to_return]
        docs = self.sync_exch.get_docs(
            changed_doc_ids, check_for_conflicts=False, include_deleted=True)

        # sync_exch.get_docs returns None instead of [] if no docs to
        # return. Potential U1DB bug.
        if docs is None:
            docs = []
        docs_by_gen = []
        for docs, doc_data in izip(docs, self.sync_exch.changes_to_return):
            _, gen, trans_id = doc_data
            docs_by_gen.append((docs, gen, trans_id))

        return (docs_by_gen, new_gen, new_trans_id)

    def fetch_doc(self, doc_id):
        """
        Fetches an individual doc.

        :param doc_id: Doc ID of the document to fetch.
        :type doc_id: str

        :return: The document requested.
        :rtype: u1db.Document
        """
        doc = self.sync_exch.get_docs([doc_id], check_for_conflicts=False,
                                      include_deleted=True)
        # doc is a generator. Thus iterating through it to return the
        # doc yielded by the generator. It will only yield one doc here.
        for d in doc:
            return d


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
# See: IRC Log below -
# <dhanush> How can I implement a queue on which a publisher should
# poll. Thus, if there are messages on the queue, it should detect the
# poll and then publish the updates?
# <dhanush> s/detect the poll/detect the messages
# <mrvn> dhanush: create a socket, recv from it
# <dhanush> mrvn: oh. so my application logic would write on that
# socket? which socket is ideal considering that I want PUB to read?
# <mrvn> if it's all one threat then just send to the PUB socket,
# otherwise PUSH/PULL comes to mind
# <dhanush> mrvn: for now everything is in a single thread. But
# probably the PUB will move to its own thread in a few days.
# <mrvn> only makes sense when you have multiple threads that want to
# publish stuff
# <dhanush> mrvn: umm. why? Why not if there's only one PUB thread?
# <mrvn> not one pub thread, threads that want to publish. PUSH - PULL
# -> PUB only makes sense if you have multiple PUSH sockets. Otherwise
# you just waste time because you could send on the PUB directly.
# <dhanush> mrvn: ah. okay. I'll keep that in mind.
# <dhanush> mrvn: so, if I send to the PUB socket directly, and then
# poll on it. It should work right?
# <mrvn> sure

# TODO: Or a ROUTER/DEALER combo.
# See: IRC Log below -
# <dhanush> so for throwing messages from the application to my
# server, I think I will use a PUSH/PULL combination. Now about
# throwing messages from server to application, is it the best idea to
# have another PUSH/PULL combination from the other side?
# <mrvn> no. if you need bidirectional then use bidirectional sockets
# <guido_g> depends on what you want to achieve
# <guido_g> "the other side" is undoubtly a little vague
# <mrvn> seperate sockets only make sense when the receiver and sender
# are in different thread and using a single socket becomes
# impossible. Or when you have broadcast (pub/sub) in the mix.
# <dhanush> guido_g: the other side would be my application logic. It
# will periodically generate some updates. or receive updates from
# clients. so clients send updates to the server, which is passes to
# the application.
# <dhanush> mrvn: ROUTER/DEALER makes more sense then.
# <mrvn> or XREQ/XREP or even just plain REQ/REP. it realy depends on
# what you want to do
# <guido_g> there is no XREP/XREQ anymore, its router / dealer

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
        :type endpoint: u1db.remote.server_state.ServerState
        """
        ZMQBaseComponent.__init__(self)
        self._state = state
        self.server_handler = ServerHandler(ENDPOINT_APPLICATION_HANDLER,
                                            self._context)
        self.seen_docs_index = SeenDocsIndex()

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

    def _prepare_u1db_sync_resource(self, user_id, source_replica_uid):
        """
        Helper function to set up instances of server_state.ServerState
        and zmq_app.SyncResource necessary for completing application
        logic for each request.

        :param user_id: User ID hash of the user.
        :type: str
        :param source_replica_uid: The replica id of the source
                                   initiating the sync.
        :type: str

        :return: A SyncResource instance
        :rtype: zmq_transport.u1db.zmq_app.SyncResource
        """
        dbname = "{0}{1}{2}".format(USER_DB_PREFIX, user_id,
                                         DATABASE_EXTENSION)
        return SyncResource(dbname, source_replica_uid, self._state)

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
        # TODO: Maybe do some application logging here.
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
            if response is not None:
                # response will be always of type list.
                for r in response:
                    try:
                        r = serialize_msg(r)
                    except DecodeError:
                        # Silently fail for now.
                        return
                    else:
                        to_send = [str_client_info, r]
                        self.server_handler.send(to_send)

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
                iden_struct.get_sync_info_request)
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

    @return_list
    def handle_get_sync_info_request(self, get_sync_info_struct):
        """
        Returns a GetSyncInfoResponse message.

        :return: GetSyncInfoResponse message wrapped in an Identifier message.
        :rtype: zmq_transport.common.message_pb2.Identifier
        """
        try:
            self.seen_docs_index.add_sync_id(get_sync_info_struct.sync_id)
        except SyncError as e:
            # TODO: Send an ErrorMessage maybe
            print e
            return None

        sync_resource = self._prepare_u1db_sync_resource(
            get_sync_info_struct.user_id, get_sync_info_struct.source_replica_uid)

        kwargs = sync_resource.get()
        # TODO: Decide about sending source_replica_uid in
        # GetSyncInfoResponse or not. Dropping it now.
        kwargs.pop(SOURCE_REPLICA_UID_KEY)
        get_sync_info_struct = create_get_sync_info_response_msg(**kwargs)
        return proto.Identifier(type=proto.Identifier.GET_SYNC_INFO_RESPONSE,
                                get_sync_info_response=get_sync_info_struct)

    @return_list
    def handle_send_doc_request(self, send_doc_req_struct):
        """
        Attempts to insert a document into the database and returns the status
        of the operation.

        :return: SendDocumentResponse message wrapped in an Identifier message.
        :type: zmq_transport.common.message_pb2.Identifier
        """
        sync_resource = self._prepare_u1db_sync_resource(
            send_doc_req_struct.user_id, send_doc_req_struct.source_replica_uid)

        try:
            sync_resource.prepare_for_sync_exchange(
                last_known_generation=send_doc_req_struct.target_last_known_generation,
                last_known_trans_id=send_doc_req_struct.target_last_known_trans_id)

        except InvalidTransactionId as e:
            # TODO: Maybe send a custom Error Message to client.
            print e
            return None

        kwargs = {SOURCE_TRANSACTION_ID_KEY:
                  send_doc_req_struct.source_transaction_id}
        try:
            new_gen, new_trans_id = sync_resource.insert_doc(
                    send_doc_req_struct.doc_id, send_doc_req_struct.doc_rev,
                    send_doc_req_struct.doc_content,
                    send_doc_req_struct.doc_generation,
                    send_doc_req_struct.source_transaction_id)
        except:
            # If sync_exch.insert_doc_from_source raises an exception.
            new_gen = send_doc_req_struct.target_last_known_generation
            new_trans_id = send_doc_req_struct.target_last_known_trans_id
            status = False
        else:
            status = True
            try:
                self.seen_docs_index.update_seen_ids(
                    send_doc_req_struct.sync_id, sync_resource.sync_exch.seen_ids)
            except SyncError as e:
                # TODO: Send an ErrorMessage maybe
                print e
                return None

        kwargs[TARGET_REPLICA_GEN_KEY] = new_gen
        kwargs[TARGET_REPLICA_TRANS_ID_KEY] = new_trans_id
        kwargs[INSERTED_KEY] = status
        send_doc_resp_struct = create_send_document_response_msg(**kwargs)
        return proto.Identifier(type=proto.Identifier.SEND_DOCUMENT_RESPONSE,
                                send_document_response=send_doc_resp_struct)

    @return_list
    def handle_all_sent_request(self, all_sent_req_struct):
        """
        Returns an AllSentResponse message.

        :return: AllSentResponse message wrapped in an Identifier message.
        :rtype: zmq_transport.common.message_pb2.Identifier
        """
        sync_resource = self._prepare_u1db_sync_resource(
            all_sent_req_struct.user_id,
            all_sent_req_struct.source_replica_uid)
        try:
            sync_resource.prepare_for_sync_exchange(
                last_known_generation=\
                    all_sent_req_struct.target_last_known_generation,
                last_known_trans_id=\
                    all_sent_req_struct.target_last_known_trans_id)
        except InvalidTransactionId as e:
            # TODO: Maybe send a custom Error Message to client.
            print e
            return None

        sync_resource.sync_exch.seen_ids =\
            self.seen_docs_index.index[all_sent_req_struct.sync_id]
        docs_by_gen, new_gen, new_trans_id = sync_resource.return_changed_docs()

        docs_to_send = [(doc.doc_id, gen, trans_id) for doc, gen, trans_id
                        in docs_by_gen]

        # TODO: First check if the last doc has been successfully
        # inserted. Or else wait. or timeout maybe? or send some error
        # signal to source ?
        # On Second thoughts this may not be required. Needs discussion.

        all_sent_resp_struct = create_all_sent_response_msg(
            items=docs_to_send, target_generation=new_gen,
            target_trans_id=new_trans_id)

        return proto.Identifier(type=proto.Identifier.ALL_SENT_RESPONSE,
                                all_sent_response=all_sent_resp_struct)

    @return_list
    def handle_get_doc_request(self, get_doc_req_struct):
        """
        Returns a list of documents changed at target.

        :return: A List of GetDocumentResponse message wrapped in an
                 Identifier message.
        :rtype: list
        """
        sync_resource = self._prepare_u1db_sync_resource(
            get_doc_req_struct.user_id,
            get_doc_req_struct.source_replica_uid)
        try:
            sync_resource.prepare_for_sync_exchange(
                last_known_generation=\
                    get_doc_req_struct.target_last_known_generation,
                last_known_trans_id=\
                    get_doc_req_struct.target_last_known_trans_id)
        except InvalidTransactionId as e:
            # TODO: Maybe send a custom Error Message to client.
            print e
            return None

        doc_id, gen, trans_id = (get_doc_req_struct.doc_id,
                                 get_doc_req_struct.doc_generation,
                                 get_doc_req_struct.trans_id)

        doc = sync_resource.fetch_doc(doc_id)

        get_doc_resp_struct = create_get_document_response_msg(
            doc_id=doc.doc_id, doc_rev=doc.rev, doc_generation=gen,
            doc_content=doc.get_json(), target_generation=-1,
            target_trans_id=trans_id)

        return proto.Identifier(type=proto.Identifier.GET_DOCUMENT_RESPONSE,
                                get_document_response=get_doc_resp_struct)

    @return_list
    def handle_put_sync_info_request(self, put_sync_info_struct):
        """
        Returns a PutSyncInfoResponse message.

        :return: PutSyncInfoResponse message wrapped in an Identifier message.
        :rtype: zmq_transport.common.message_pb2.Identifier
        """
        # TODO: Do some db transaction here.

        sync_resource = self._prepare_u1db_sync_resource(
            put_sync_info_struct.user_id,
            put_sync_info_struct.source_replica_uid)

        try:
            sync_resource.prepare_for_sync_exchange(
                put_sync_info_struct.target_last_known_generation,
                put_sync_info_struct.target_last_known_trans_id)
        except InvalidTransactionId as e:
            # TODO: Maybe send a custom Error Message to client.
            print e
            return None

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
