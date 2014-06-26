# System Imports
import unittest

# Local Imports
from zmq_transport.common import message_pb2 as proto
from zmq_transport.common.utils import *


class BaseMessageTest(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        unittest.TestCase.__init__(self, *args, **kwargs)
        self.msg_struct = None

    def tearDown(self):
        self.msg_struct = None


class SubscribeRequestTest(BaseMessageTest):

    def setUp(self):
        self.msg_struct = create_subscribe_request_msg(key="TEST")

    def test_create_subscribe_request_msg(self):
        self.assertIsInstance(self.msg_struct, proto.SubscribeRequest)
        self.assertEqual(self.msg_struct.key, "TEST")

    def test_serialize_msg(self):
        serialized_str = serialize_msg(self.msg_struct)
        parsed_msg_struct = deserialize_msg("SubscribeRequest", serialized_str)
        self.assertIsInstance(parsed_msg_struct, proto.SubscribeRequest)
        self.assertEqual(self.msg_struct.key, parsed_msg_struct.key)


class UnsubscribeRequestTest(BaseMessageTest):

    def setUp(self):
        self.msg_struct = create_unsubscribe_request_msg(key="TEST")

    def test_create_unsubscribe_request_msg(self):
        self.assertIsInstance(self.msg_struct, proto.UnsubscribeRequest)
        self.assertEqual(self.msg_struct.key, "TEST")

    def test_serialize_msg(self):
        serialized_str = serialize_msg(self.msg_struct)
        parsed_msg_struct = deserialize_msg("UnsubscribeRequest", serialized_str)
        self.assertIsInstance(parsed_msg_struct, proto.UnsubscribeRequest)
        self.assertEqual(self.msg_struct.key, parsed_msg_struct.key)


class SyncTypeTest(BaseMessageTest):

    def setUp(self):
        self.msg_struct = create_sync_type_msg(sync_type="TEST")

    def test_create_sync_type_msg(self):
        self.assertIsInstance(self.msg_struct, proto.SyncType)
        self.assertEqual(self.msg_struct.sync_type, "TEST")

    def test_serialize_msg(self):
        serialized_str = serialize_msg(self.msg_struct)
        parsed_msg_struct = deserialize_msg("SyncType", serialized_str)
        self.assertIsInstance(parsed_msg_struct, proto.SyncType)
        self.assertEqual(self.msg_struct.sync_type,
                         parsed_msg_struct.sync_type)


class ZMQVerbTest(BaseMessageTest):

    def setUp(self):
        self.msg_struct = create_zmq_verb_msg(verb=proto.ZMQVerb.GET)

    def test_create_zmq_verb_msg(self):
        self.assertIsInstance(self.msg_struct, proto.ZMQVerb)
        self.assertEqual(self.msg_struct.verb, proto.ZMQVerb.GET)
        self.msg_struct = create_zmq_verb_msg(verb=proto.ZMQVerb.POST)
        self.assertEqual(self.msg_struct.verb, proto.ZMQVerb.POST)
        self.msg_struct = create_zmq_verb_msg(verb=proto.ZMQVerb.PUT)
        self.assertEqual(self.msg_struct.verb, proto.ZMQVerb.PUT)
        self.msg_struct = create_zmq_verb_msg(verb=proto.ZMQVerb.DELETE)
        self.assertEqual(self.msg_struct.verb, proto.ZMQVerb.DELETE)

    def test_serialize_msg(self):
        serialized_str = serialize_msg(self.msg_struct)
        parsed_msg_struct = deserialize_msg("ZMQVerb", serialized_str)
        self.assertIsInstance(parsed_msg_struct, proto.ZMQVerb)
        self.assertEqual(self.msg_struct.verb, parsed_msg_struct.verb)


class GetSyncInfoRequestTest(BaseMessageTest):

    def setUp(self):
        self.msg_struct = create_get_sync_info_request_msg(
            source_replica_uid="UID1", sync_id="SYNC1")
        
    def test_create_get_sync_info_request_msg(self):
        self.assertIsInstance(self.msg_struct, proto.GetSyncInfoRequest)
        self.assertEqual(self.msg_struct.source_replica_uid, "UID1")
        self.assertEqual(self.msg_struct.sync_id, "SYNC1")

    def test_serialize_msg(self):
        serialized_str = serialize_msg(self.msg_struct)
        parsed_msg_struct = deserialize_msg("GetSyncInfoRequest", serialized_str)
        self.assertIsInstance(parsed_msg_struct, proto.GetSyncInfoRequest)
        self.assertEqual(parsed_msg_struct.source_replica_uid, "UID1")
        self.assertEqual(parsed_msg_struct.sync_id, "SYNC1")


class GetSyncInfoResponseTest(BaseMessageTest):

    def setUp(self):
        self.msg_struct = create_get_sync_info_response_msg(
            target_replica_uid="T-UID", target_replica_generation=1,
            target_replica_trans_id="TRANS-ID", source_last_known_generation=2,
            source_last_known_trans_id = "LAST_TRANS_ID")

    def test_create_get_sync_info_response_msg(self):
        self.assertIsInstance(self.msg_struct, proto.GetSyncInfoResponse)
        self.assertEqual(self.msg_struct.target_replica_uid, "T-UID")
        self.assertEqual(self.msg_struct.target_replica_generation, 1)
        self.assertEqual(self.msg_struct.target_replica_trans_id, "TRANS-ID")
        self.assertEqual(self.msg_struct.source_last_known_generation, 2)
        self.assertEqual(self.msg_struct.source_last_known_trans_id,
                         "LAST_TRANS_ID")

    def test_serialize_msg(self):
        serialized_str = serialize_msg(self.msg_struct)
        parsed_msg_struct = deserialize_msg("GetSyncInfoResponse", serialized_str)
        self.assertIsInstance(parsed_msg_struct, proto.GetSyncInfoResponse)
        self.assertEqual(parsed_msg_struct.target_replica_uid, "T-UID")
        self.assertEqual(parsed_msg_struct.target_replica_generation, 1)
        self.assertEqual(parsed_msg_struct.target_replica_trans_id, "TRANS-ID")
        self.assertEqual(parsed_msg_struct.source_last_known_generation, 2)
        self.assertEqual(parsed_msg_struct.source_last_known_trans_id,
                         "LAST_TRANS_ID")


class SendDocumentRequestTest(BaseMessageTest):

    def setUp(self):
        self.msg_struct = create_send_document_request_msg(
            source_replica_uid="UID1", sync_id="SYNC1", doc_id="DOC1",
            doc_generation=1, doc_content="Dummy text.", source_generation=2,
            source_transaction_id="TRANS-ID")

    def test_create_send_document_request_msg(self):
        self.assertIsInstance(self.msg_struct, proto.SendDocumentRequest)
        self.assertEqual(self.msg_struct.source_replica_uid, "UID1")
        self.assertEqual(self.msg_struct.sync_id, "SYNC1")
        self.assertEqual(self.msg_struct.doc_id, "DOC1")
        self.assertEqual(self.msg_struct.doc_generation, 1)
        self.assertEqual(self.msg_struct.doc_content, "Dummy text.")
        self.assertEqual(self.msg_struct.source_generation, 2)
        self.assertEqual(self.msg_struct.source_transaction_id, "TRANS-ID")

    def test_serialize_msg(self):
        serialized_str = serialize_msg(self.msg_struct)
        parsed_msg_struct = deserialize_msg("SendDocumentRequest", serialized_str)
        self.assertIsInstance(parsed_msg_struct, proto.SendDocumentRequest)
        self.assertEqual(parsed_msg_struct.source_replica_uid, "UID1")
        self.assertEqual(parsed_msg_struct.sync_id, "SYNC1")
        self.assertEqual(parsed_msg_struct.doc_id, "DOC1")
        self.assertEqual(parsed_msg_struct.doc_generation, 1)
        self.assertEqual(parsed_msg_struct.doc_content, "Dummy text.")
        self.assertEqual(parsed_msg_struct.source_generation, 2)
        self.assertEqual(parsed_msg_struct.source_transaction_id, "TRANS-ID")


class SendDocumentResponseTest(BaseMessageTest):

    def setUp(self):
        self.msg_struct = create_send_document_response_msg(
            source_transaction_id="TRANS-ID", inserted=True)

    def test_create_send_document_response_msg(self):
        self.assertIsInstance(self.msg_struct, proto.SendDocumentResponse)
        self.assertEqual(self.msg_struct.source_transaction_id, "TRANS-ID")
        self.assertEqual(self.msg_struct.inserted, True)
        self.msg_struct.inserted = False
        self.assertEqual(self.msg_struct.inserted, False)

    def test_serialize_msg(self):
        serialized_str = serialize_msg(self.msg_struct)
        parsed_msg_struct = deserialize_msg("SendDocumentResponse", serialized_str)
        self.assertIsInstance(parsed_msg_struct, proto.SendDocumentResponse)
        self.assertEqual(parsed_msg_struct.source_transaction_id, "TRANS-ID")
        self.assertEqual(parsed_msg_struct.inserted, True)


class DocInfoTest(BaseMessageTest):

    def setUp(self):
        self.msg_struct = create_doc_info_msg(doc_id="DOC-ID", doc_generation=2)

    def test_create_doc_info_msg(self):
        self.assertIsInstance(self.msg_struct, proto.DocInfo)
        self.assertEqual(self.msg_struct.doc_id, "DOC-ID")
        self.assertEqual(self.msg_struct.doc_generation, 2)

    def test_serialize_msg(self):
        serialized_str = serialize_msg(self.msg_struct)
        parsed_msg_struct = deserialize_msg("DocInfo", serialized_str)
        self.assertIsInstance(parsed_msg_struct, proto.DocInfo)
        self.assertEqual(parsed_msg_struct.doc_id, "DOC-ID")
        self.assertEqual(parsed_msg_struct.doc_generation, 2)


class AllSentRequestTest(BaseMessageTest):

    def setUp(self):
        self.msg_struct = create_all_sent_request_msg(total_docs_sent=4,
                                                      all_sent=True)

    def test_create_all_sent_request_msg(self):
        self.assertIsInstance(self.msg_struct, proto.AllSentRequest)
        self.assertEqual(self.msg_struct.total_docs_sent, 4)
        self.assertEqual(self.msg_struct.all_sent, True)
        self.msg_struct.all_sent = False
        self.assertEqual(self.msg_struct.all_sent, False)

    def test_serialize_msg(self):
        serialized_str = serialize_msg(self.msg_struct)
        parsed_msg_struct = deserialize_msg("AllSentRequest", serialized_str)
        self.assertIsInstance(parsed_msg_struct, proto.AllSentRequest)
        self.assertEqual(parsed_msg_struct.total_docs_sent, 4)
        self.assertEqual(parsed_msg_struct.all_sent, True)


class AllSentResponseTest(BaseMessageTest):

    def setUp(self):
        self.items = [("D1", 2), ("D2", 4), ("D3", 9), ("D4", 5)]
        self.msg_struct = create_all_sent_response_msg(
            items=self.items, target_generation=20, target_trans_id="TRANS-ID")

    def test_create_all_sent_response_msg(self):
        self.assertIsInstance(self.msg_struct, proto.AllSentResponse)
        self.assertEqual(self.msg_struct.target_generation, 20)
        self.assertEqual(self.msg_struct.target_trans_id, "TRANS-ID")
        self.assertEqual(len(self.msg_struct.doc_info), len(self.items))
        for i in range(len(self.items)):
            self.assertEqual(self.msg_struct.doc_info[i].doc_id, self.items[i][0])
            self.assertEqual(self.msg_struct.doc_info[i].doc_generation,
                             self.items[i][1])

    def test_serialize_msg(self):
        serialized_str = serialize_msg(self.msg_struct)
        parsed_msg_struct = deserialize_msg("AllSentResponse", serialized_str)
        self.assertIsInstance(parsed_msg_struct, proto.AllSentResponse)
        self.assertEqual(parsed_msg_struct.target_generation, 20)
        self.assertEqual(parsed_msg_struct.target_trans_id, "TRANS-ID")
        self.assertEqual(len(parsed_msg_struct.doc_info), len(self.items))


class GetDocumentRequestTest(BaseMessageTest):

    def setUp(self):
        self.msg_struct = create_get_document_request_msg(
            source_replica_uid="REP-UID", sync_id="SYNC1",
            docs_received_count=2)

    def test_create_get_document_request_msg(self):
        self.assertIsInstance(self.msg_struct, proto.GetDocumentRequest)
        self.assertEqual(self.msg_struct.source_replica_uid, "REP-UID")
        self.assertEqual(self.msg_struct.sync_id, "SYNC1")
        self.assertEqual(self.msg_struct.docs_received_count, 2)

    def test_serialize_msg(self):
        serialized_str = serialize_msg(self.msg_struct)
        parsed_msg_struct = deserialize_msg("GetDocumentRequest", serialized_str)
        self.assertIsInstance(parsed_msg_struct, proto.GetDocumentRequest)
        self.assertEqual(parsed_msg_struct.source_replica_uid, "REP-UID")
        self.assertEqual(parsed_msg_struct.sync_id, "SYNC1")
        self.assertEqual(parsed_msg_struct.docs_received_count, 2)


class GetDocumentResponseTest(BaseMessageTest):

    def setUp(self):
        self.msg_struct = create_get_document_response_msg(
            doc_id="DOC1", doc_rev=2, doc_generation=1, doc_content="Dummy text.",
            target_generation=2, target_trans_id="TAR-ID")

    def test_create_get_document_response_msg(self):
        self.assertIsInstance(self.msg_struct, proto.GetDocumentResponse)
        self.assertEqual(self.msg_struct.doc_id, "DOC1")
        self.assertEqual(self.msg_struct.doc_rev, 2)
        self.assertEqual(self.msg_struct.doc_generation, 1)
        self.assertEqual(self.msg_struct.doc_content, "Dummy text.")
        self.assertEqual(self.msg_struct.target_generation, 2)
        self.assertEqual(self.msg_struct.target_trans_id, "TAR-ID")

    def test_serialize_msg(self):
        serialized_str = serialize_msg(self.msg_struct)
        parsed_msg_struct = deserialize_msg("GetDocumentResponse", serialized_str)
        self.assertIsInstance(parsed_msg_struct, proto.GetDocumentResponse)
        self.assertEqual(parsed_msg_struct.doc_id, "DOC1")
        self.assertEqual(parsed_msg_struct.doc_generation, 1)
        self.assertEqual(parsed_msg_struct.doc_content, "Dummy text.")
        self.assertEqual(parsed_msg_struct.target_generation, 2)
        self.assertEqual(parsed_msg_struct.target_trans_id, "TAR-ID")


class PutSyncInfoRequestTest(BaseMessageTest):

    def setUp(self):
        self.msg_struct = create_put_sync_info_request_msg(
            sync_id="SYNC1", source_replica_uid="REP-ID", source_replica_generation=1,
            source_transaction_id="TRANS-ID")

    def test_create_put_sync_info_request_msg(self):
        self.assertIsInstance(self.msg_struct, proto.PutSyncInfoRequest)
        self.assertEqual(self.msg_struct.sync_id, "SYNC1")
        self.assertEqual(self.msg_struct.source_replica_uid, "REP-ID")
        self.assertEqual(self.msg_struct.source_replica_generation, 1)
        self.assertEqual(self.msg_struct.source_transaction_id, "TRANS-ID")

    def test_serialize_msg(self):
        serialized_str = serialize_msg(self.msg_struct)
        parsed_msg_struct = deserialize_msg("PutSyncInfoRequest",
                                            serialized_str)
        self.assertIsInstance(parsed_msg_struct, proto.PutSyncInfoRequest)
        self.assertEqual(parsed_msg_struct.sync_id, "SYNC1")
        self.assertEqual(parsed_msg_struct.source_replica_uid, "REP-ID")
        self.assertEqual(parsed_msg_struct.source_replica_generation, 1)
        self.assertEqual(parsed_msg_struct.source_transaction_id, "TRANS-ID")


class PutSyncInfoResponseTest(BaseMessageTest):

    def setUp(self):
        self.msg_struct = create_put_sync_info_response_msg(
            source_transaction_id="TRANS-ID", inserted=True)

    def test_create_put_sync_info_response_msg(self):
        self.assertIsInstance(self.msg_struct, proto.PutSyncInfoResponse)
        self.assertEqual(self.msg_struct.source_transaction_id, "TRANS-ID")
        self.assertEqual(self.msg_struct.inserted, True)
        self.msg_struct.inserted = False
        self.assertEqual(self.msg_struct.inserted, False)

    def test_serialize_msg(self):
        serialized_str = serialize_msg(self.msg_struct)
        parsed_msg_struct = deserialize_msg("PutSyncInfoResponse", serialized_str)
        self.assertIsInstance(parsed_msg_struct, proto.PutSyncInfoResponse)
        self.assertEqual(parsed_msg_struct.source_transaction_id, "TRANS-ID")
        self.assertEqual(parsed_msg_struct.inserted, True)


class IdentifierTest(BaseMessageTest):
    pass

