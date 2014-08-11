"""
Test module for zmq_transport.app.zmq_app
"""

# System imports
import os.path
import unittest
try:
    import simplejson as json
except ImportError:
    import json

# Dependencies' imports
from mock import (
    MagicMock,
    patch
)
import zmq
from zmq.eventloop.zmqstream import ZMQStream
from zmq.eventloop.ioloop import IOLoop
import u1db
from u1db.remote import server_state
from u1db.backends.sqlite_backend import SQLiteSyncTarget
from leap.soledad.common import USER_DB_PREFIX

# Local imports
from zmq_transport.app.zmq_app import (
    return_list,
    SeenDocsIndex,
    SyncResource,
    ServerHandler,
    ZMQApp
)
from zmq_transport.config.settings import (
    DATABASE_ROOT,
    DATABASE_EXTENSION,
    ENDPOINT_APPLICATION_HANDLER
)
from zmq_transport.config.u1db_settings import (
    TARGET_REPLICA_UID_KEY,
    TARGET_REPLICA_GEN_KEY,
    TARGET_REPLICA_TRANS_ID_KEY,
    SOURCE_REPLICA_UID_KEY,
    SOURCE_LAST_KNOWN_GEN_KEY,
    SOURCE_LAST_KNOWN_TRANS_ID_KEY
)
from zmq_transport.common.errors import SyncError
from zmq_transport.common.utils import (
    create_ping_msg,
    create_get_sync_info_request_msg,
    create_send_document_request_msg,
    create_all_sent_request_msg,
    create_get_document_request_msg,
    create_put_sync_info_request_msg,
    get_sync_id,
    serialize_msg
)
from zmq_transport.common import message_pb2 as proto
from zmq_transport.u1db.sync import SyncExchange


# Test stubs setup.
def init_server_state(cls=None):
    """
    Helper method to initiate a server_state.ServerState instance.

    :param cls: A class instance. Default is None. If it is set to None,
                then init_server_state returns a server_state.ServerState
                instance.
    :type cls: type

    :rtype: None if cls == None, else server_state.ServerState
    """
    state = server_state.ServerState()
    state.set_workingdir(DATABASE_ROOT)
    if cls:
        cls.state = state
    else:
        return state

def open_source_db(cls=None, create=True):
    """
    Helper method to open the database representing the source replica.

    :param cls: A class instance. Default is None. If it is set to None,
                then init_server_state returns a server_state.ServerState
                instance.
    :type cls: type
    :param create: A flag to indicate that the source database will be
                   created or not.
    :type create: bool

    :return: None or (Database instance and source_replica_uid)
    :rtype: None/tuple
    """
    source = u1db.open((os.path.join(DATABASE_ROOT,
                                  "source-USER-1.u1db")), create=create)
    source_replica_uid = source._get_replica_uid()
    if cls:
        cls.source = source
        cls.source_replica_uid = source_replica_uid
    else:
        return source, source_replica_uid


class BaseApplicationTest(unittest.TestCase):
    """
    Base test class for zmq_transport.app.zmq_app tests.
    """
    pass

class ReturnListTest(BaseApplicationTest):
    """
    Test suite for zmq_app.return_list
    """
    def test_return_list(self):
        @return_list
        def dummy_test():
            return "Hello"

        self.assertEqual(["Hello"], dummy_test())


