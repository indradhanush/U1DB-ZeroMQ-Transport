"""
Test suite for zmq_transport.u1db.zmq_target
"""

# System imports
import unittest

# Dependencies' imports
from mock import (
    patch,
    Mock,
    MagicMock
)

# Local imports
from zmq_transport.u1db import zmq_target
from zmq_transport.u1db.zmq_target import (
    ZMQSyncTarget
)
from zmq_transport.client.zmq_client import ZMQClientBase
from zmq_transport.config.settings import (
    ENDPOINT_CLIENT_HANDLER,
    ENDPOINT_PUBLISHER
)
from zmq_transport.common.errors import UserIDNotSet


class TestZMQSyncTarget(unittest.TestCase):
    """
    Tests zmq_target.u1db.zmq_target.ZMQSyncTarget
    """
    def setUp(self):
        self.endpoints = [ENDPOINT_CLIENT_HANDLER, ENDPOINT_PUBLISHER]
        self.user_id = "Unique user id that will never be the same."
        self.source_replica_uid = "Unique replica uid of the source."
        # self.patcher = patch("zmq_transport.u1db.zmq_target.ZMQClientBase",
        #                      spec=True)
        # self.patcher.start()
        # self.speaker_mock = patch("zmq_transport.client.zmq_client.Speaker",
        #                           spec=True)
        # self.speaker_mock.start()
        self.target = ZMQSyncTarget(self.endpoints)

    def setup_common_mocks(self):
        """
        Helper to setup common mocks between tests. There is a better way
        to do this I'm sure.
        """
        zmq_target.proto.Identifier = Mock(return_value="Mocked Identifier")
        zmq_target.serialize_msg = Mock(return_value="Serialized string")
        self.target.speaker.send = Mock()
        # Need indexing support here.
        self.target.speaker.recv = MagicMock(return_value="Mocked response")

    def test___init__raises_ValueError(self):
        """
        Tests that ZMQSyncTarget.__init__ raises a ValueError when the
        list of endpoints is not of length 2.
        """
        with self.assertRaises(ValueError):
            target = ZMQSyncTarget([])

    def test___init__raises_TypeError(self):
        """
        Tests that ZMQSyncTarget.__init__ raises a TypeError when the
        endpoints passed is not wrapped in a list.
        """
        with self.assertRaises(TypeError):
            target = ZMQSyncTarget("spam")

    def test___init__works_correctly(self):
        """
        Tests that ZMQSyncTarget.__init__ works correctly as required.
        """
        self.assertEqual(self.target.endpoints, self.endpoints)
        self.assertEqual(self.target.sync_required, False)
        self.assertEqual(self.target.sync_info, None)
        self.assertEqual(self.target.user_id, None)
        self.assertEqual(self.target.sync_id, None)
        self.assertEqual(self.target.target_last_known_generation, None)
        self.assertEqual(self.target.target_last_known_trans_id, None)
        self.assertEqual(self.target.source_current_gen, None)
        self.assertEqual(self.target.source_current_trans_id, None)
        self.assertEqual(self.target.source_last_known_generation, None)
        self.assertEqual(self.target.source_last_known_trans_id, None)

    def test__prepare_reactor_raises_NotImplementedError(self):
        """
        Tests that ZMQSyncTarget._prepare_reactor raises NotImplementedError
        """
        with self.assertRaises(NotImplementedError):
            self.target._prepare_reactor()

    def test_set_user_id(self):
        """
        Tests that ZMQSyncTarget.set_user_id sets user id as specified by
        the paramter.
        """
        self.target.set_user_id(self.user_id)
        self.assertEqual(self.target.user_id, self.user_id)

    def test_release_user_id(self):
        """
        Tests that ZMQSyncTarget.release_user_id sets user id to None
        """
        self.target.release_user_id()
        self.assertEqual(self.target.user_id, None)

    def test_check_user_id_raises_UserIDNotSet(self):
        """
        Tests that ZMQSyncTarget.check_user_id raises UserIDNotSet when
        ZMQSyncTarget.user_id is None
        """
        with self.assertRaises(UserIDNotSet):
            self.target.check_user_id()

    def test_start_raises_UserIDNotSet(self):
        """
        Tests that ZMQSyncTarget.start raises UserIDNotSet exception,
        when ZMQSyncTarget.user_id is None
        """
        with self.assertRaises(UserIDNotSet):
            self.target.start()

    def test_start_works_correctly(self):
        """
        Tests that ZMQSyncTarget.start works as intended under the right
        conditions.
        """
        self.target.check_user_id = MagicMock()
        self.target.speaker.run = MagicMock()
        self.target.set_user_id(self.user_id)
        self.target.start()
        self.target.check_user_id.assert_called_once()
        self.target.speaker.run.assert_called_once()

    def test_connect(self):
        """
        Tests ZMQSyncTarget.connect
        """
        self.assertIsInstance(ZMQSyncTarget.connect(self.endpoints),
                              ZMQSyncTarget)

    def test_get_sync_info(self):
        """
        Tests ZMQSyncTarget.get_sync_info
        """
        zmq_target.get_sync_id = Mock(return_value="Mocked sync-id")
        zmq_target.create_get_sync_info_request_msg = Mock(
            return_value="Mocked GetSyncInfoRequest")
        self.setup_common_mocks()
        response_dict = {
            "target_replica_uid": "T-ID",
            "target_replica_generation": 0,
            "target_replica_trans_id": "",
            "source_last_known_generation": 0,
            "source_last_known_trans_id": ""
        }
        mocked_response = Mock(**response_dict)
        zmq_target.parse_response = Mock(return_value=mocked_response)

        self.target.user_id = self.user_id
        response = self.target.get_sync_info(self.source_replica_uid)
        self.assertIsInstance(response, tuple)
        self.assertEqual(len(response), 5)
        self.assertEqual(response[0], response_dict["target_replica_uid"])
        self.assertEqual(response[1],
                         response_dict["target_replica_generation"])
        self.assertEqual(response[2], response_dict["target_replica_trans_id"])
        self.assertEqual(response[3],
                         response_dict["source_last_known_generation"])
        self.assertEqual(response[4],
                         response_dict["source_last_known_trans_id"])

    def test_record_sync_info(self):
        """
        Tests ZMQSyncTarget.record_sync_info
        """
        zmq_target.create_put_sync_info_request_msg = Mock(
            return_value="Mocked PutSyncInfoRequest")
        self.setup_common_mocks()
        response_dict = {
            "source_transaction_id": "",
            "inserted": True
        }
        mocked_response = Mock(**response_dict)
        zmq_target.parse_response = Mock(return_value=mocked_response)

        response = self.target.record_sync_info(self.source_replica_uid, 0, "")
        self.assertIsInstance(response, tuple)
        self.assertEqual(len(response), 2)
        self.assertEqual(response[0], response_dict["source_transaction_id"])
        self.assertEqual(response[1], response_dict["inserted"])

    def test_send_doc_info(self):
        """
        Tests ZMQSyncTarget.send_doc_info
        """
        zmq_target.create_send_document_request_msg = Mock(
            return_value="Mocked SendDocumentRequest")
        self.setup_common_mocks()
        return_value = "Mocked SendDocumentResponse"
        zmq_target.parse_response = Mock(
            return_value=return_value)
        retval = self.target.send_doc_info(self.source_replica_uid, "doc_id", "doc_rev",
                                  1, "Contents", 1, "")
        self.assertEqual(retval, return_value)

    def test_get_doc_at_target(self):
        """
        Tests ZMQSyncTarget.get_doc_at_target
        """
        zmq_target.create_get_document_request_msg = Mock(
            return_value="Mocked GetDocumentRequest")
        self.setup_common_mocks()
        response_dict = {
            "doc_id": "DOC-ID",
            "doc_rev": "REV",
            "doc_generation": 1,
            "doc_content": "Content",
            "target_generation": 0,
            "target_trans_id": ""
        }
        mocked_response = Mock(**response_dict)
        zmq_target.parse_response = Mock(return_value=mocked_response)
        self.target.get_doc_at_target(self.source_replica_uid, MagicMock(), 0)

    def test_sync_exchange(self):
        """
        Tests ZMQSyncTarget.sync_exchange
        """
        zmq_target.create_all_sent_request_msg = Mock(
            return_value="Mocked AllSentRequest")
        self.setup_common_mocks()
        doc_dict = {
            "doc_id": Mock(),
            "rev": Mock(),
            "get_json": Mock(return_value='{"mock": "mocked content" }')
        }
        mocked_doc = MagicMock(name="mocked_doc", **doc_dict)
        docs_by_generation = [(mocked_doc, 0, "")]
        self.target.send_doc_info = Mock(return_value=Mock(inserted=False))
        response_dict = {
            "doc_info": [MagicMock(name="doc_info")]
        }
        zmq_target.parse_response = Mock(return_value=Mock(**response_dict),
                                         name="parse_response")

        return_value = {
            "doc_id": Mock(),
            "doc_rev": Mock(),
            "doc_content": Mock(),
            "doc_generation": Mock(),
            "target_generation": Mock()
        }
        self.target.get_doc_at_target = Mock(name="get_doc_at_target",
                                             return_value=return_value)

        zmq_target.Document = Mock(return_value=Mock())

        self.target.sync_exchange(docs_by_generation,
                                  self.source_replica_uid, Mock())

    def test_close(self):
        """
        Tests ZMQSyncTarget.close
        """
        self.assertIsNone(self.target.close())

    def tearDown(self):
        # self.patcher.stop()
        # self.speaker_mock.stop()
        pass
