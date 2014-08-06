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
from mock import MagicMock
import zmq
import u1db
from u1db.remote import server_state
from u1db.backends.sqlite_backend import SQLiteSyncTarget
from leap.soledad.common import USER_DB_PREFIX

# Local imports
from zmq_transport.app.zmq_app import (
    return_list,
    SeenDocsIndex,
    SyncResource,
    ServerHandler
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
from zmq_transport.u1db.sync import SyncExchange


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
        self.seen_docs.update_seen_ids(self.sync_id, seen_ids)

    def tearDown(self):
        del self.seen_docs
        del self.sync_id


class SyncResourceTest(BaseApplicationTest):
    """
    Test suite for zmq_app.SyncResource
    """
    def setUp(self):
        import pdb

        self.state = server_state.ServerState()
        self.state.set_workingdir(DATABASE_ROOT)
        self.source = u1db.open((os.path.join(DATABASE_ROOT,
                                  "source-USER-1.u1db")), create=True)
        self.source_replica_uid = self.source._get_replica_uid()
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
        del self.source
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
        # Mock is sexy, but a little difficult at the moment.
        ServerHandler.__init__ = MagicMock(return_value=None)
        server_handler = ServerHandler(ENDPOINT_APPLICATION_HANDLER,
                                       self.context)
        ServerHandler.__init__.assert_called_once_with(
            ENDPOINT_APPLICATION_HANDLER, self.context)

    def test_run(self):
        """
        Tests ServerHandler.run
        """
        import pdb

        ServerHandler.run = MagicMock(return_value=None)
        server_handler = ServerHandler(ENDPOINT_APPLICATION_HANDLER,
                                       self.context)
        ServerHandler.run.assert_called_once()

    def tearDown(self):
        self.context.term()



# class ApplicationTest(BaseApplicationTest):

#     def setUp(self):
#         self.application = Application(ENDPOINT_APPLICATION_HANDLER)

#     def test_application_init(self):
#         self.assertIsInstance(self.application, Application,
#                               "Instance is not of type Application.")