class SeenDocsIndexTest(BaseApplicationTest):
    """
    Test suite for zmq_app.SeenDocsIndex
    """
    def setUp(self):
        self.seen_docs = SeenDocsIndex()
        self.sync_id = "S-1"

    def test___init__(self):
        """
        Tests zmq_app.SeenDocsIndex.__init__
        """
        self.assertEqual(self.seen_docs.index, {})

    def test_add_sync_id(self):
        """
        Tests zmq_app.SeenDocsIndex.add_sync_id
        """
        self.seen_docs.add_sync_id(self.sync_id)
        self.assertEqual(self.seen_docs.index.get(self.sync_id), {})
        with self.assertRaises(SyncError):
            self.seen_docs.add_sync_id(self.sync_id)

    def test_update_seen_ids(self):
        """
        Tests zmq_app.SeenDocsIndex.update_seen_ids
        """
        seen_ids = {
            "d1": 1,
            "d2": 2,
            "d3": 3
        }
        with self.assertRaises(SyncError):
            self.seen_docs.update_seen_ids(self.sync_id, seen_ids)

        self.seen_docs.add_sync_id(self.sync_id)
        self.assertEqual(self.seen_docs.index.get(self.sync_id), {})
        self.seen_docs.update_seen_ids(self.sync_id, seen_ids)
        self.assertEqual(self.seen_docs.index.get(self.sync_id), seen_ids)

    def tearDown(self):
        del self.seen_docs
        del self.sync_id


class SyncResourceTest(BaseApplicationTest):
    """
    Test suite for zmq_app.SyncResource
    """
    def setUp(self):
        init_server_state(self)
        open_source_db(self)
        self.dbname = "{0}USER-1{1}".format(USER_DB_PREFIX, DATABASE_EXTENSION)
        self.sync_resource = SyncResource(self.dbname, self.source_replica_uid,
                                          self.state)

    def test___init__(self):
        """
        Tests SyncResource.__init__
        """
        self.assertEqual(self.sync_resource._dbname, self.dbname)
        self.assertEqual(self.sync_resource._source_replica_uid,
                         self.source_replica_uid)
        self.assertIsInstance(self.sync_resource._state,
                              server_state.ServerState)
        self.assertEqual(self.sync_resource._replica_uid, None)

    def test_get_target(self):
        """
        Tests SyncResource.get_target
        """
        self.assertIsInstance(self.sync_resource.get_target(), SQLiteSyncTarget)

    def test_get(self):
        """
        Tests SyncResource.get
        """
        ret = self.sync_resource.get()
        self.assertIsNotNone(ret.get(TARGET_REPLICA_UID_KEY))
        self.assertIsNotNone(ret.get(TARGET_REPLICA_GEN_KEY))
        self.assertIsNotNone(ret.get(TARGET_REPLICA_TRANS_ID_KEY))
        self.assertIsNotNone(ret.get(SOURCE_REPLICA_UID_KEY))
        self.assertIsNotNone(ret.get(SOURCE_LAST_KNOWN_GEN_KEY))
        self.assertIsNotNone(ret.get(SOURCE_LAST_KNOWN_TRANS_ID_KEY))

    def test_put(self):
        """
        Tests SyncResource.put
        """
        self.assertEqual(self.sync_resource.put(0, ""), True)

    def test_prepare_for_sync_exchange(self):
        """
        Tests SyncResource.prepare_for_sync_exchange
        """
        self.sync_resource.prepare_for_sync_exchange(0, "")
        self.assertIsInstance(self.sync_resource.sync_exch, SyncExchange)
        self.sync_resource.prepare_for_sync_exchange(0, "", True)
        self.assertIsInstance(self.sync_resource.sync_exch, SyncExchange)

    def test_insert_doc(self):
        """
        Tests SyncResource.insert_doc
        """
        doc = self.source.create_doc({"data": "Hello World"})
        _, _, changes = self.source.whats_changed(0)
        _, gen, trans_id = changes[0]

        self.sync_resource.prepare_for_sync_exchange(0, "")
        new_gen, new_trans_id = self.sync_resource.insert_doc(
            doc.doc_id, doc.rev, json.dumps(doc.content), gen, trans_id)
        self.assertIsInstance(new_gen, int)
        self.assertIsInstance(new_trans_id, unicode)
        self.assertNotEqual(len(new_trans_id), 0)
        self.assertEqual(new_trans_id[:2], "T-")

    def test_return_changed_docs(self):
        """
        Tests SyncResource.return_changed_docs
        """
        self.sync_resource.prepare_for_sync_exchange(0, "")
        doc = self.sync_resource.sync_exch._db.create_doc(
            {"data": "hello world"})
        (docs_by_gen, new_gen,
         new_trans_id) = self.sync_resource.return_changed_docs()
        self.assertEqual(docs_by_gen[-1][0], doc)
        self.assertIsInstance(new_gen, int)
        self.assertNotEqual(new_gen, 0)
        self.assertIsInstance(new_trans_id, unicode)
        self.assertNotEqual(len(new_trans_id), 0)
        self.assertEqual(new_trans_id[:2], "T-")

    def test_fetch_doc(self):
        """
        Tests SyncResource.fetch_doc
        """
        self.sync_resource.prepare_for_sync_exchange(0, "")
        doc = self.sync_resource.sync_exch._db.create_doc(
            {"data": "hello world"})
        self.assertEqual(doc, self.sync_resource.fetch_doc(doc.doc_id))

    def tearDown(self):
        del self.state
        self.source.close()
        del self.source_replica_uid
        del self.dbname
        del self.sync_resource


