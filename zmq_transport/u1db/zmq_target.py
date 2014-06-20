"""
SyncTarget API implementation to a remote ZMQ server.
"""

# ZMQ imports
import zmq
from zmq.eventloop.ioloop import PeriodicCallback

# Local Imports
from zmq_transport.client.zmq_client import ZMQClientBase
from zmq_transport.common import message_pb2 as proto
from zmq_transport.common.utils import create_zmq_verb_msg,\
    create_sync_type_msg, create_get_sync_info_request_msg, serialize_msg,\
    deserialize_msg, get_sync_id, create_put_sync_info_request_msg,\
    create_send_document_request_msg, create_get_document_request_msg,\
    parse_response, get_doc_info, get_source_replica_uid
from zmq_transport.u1db import SyncTarget


class ZMQSyncTarget(ZMQClientBase, SyncTarget):
    """
    Implements the SyncTarget API to a remote ZMQ server.
    """
    def __init__(self, endpoints):
        """
        Initializes ZMQSyncTarget instance.
        
        :param endpoints: list of endpoints. endpoints[0] is
        endpoint_client_handler and endpoints[1] is endpoint_publisher.
        :type endpoints: list
        """
        if isinstance(endpoints, list):
            assert (len(endpoints) == 2), "Length of endpoints must be 2."
            ZMQClientBase.__init__(self, endpoints[0], endpoints[1])
            self.endpoints = endpoints
            self.sync_required = False
            self.sync_info = None
        else:
            raise TypeError("Expected type(endpoints) list. Got %s" %
                            (type(endpoints)))

    def _prepare_reactor(self):
        """
        Overridden from zmq_transport.client.zmq_client.ZMQClientBase
        Raises NotImplementedError because ZMQSyncTarget is using poller for
        now.
        """
        raise NotImplementedError("Target uses zmq.Poller()")

    def start(self):
        """
        Overridden from zmq_transport.client.zmq_client.ZMQClientBase
        """
        self.speaker.run()
        poller = zmq.Poller()
        poller.register(self.speaker._socket, zmq.POLLIN)
        poller.register(self.updates._socket, zmq.POLLIN)

        while True:
            socks = dict(poller.poll(1000))
            if socks.get(self.speaker._socket) == zmq.POLLIN:
                pass
            elif socks.get(self.updates._socket) == zmq.POLLIN:
                pass
            else:
                self.check_new_sync()

    @staticmethod
    def connect(endpoints):
        """
        Returns ZMQSyncTarget instance

        :param endpoints: list of endpoints. endpoints[0] is endpoint_client_handler and
                          endpoints[1] is endpoint_publisher
        :type endpoints: list
        """
        return ZMQSyncTarget(endpoints[0], endpoints[1])

    def get_sync_info(self, source_replica_uid):
        """
        Returns the sync state information.

        :returns: tuple
        """
        # Create GetSyncInfoRequest message.
        sync_id = get_sync_id()
        get_sync_info_struct = create_get_sync_info_request_msg(
            source_replica_uid=source_replica_uid, sync_id=sync_id)
        iden_get_sync_info_struct = proto.Identifier(
            type=proto.Identifier.GET_SYNC_INFO_REQUEST,
            get_sync_info_request=get_sync_info_struct)
        str_iden_get_sync_info = serialize_msg(iden_get_sync_info_struct)

        # TODO: Wrapping sync_type and zmq_verb messages in Identifier
        # message now. Might remove. Probably not required.

        # Create SyncType message.
        sync_type_struct = create_sync_type_msg(sync_type="sync-from")
        iden_sync_type_struct = proto.Identifier(
            type=proto.Identifier.SYNC_TYPE, sync_type=sync_type_struct)
        str_iden_sync_type = serialize_msg(iden_sync_type_struct)

        # Create ZMQVerb message.
        zmq_verb_struct = create_zmq_verb_msg(verb=proto.ZMQVerb.GET)
        iden_zmq_verb_struct = proto.Identifier(type=proto.Identifier.ZMQ_VERB,
                                         zmq_verb=zmq_verb_struct)
        str_iden_zmq_verb = serialize_msg(iden_zmq_verb_struct)

        # Frame 1: ZMQVerb; Frame 2: SyncType; Frame 3:GetSyncInfoRequest
        to_send = [str_iden_zmq_verb, str_iden_sync_type, str_iden_get_sync_info]
        self.speaker.send(to_send)

        # Frame 1: GetSyncInfoResponse;
        response = self.speaker.recv()[0]
        response =  parse_response(response, "get_sync_info_response")
        return (response.target_replica_uid, response.target_replica_generation,
                response.target_replica_trans_id,
                response.source_last_known_generation,
                response.source_last_known_trans_id)

    def record_sync_info(self, source_replica_uid, source_replica_generation,
                         source_transaction_id):
        """
        Informs the target, about its latest state after completion of the
        sync_exchange.

        :returns: source_transaction_id and inserted status.
        :type: tuple
        """
        # Create PutSyncInfoRequest message.
        sync_id = get_sync_id() # Might have to pass this as a param
        # too or might not be needed at all.
        put_sync_info_struct = create_put_sync_info_request_msg(
            sync_id=sync_id, source_replica_uid=source_replica_uid,
            source_replica_generation=source_replica_generation,
            source_transaction_id=source_transaction_id)
        iden_put_sync_info_struct = proto.Identifier(
            type=proto.Identifier.PUT_SYNC_INFO_REQUEST,
            put_sync_info_request=put_sync_info_struct)
        str_iden_put_sync_info = serialize_msg(iden_put_sync_info_struct)

        # Create SyncType message.
        sync_type_struct = create_sync_type_msg(sync_type="sync-from")
        iden_sync_type = proto.Identifier(type=proto.Identifier.SYNC_TYPE,
                                          sync_type=sync_type_struct)
        str_iden_sync_type = serialize_msg(iden_sync_type)

        # Create ZMQVerb message.
        zmq_verb_struct = create_zmq_verb_msg(verb=proto.ZMQVerb.PUT)
        iden_zmq_verb_struct = proto.Identifier(type=proto.Identifier.ZMQ_VERB,
                                         zmq_verb=zmq_verb_struct)
        str_iden_zmq_verb = serialize_msg(iden_zmq_verb_struct)

        to_send = [str_iden_zmq_verb, str_iden_sync_type, str_iden_put_sync_info]
        self.speaker.send(to_send)

        # Frame 1: PutSyncInfoResponse;
        response = self.speaker.recv()[0]
        response = parse_response(response, "put_sync_info_response")
        return (response.source_transaction_id, response.inserted)

    def _parse_sync_stream(self, data, return_doc_cb, ensure_callback=None):
        pass

    def send_doc_info(self, source_replica_uid, sync_id, doc_id,
                      doc_generation, doc_content, source_generation,
                      source_transaction_id):
        """
        After "GetSyncInfoRequest" message has been sent and
        "GetSyncInfoResponse" is received, the source will now know which
        documents have changed at source since the last sync. This method is
        used to send those those documents one at a time.

        :param source_replica_uid: The uid that identifies the source db.
        :type source_replica_uid: str
        :param sync_id: The uid that identifies a particular sync.
        :type sync_id: str
        :param doc_id: The uid that identifies a particular document.
        :type doc_id: str
        :param doc_generation: Generation of the document.
        :type doc_generation: int
        :param doc_content: Contents of the document.
        :type doc_content: str
        :param source_replica_uid: The uid that identifies the source db.
        :param sync_id: The uid that identifies a particular sync.
        :param source_generation: Generation at source.
        :type source_generation: int
        :param source_transaction_id: The current transaction id at source.
        :type source_transaction_id: str

        :returns: source_transaction_id and inserted status.
        :type: tuple
        """
        # Create SendDocumentRequest message.
        send_doc_req_struct = create_send_document_request_msg(
            source_replica_uid=source_replica_uid, sync_id=sync_id,
            doc_id=doc_id, doc_generation=doc_generation,
            doc_content=doc_content, source_generation=source_generation,
            source_transaction_id=source_transaction_id)
        iden_send_doc_req = proto.Identifier(
            type=proto.Identifier.SEND_DOCUMENT_REQUEST,
            send_document_request=send_doc_req_struct)
        str_iden_send_doc_req = serialize_msg(iden_send_doc_req)

        # Create SyncType message.
        sync_type_struct = create_sync_type_msg(sync_type="sync-to")
        iden_sync_type = proto.Identifier(type=proto.Identifier.SYNC_TYPE,
                                          sync_type=sync_type_struct)
        str_iden_sync_type = serialize_msg(iden_sync_type)

        # Create ZMQVerb message
        zmq_verb_struct = create_zmq_verb_msg(verb=proto.ZMQVerb.POST)
        iden_zmq_verb = proto.Identifier(type=proto.Identifier.ZMQ_VERB,
                                         zmq_verb=zmq_verb_struct)
        str_iden_zmq_verb = serialize_msg(iden_zmq_verb)

        # Frame 1: ZMQVerb; Frame 2: SyncType; Frame 3: SendDocumentRequest;
        to_send = [str_iden_zmq_verb, str_iden_sync_type, str_iden_send_doc_req]
        self.speaker.send(to_send)

        # Frame 1: SendDocumentResponse;
        response = self.speaker.recv()[0]
        response = parse_response(response, "send_document_response")
        return (response.source_transaction_id, response.inserted)

    def get_doc_at_target(self, source_replica_uid, sync_id,
                          docs_received_count):
        """
        Sends a GetDocumentRequest to target to receive documents that were
        changed at the target replica.

        :param source_replica_uid: The identifier of the source replica.
        :type source_replica_uid: str
        :param sync_id: The sync id of the current sync in process.
        :type sync_id: str
        :param docs_received_count: Total count of docs received.
        :type docs_received_count: int

        :returns: dict
        """
        # Create GetDocumentRequest message.
        get_doc_req_struct = create_get_document_request_msg(
            source_replica_uid=source_replica_uid, sync_id=sync_id,
            docs_received_count=docs_received_count)
        iden_get_doc_req = proto.Identifier(
            type=proto.Identifier.GET_DOCUMENT_REQUEST,
            get_document_request=get_doc_req_struct)
        str_iden_get_doc_req = serialize_msg(iden_get_doc_req)

        # Create SyncType message.
        sync_type_struct = create_sync_type_msg(sync_type="sync-from")
        iden_sync_type = proto.Identifier(type=proto.Identifier.SYNC_TYPE,
                                          sync_type=sync_type_struct)
        str_iden_sync_type = serialize_msg(iden_sync_type)

        # Create ZMQVerb message
        zmq_verb_struct = create_zmq_verb_msg(verb=proto.ZMQVerb.GET)
        iden_zmq_verb = proto.Identifier(type=proto.Identifier.ZMQ_VERB,
                                         zmq_verb=zmq_verb_struct)
        str_iden_zmq_verb = serialize_msg(iden_zmq_verb)

        # Frame 1: ZMQVerb; Frame 2: SyncType; Frame 3: GetDocumentRequest
        to_send = [str_iden_zmq_verb, str_iden_sync_type, str_iden_get_doc_req]
        self.speaker.send(to_send)

        # Frame 1: GetDocumentResponse
        response = self.speaker.recv()[0]
        response = parse_response(response, "get_document_response")
        return {"doc_id": response.doc_id,
                "doc_generation":response.doc_generation,
                "doc_content": response.doc_content,
                "target_generation": response.target_generation,
                "target_trans_id": response.target_trans_id}

    def sync_exchange(self, docs_by_generation, source_replica_uid,
                      last_known_generation, last_known_trans_id,
                      return_doc_cb, ensure_callback=None):
        """
        Incorporate the documents sent from the source replica.
        """
        pass

    ################### Start of Application logic handlers. ##################

    def check_new_sync(self):
        """
        Method to check if new sync is required.
        """
        if self.sync_required:
            source_replica_uid = get_source_replica_uid()
            sync_info_response = self.get_sync_info(source_replica_uid)
            print sync_info_response

            sync_id = get_sync_id() # Ideally will be set as an
            # attribute of sync.
            doc_id, doc_generation, doc_content = get_doc_info()
            send_doc_response = self.send_doc_info(
                source_replica_uid, sync_id, doc_id, doc_generation, doc_content,
                25, sync_info_response[4])
            print send_doc_response

            target_docs_response = self.get_doc_at_target(source_replica_uid,
                                                          sync_id, 0)
            print target_docs_response
            # record_sync_response =  self.record_sync_info(
            #     source_replica_uid, sync_info_response[3],
            #     sync_info_response[4])


            self.sync_required = False
        else:
            # TODO: Some client side event that will indicate if sync
            # is instigated or not.
            # self.sync_required = client_event()
            self.sync_required = True

    ################### End of Application logic handlers. ####################