class ServerHandlerTest(BaseApplicationTest):
    """
    Test suite for zmq_transport.app.zmq_app.ServerHandler
    """
    def setUp(self):
        self.context = zmq.Context()

    def test___init__(self):
        """
        Tests ServerHandler.__init__
        """
        # Mock is sexy, but a little difficult to implement sometimes.
        with patch.object(ServerHandler, "__init__") as mock_init:
            mock_init.return_value = None
            server_handler = ServerHandler(ENDPOINT_APPLICATION_HANDLER,
                                           self.context)
            mock_init.assert_called_once_with(
                ENDPOINT_APPLICATION_HANDLER, self.context)

    def test_run(self):
        """
        Tests ServerHandler.run
        """
        with patch.object(ServerHandler, "run") as mock_run:
            mock_run.return_value = None
            server_handler = ServerHandler(ENDPOINT_APPLICATION_HANDLER,
                                           self.context)
            server_handler.run(ENDPOINT_APPLICATION_HANDLER)
            server_handler.run.assert_called_once_with(
                ENDPOINT_APPLICATION_HANDLER)

    def tearDown(self):
        self.context.destroy()


class ZMQAppTest(BaseApplicationTest):
    """
    Test suite for zmq_transport.app.zmq_app.ZMQApp
    """
    def setup_stub_sync_environment(self, cls=None, create=True):
        """
        Helper method to set up test stubs to simulate sync environment
        plus set up source replica.
        """
        if cls:
            open_source_db(cls, create)
            source, source_replica_uid = None, None
        else:
            source, source_replica_uid = open_source_db(cls, create)

        # Simulate that a sync is already in session.
        sync_id = get_sync_id()
        self.zmq_app.seen_docs_index.add_sync_id(sync_id)
        return source, source_replica_uid, sync_id

    def setUp(self):
        init_server_state(self)
        self.zmq_app = ZMQApp(self.state)

    def test___init__(self):
        """
        Tests ZMQApp.__init__
        """
        self.assertIsInstance(self.zmq_app._context, zmq.Context)
        self.assertEqual(self.zmq_app._loop, None)
        self.assertEqual(self.zmq_app.dataset, [])
        self.assertIsInstance(self.zmq_app._state, server_state.ServerState)
        self.assertIsInstance(self.zmq_app.server_handler, ServerHandler)
        self.assertIsInstance(self.zmq_app.seen_docs_index, SeenDocsIndex)

    def test__prepare_reactor(self):
        """
        Tests ZMQApp._prepare_reactor
        """
        self.zmq_app._prepare_reactor()
        self.assertIsInstance(self.zmq_app._loop, IOLoop)
        self.assertIsInstance(self.zmq_app.server_handler._socket, ZMQStream)

    def test__ping(self):
        """
        Tests ZMQApp._ping
        """
        ping_struct = create_ping_msg()
        iden_ping_struct = proto.Identifier(type=proto.Identifier.PING,
                                            ping=ping_struct)
        str_iden_ping = serialize_msg(iden_ping_struct)
        with patch.object(self.zmq_app.server_handler, "send") as mock_send:
            self.zmq_app._ping()
            self.zmq_app.server_handler.send.assert_called_once_with(
                [str_iden_ping])

    def test__prepare_u1b_sync_resource(self):
        """
        Tests ZMQApp._prepare_u1db_sync_resource
        """
        source, source_replica_uid = open_source_db()
        source_replica_uid = source._get_replica_uid()
        sync_resource = self.zmq_app._prepare_u1db_sync_resource(
            "USER-1", source_replica_uid)
        self.assertIsInstance(sync_resource, SyncResource)

    def test__handle_snd_update(self):
        """
        Tests ZMQApp.handle_snd_update
        """
        ret = self.zmq_app.handle_snd_update(["Hello"], None)
        #TODO: This test is meaningless now. Will be done once
        #ZMQApp.handle_snd_update does something meanigful.
        self.assertIsNone(ret)

    def test_handle_rcv_update(self):
        """
        Tests ZMQApp.handle_rcv_update
        """
        source, source_replica_uid = open_source_db()
        msg = create_get_sync_info_request_msg(
            user_id="USER-1", source_replica_uid=source_replica_uid,
            sync_id=get_sync_id()
        )
        iden_struct = proto.Identifier(
            type=proto.Identifier.GET_SYNC_INFO_REQUEST,
            get_sync_info_request=msg)
        dummy_client_info = "client 1"
        iden_str = serialize_msg(iden_struct)
        self.zmq_app.server_handler.send = MagicMock(return_value=None)
        with patch.object(self.zmq_app.server_handler, "send") as mock_send:
            response = self.zmq_app.handle_rcv_update(
                [dummy_client_info, iden_str])
            mock_send.assert_called_once()

    def test_identify_msg_with_get_sync_info_request(self):
        """
        Tests ZMQApp.identify_msg for messsage type GetSyncInfoRequest
        """
        source, source_replica_uid = open_source_db()

        msg = create_get_sync_info_request_msg(
            user_id="USER-1", source_replica_uid=source_replica_uid,
            sync_id=get_sync_id())
        iden_struct = proto.Identifier(
            type=proto.Identifier.GET_SYNC_INFO_REQUEST,
            get_sync_info_request=msg)
        ret = self.zmq_app.identify_msg(iden_struct)
        self.assertIsInstance(ret, list)
        ret = ret[0]
        self.assertIsInstance(ret, proto.Identifier)
        self.assertEqual(ret.type, proto.Identifier.GET_SYNC_INFO_RESPONSE)
        self.assertIsInstance(ret.get_sync_info_response,
                              proto.GetSyncInfoResponse)

    def test_identify_msg_with_send_document_request(self):
        """
        Tests ZMQApp.identify_msg for message type SendDocumentRequest
        """
        source, source_replica_uid, sync_id = self.setup_stub_sync_environment()

        doc = source.create_doc({"data": "hello world"})
        gen = source._get_generation()
        trans_id = source._get_trans_id_for_gen(gen)

        msg = create_send_document_request_msg(
            user_id="USER-1", source_replica_uid=source_replica_uid,
            sync_id=sync_id, doc_id=doc.doc_id, doc_rev=doc.rev,
            doc_generation=1, doc_content=json.dumps(doc.content),
            source_generation=gen, source_transaction_id=trans_id,
            target_last_known_generation=0, target_last_known_trans_id="")
        iden_struct = proto.Identifier(
            type=proto.Identifier.SEND_DOCUMENT_REQUEST,
            send_document_request=msg)
        ret = self.zmq_app.identify_msg(iden_struct)
        self.assertIsInstance(ret, list)
        ret = ret[0]
        self.assertIsInstance(ret, proto.Identifier)
        self.assertEqual(ret.type, proto.Identifier.SEND_DOCUMENT_RESPONSE)
        self.assertIsInstance(ret.send_document_response,
                              proto.SendDocumentResponse)

    def test_identify_msg_with_all_sent_request(self):
        """
        Tests ZMQApp.identify_msg for message type AllSentResponse
        """
        source, source_replica_uid, sync_id = self.setup_stub_sync_environment()

        msg = create_all_sent_request_msg(
            user_id="USER-1", sync_id=sync_id,
            source_replica_uid=source_replica_uid, total_docs_sent=0,
            all_sent=True, target_last_known_generation=0,
            target_last_known_trans_id="")
        iden_struct = proto.Identifier(
            type=proto.Identifier.ALL_SENT_REQUEST,
            all_sent_request=msg)
        ret = self.zmq_app.identify_msg(iden_struct)
        self.assertIsInstance(ret, list)
        ret = ret[0]
        self.assertIsInstance(ret, proto.Identifier)
        self.assertEqual(ret.type, proto.Identifier.ALL_SENT_RESPONSE)
        self.assertIsInstance(ret.all_sent_response, proto.AllSentResponse)

    def test_identify_msg_with_get_doc_request(self):
        """
        Tests ZMQApp.identify_msg for message type GetDocumentRequest
        """
        source, source_replica_uid, sync_id = self.setup_stub_sync_environment()

        sync_resource = self.zmq_app._prepare_u1db_sync_resource(
            "USER-1", source_replica_uid)
        sync_resource.prepare_for_sync_exchange(0, "")
        doc = sync_resource.sync_exch._db.create_doc({"data": "hello world!"})
        docs_by_gen, _, _ = sync_resource.return_changed_docs()

        _, gen, trans_id = docs_by_gen[-1]

        msg = create_get_document_request_msg(
            user_id="USER-1", source_replica_uid=source_replica_uid,
            sync_id=sync_id, doc_id=doc.doc_id, doc_generation=gen,
            trans_id=trans_id,docs_received_count=0,
            target_last_known_generation=0,
            target_last_known_trans_id="")
        iden_struct = proto.Identifier(
            type=proto.Identifier.GET_DOCUMENT_REQUEST,
            get_document_request=msg)

        ret = self.zmq_app.identify_msg(iden_struct)
        self.assertIsInstance(ret, list)
        ret = ret[0]
        self.assertIsInstance(ret, proto.Identifier)
        self.assertEqual(ret.type, proto.Identifier.GET_DOCUMENT_RESPONSE)
        self.assertIsInstance(ret.get_document_response,
                              proto.GetDocumentResponse)

    def test_identify_msg_with_put_sync_info_request(self):
        """
        Tests ZMQApp.identify_msg for message type PutSyncInfoRequest
        """
        source, source_replica_uid, sync_id = self.setup_stub_sync_environment()

        msg = create_put_sync_info_request_msg(
            user_id="USER-1", sync_id=sync_id,
            source_replica_uid=source_replica_uid, source_replica_generation=0,
            source_transaction_id="", target_last_known_generation=0,
            target_last_known_trans_id="")
        iden_struct = proto.Identifier(
            type=proto.Identifier.PUT_SYNC_INFO_REQUEST,
            put_sync_info_request=msg)

        ret = self.zmq_app.identify_msg(iden_struct)
        self.assertIsInstance(ret, list)
        ret = ret[0]
        self.assertIsInstance(ret, proto.Identifier)
        self.assertEqual(ret.type, proto.Identifier.PUT_SYNC_INFO_RESPONSE)
        self.assertIsInstance(ret.put_sync_info_response,
                              proto.PutSyncInfoResponse)

    def test_handle_get_sync_info_request(self):
        """
        Tests ZMQApp.handle_get_sync_info_request
        """
        source, source_replica_uid, sync_id = self.setup_stub_sync_environment()

        msg = create_get_sync_info_request_msg(
            user_id="USER-1", source_replica_uid=source_replica_uid,
            sync_id=sync_id)

        ret = self.zmq_app.handle_get_sync_info_request(msg)
        self.assertEqual(ret, None)

        # Reset Index
        self.zmq_app.seen_docs_index.index = {}

        ret = self.zmq_app.handle_get_sync_info_request(msg)
        self.assertIsInstance(ret, list)
        ret = ret[0]
        self.assertIsInstance(ret, proto.Identifier)
        self.assertEqual(ret.type, proto.Identifier.GET_SYNC_INFO_RESPONSE)
        self.assertIsInstance(ret.get_sync_info_response,
                              proto.GetSyncInfoResponse)

    def test_handle_send_doc_request_invalid_generation(self):
        """
        Tests ZMQApp.handle_send_doc_request with an invalid generation.
        """
        source, source_replica_uid, sync_id = self.setup_stub_sync_environment()

        doc = source.create_doc({"data": "hello world"})
        gen = source._get_generation()
        trans_id = source._get_trans_id_for_gen(gen)

        msg = create_send_document_request_msg(
            user_id="USER-1", source_replica_uid=source_replica_uid,
            sync_id=sync_id, doc_id=doc.doc_id, doc_rev=doc.rev,
            doc_generation=1, doc_content=json.dumps(doc.content),
            source_generation=gen, source_transaction_id=trans_id,
            target_last_known_generation=-1,
            target_last_known_trans_id="")

        ret = self.zmq_app.handle_send_doc_request(msg)
        self.assertEqual(ret, None)

    def test_handle_send_doc_request_invalid_transaction_id(self):
        """
        Tests ZMQApp.handle_send_doc_request with an invalid
        transaction_id.
        """
        source, source_replica_uid, sync_id = self.setup_stub_sync_environment()

        doc = source.create_doc({"data": "hello world"})
        gen = source._get_generation()
        trans_id = source._get_trans_id_for_gen(gen)

        msg = create_send_document_request_msg(
            user_id="USER-1", source_replica_uid=source_replica_uid,
            sync_id=sync_id, doc_id=doc.doc_id, doc_rev=doc.rev,
            doc_generation=1, doc_content=json.dumps(doc.content),
            source_generation=gen, source_transaction_id=trans_id,
            target_last_known_generation=1,
            target_last_known_trans_id="Invalid trans_id")

        ret = self.zmq_app.handle_send_doc_request(msg)
        self.assertEqual(ret, None)

    def test_handle_send_doc_request_insert_doc_fails(self):
        """
        Tests ZMQApp.handle_send_doc_request when an insert document
        operation fails.
        """
        source, source_replica_uid, sync_id = self.setup_stub_sync_environment()

        doc = source.create_doc({"data": "hello world"})
        gen = source._get_generation()
        trans_id = source._get_trans_id_for_gen(gen)

        msg = create_send_document_request_msg(
            user_id="USER-1", source_replica_uid=source_replica_uid,
            sync_id=sync_id, doc_id=doc.doc_id, doc_rev=doc.rev,
            doc_generation=1, doc_content="Test data",
            source_generation=gen, source_transaction_id=trans_id,
            target_last_known_generation=0,
            target_last_known_trans_id="")

        ret = self.zmq_app.handle_send_doc_request(msg)
        self.assertIsInstance(ret, list)
        ret = ret[0]
        self.assertIsInstance(ret, proto.Identifier)
        self.assertEqual(ret.type, proto.Identifier.SEND_DOCUMENT_RESPONSE)
        self.assertIsInstance(ret.send_document_response,
                              proto.SendDocumentResponse)
        self.assertEqual(ret.send_document_response.inserted, False)


    def test_handle_send_doc_request_sync_error(self):
        """
        Tests ZMQApp.handle_send_doc_request when a SyncError is raised.
        """
        # Testing for the case when a SyncError is raised while
        # updating the seen_docs_index after a successful insertion.

        # TODO: Note: Probably this use case should come before inserting
        # the doc to detect an out of session document. Also, the
        # index should be re-updated to confirm that this doc was
        # actually seen.
        source, source_replica_uid, sync_id = self.setup_stub_sync_environment()

        doc = source.create_doc({"data": "hello world"})
        gen = source._get_generation()
        trans_id = source._get_trans_id_for_gen(gen)

        self.zmq_app.seen_docs_index.index.pop(sync_id)

        msg = create_send_document_request_msg(
            user_id="USER-1", source_replica_uid=source_replica_uid,
            sync_id=sync_id, doc_id=doc.doc_id, doc_rev=doc.rev,
            doc_generation=1, doc_content=json.dumps(doc.content),
            source_generation=gen, source_transaction_id=trans_id,
            target_last_known_generation=0,
            target_last_known_trans_id="")

        ret = self.zmq_app.handle_send_doc_request(msg)
        self.assertEqual(ret, None)

    def test_handle_all_sent_request_invalid_generation(self):
        """
        Tests ZMQApp.handle_all_sent_request with an invalid generation.
        """
        source, source_replica_uid, sync_id = self.setup_stub_sync_environment()

        msg = create_all_sent_request_msg(
            user_id="USER-1", sync_id=sync_id,
            source_replica_uid=source_replica_uid, total_docs_sent=0,
            all_sent=True, target_last_known_generation=-1,
            target_last_known_trans_id="")
        ret = self.zmq_app.handle_all_sent_request(msg)
        self.assertEqual(ret, None)

    def test_handle_all_sent_request_invalid_transaction_id(self):
        """
        Tests ZMQApp.handle_all_sent_request with an invalid
        transaction_id.
        """
        source, source_replica_uid, sync_id = self.setup_stub_sync_environment()

        msg = create_all_sent_request_msg(
            user_id="USER-1", sync_id=sync_id,
            source_replica_uid=source_replica_uid, total_docs_sent=0,
            all_sent=True, target_last_known_generation=1,
            target_last_known_trans_id="Invalid transaction_id.")

        ret = self.zmq_app.handle_all_sent_request(msg)
        self.assertEqual(ret, None)

    def test_handle_all_sent_request_success(self):
        """
        Tests ZMQApp.handle_all_sent_request for success.
        """
        source, source_replica_uid, sync_id = self.setup_stub_sync_environment()

        msg = create_all_sent_request_msg(
            user_id="USER-1", sync_id=sync_id,
            source_replica_uid=source_replica_uid, total_docs_sent=0,
            all_sent=True, target_last_known_generation=0,
            target_last_known_trans_id="")

        ret = self.zmq_app.handle_all_sent_request(msg)
        self.assertIsInstance(ret, list)
        ret = ret[0]
        self.assertIsInstance(ret, proto.Identifier)
        self.assertEqual(ret.type, proto.Identifier.ALL_SENT_RESPONSE)
        self.assertIsInstance(ret.all_sent_response, proto.AllSentResponse)

    def test_handle_get_doc_request_invalid_generation(self):
        """
        Tests ZMQApp.handle_get_document_request with an invalid
        generation.
        """
        source, source_replica_uid, sync_id = self.setup_stub_sync_environment()

        sync_resource = self.zmq_app._prepare_u1db_sync_resource(
            "USER-1", source_replica_uid)
        sync_resource.prepare_for_sync_exchange(0, "")
        doc = sync_resource.sync_exch._db.create_doc({"data": "hello world!"})
        docs_by_gen, _, _ = sync_resource.return_changed_docs()
        _, gen, trans_id = docs_by_gen[-1]

        msg = create_get_document_request_msg(
            user_id="USER-1", source_replica_uid=source_replica_uid,
            sync_id=sync_id, doc_id=doc.doc_id, doc_generation=gen,
            trans_id=trans_id,docs_received_count=0,
            target_last_known_generation=-1,
            target_last_known_trans_id="")

        ret = self.zmq_app.handle_get_doc_request(msg)
        self.assertEqual(ret, None)

    def test_handle_get_doc_request_invalid_transaction_id(self):
        """
        Tests ZMQApp.handle_get_document_request with an invalid
        transaction_id.
        """
        source, source_replica_uid, sync_id = self.setup_stub_sync_environment()

        sync_resource = self.zmq_app._prepare_u1db_sync_resource(
            "USER-1", source_replica_uid)
        sync_resource.prepare_for_sync_exchange(0, "")
        doc = sync_resource.sync_exch._db.create_doc({"data": "hello world!"})
        docs_by_gen, _, _ = sync_resource.return_changed_docs()
        _, gen, trans_id = docs_by_gen[-1]

        msg = create_get_document_request_msg(
            user_id="USER-1", source_replica_uid=source_replica_uid,
            sync_id=sync_id, doc_id=doc.doc_id, doc_generation=gen,
            trans_id=trans_id,docs_received_count=0,
            target_last_known_generation=1,
            target_last_known_trans_id="Invalid transaction_id")

        ret = self.zmq_app.handle_get_doc_request(msg)
        self.assertEqual(ret, None)

    def test_handle_get_doc_request_success(self):
        """
        Tests ZMQApp.handle_get_document_request for success.
        """
        source, source_replica_uid, sync_id = self.setup_stub_sync_environment()

        sync_resource = self.zmq_app._prepare_u1db_sync_resource(
            "USER-1", source_replica_uid)
        sync_resource.prepare_for_sync_exchange(0, "")
        doc = sync_resource.sync_exch._db.create_doc({"data": "hello world!"})
        docs_by_gen, _, _ = sync_resource.return_changed_docs()
        _, gen, trans_id = docs_by_gen[-1]

        msg = create_get_document_request_msg(
            user_id="USER-1", source_replica_uid=source_replica_uid,
            sync_id=sync_id, doc_id=doc.doc_id, doc_generation=gen,
            trans_id=trans_id,docs_received_count=0,
            target_last_known_generation=0,
            target_last_known_trans_id="")

        ret = self.zmq_app.handle_get_doc_request(msg)
        self.assertIsInstance(ret, list)
        ret = ret[0]
        self.assertIsInstance(ret, proto.Identifier)
        self.assertEqual(ret.type, proto.Identifier.GET_DOCUMENT_RESPONSE)
        self.assertIsInstance(ret.get_document_response,
                              proto.GetDocumentResponse)

    def test_handle_put_sync_info_request_invalid_generation(self):
        """
        Tests ZMQApp.handle_put_sync_info_request
        """
        source, source_replica_uid, sync_id = self.setup_stub_sync_environment()

        msg = create_put_sync_info_request_msg(
            user_id="USER-1", sync_id=sync_id,
            source_replica_uid=source_replica_uid, source_replica_generation=0,
            source_transaction_id="", target_last_known_generation=-1,
            target_last_known_trans_id="")

        ret = self.zmq_app.handle_put_sync_info_request(msg)
        self.assertEqual(ret, None)

    def test_handle_put_sync_info_request_invalid_transaction_id(self):
        """
        Tests ZMQApp.handle_put_sync_info_request
        """
        source, source_replica_uid, sync_id = self.setup_stub_sync_environment()

        msg = create_put_sync_info_request_msg(
            user_id="USER-1", sync_id=sync_id,
            source_replica_uid=source_replica_uid, source_replica_generation=0,
            source_transaction_id="", target_last_known_generation=1,
            target_last_known_trans_id="Invalid transaction_id.")

        ret = self.zmq_app.handle_put_sync_info_request(msg)
        self.assertEqual(ret, None)

    def test_stop(self):
        """
        Tests ZMQApp.stop
        """
        #TODO: Need some ideas on how to test this.
        pass

    def tearDown(self):
        del self.zmq_app
