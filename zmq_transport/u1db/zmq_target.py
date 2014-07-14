"""
SyncTarget API implementation to a remote ZMQ server.
"""
# System Imports
import sys
try:
    import simplejson as json
except ImportError:
    import json

# ZMQ imports
import zmq
from zmq.eventloop.ioloop import PeriodicCallback

# Local Imports
from zmq_transport.client.zmq_client import ZMQClientBase
from zmq_transport.common.errors import UserIDNotSet
from zmq_transport.common import message_pb2 as proto
from zmq_transport.common.utils import (
    serialize_msg,
    deserialize_msg,
    create_zmq_verb_msg,
    create_sync_type_msg,
    create_get_sync_info_request_msg,
    create_put_sync_info_request_msg,
    create_send_document_request_msg,
    create_get_document_request_msg,
    create_all_sent_request_msg,
    parse_response,
    get_sync_id,
    get_doc_info,
    get_source_replica_uid
)

from u1db import (
    SyncTarget,
    Document
)

class ZMQSyncTarget(ZMQClientBase, SyncTarget):
    """
    Implements the SyncTarget API to a remote ZMQ server.
    """
    def __init__(self, endpoints):
        """
        Initializes ZMQSyncTarget instance.
        
        :param endpoints: list of endpoints. endpoints[0] is
                          endpoint_client_handler and endpoints[1] is
                          endpoint_publisher.
        :type endpoints: list
        """
        if isinstance(endpoints, list):
            if len(endpoints) != 2:
                raise ValueError("Length of endpoints must be 2.")
            ZMQClientBase.__init__(self, endpoints[0], endpoints[1])
            self.endpoints = endpoints
            self.sync_required = False
            self.sync_info = None
            self.user_id = None
            # self.target_last_known_generation = None
            # self.target_last_known_trans_id = None
            self.source_current_gen = None
            self.source_current_trans_id = None
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

    def set_user_id(self, user_id):
        """
        Helper method to set the user_id.

        :param user_id: The user_id of the current user.
        :type user_id: str
        """
        self.user_id = user_id

    def release_user_id(self):
        """
        Helper method to reset the user_id.

        :param user_id: The user_id of the current user.
        :type user_id: str
        """
        self.user_id = None

    def check_user_id(self):
        """
        Checks if the user_id is set.
        Raises zmq_transport.common.errors.UserIDNotSet exception.
        """
        if not self.user_id:
            raise UserIDNotSet("User ID is None.")

    def start(self):
        """
        Overridden from zmq_transport.client.zmq_client.ZMQClientBase
        """
        try:
            self.check_user_id()
        except UserIDNotSet, e:
            print "Aborting:", e
            sys.exit()
        else:
            self.speaker.run()
        # poller = zmq.Poller()
        # poller.register(self.speaker._socket, zmq.POLLIN)
        # poller.register(self.updates._socket, zmq.POLLIN)

        # while True:
        #     socks = dict(poller.poll(1000))
        #     if socks.get(self.speaker._socket) == zmq.POLLIN:
        #         pass
        #     elif socks.get(self.updates._socket) == zmq.POLLIN:
        #         pass
        #     else:
        #         self.check_new_sync()

    @staticmethod
    def connect(endpoints):
        """
        Returns ZMQSyncTarget instance

        :param endpoints: list of endpoints. endpoints[0] is
                          endpoint_client_handler and endpoints[1] is
                          endpoint_publisher
        :type endpoints: list
        """
        return ZMQSyncTarget(endpoints[0], endpoints[1])

    def _get_source_generation(self):
        """
        Returns the current source generation.
        # TODO: Implement actual functionality. Arbit for now.
        """
        return 20

    def get_sync_info(self, source_replica_uid):
        """
        Returns the sync state information.

        :return: Last time target was synced with source.
        :rtype: tuple
        """

        print "Entering get_sync_info..."
        # Create GetSyncInfoRequest message.
        sync_id = get_sync_id()
        get_sync_info_struct = create_get_sync_info_request_msg(
            user_id=self.user_id, source_replica_uid=source_replica_uid,
            sync_id=sync_id)
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
        Informs the target, about source's latest state after completion of the
        sync_exchange.

        :return: source_transaction_id and inserted status.
        :rtype: tuple
        """
        print "Entering record_sync_info..."
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

    def send_doc_info(self, source_replica_uid, sync_id, doc_id, doc_rev,
                      doc_generation, doc_content, source_generation,
                      source_transaction_id, target_last_known_generation,
                      target_last_known_trans_id):
        """
        After "GetSyncInfoRequest" message has been sent and
        "GetSyncInfoResponse" is received, the source will now know which
        documents have changed at source since the last sync. This method is
        used to send those those documents one at a time to the target.

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

        :return: source_transaction_id and inserted status.
        :rtype: tuple
        """
        print ">>>>>>>>", target_last_known_trans_id, target_last_known_generation
        # Create SendDocumentRequest message.
        send_doc_req_struct = create_send_document_request_msg(
            user_id=self.user_id, source_replica_uid=source_replica_uid,
            sync_id=sync_id, doc_id=doc_id, doc_rev=doc_rev,
            doc_generation=doc_generation, doc_content=doc_content,
            source_generation=source_generation,
            source_transaction_id=str(source_transaction_id),
            target_last_known_generation=target_last_known_generation,
            target_last_known_trans_id=str(target_last_known_trans_id))
        iden_send_doc_req = proto.Identifier(
            type=proto.Identifier.SEND_DOCUMENT_REQUEST,
            send_document_request=send_doc_req_struct)
        str_iden_send_doc_req = serialize_msg(iden_send_doc_req)

        # Create SyncType message.
        sync_type_struct = create_sync_type_msg(sync_type="sync-from")
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
                          docs_received_count, target_last_known_generation,
                          target_last_known_trans_id):
        """
        Sends a GetDocumentRequest to target to receive documents that were
        changed at the target replica.

        :param source_replica_uid: The identifier of the source replica.
        :type source_replica_uid: str
        :param sync_id: The sync id of the current sync in process.
        :type sync_id: str
        :param docs_received_count: Total count of docs received.
        :type docs_received_count: int

        :return: A document from the target.
        :rtype: dict
        """
        # Create GetDocumentRequest message.
        get_doc_req_struct = create_get_document_request_msg(
            user_id=self.user_id, source_replica_uid=source_replica_uid,
            sync_id=sync_id, docs_received_count=docs_received_count,
            target_last_known_generation=target_last_known_generation,
            target_last_known_trans_id=target_last_known_trans_id)
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
                "doc_rev": response.doc_rev,
                "doc_generation":response.doc_generation,
                "doc_content": response.doc_content,
                "target_generation": response.target_generation,
                "target_trans_id": response.target_trans_id}

    def sync_exchange(self, docs_by_generation, source_replica_uid,
                      last_known_generation, last_known_trans_id,
                      return_doc_cb, ensure_callback=None):
        """
        Send docs changed at source one at a time, and then incorporate docs
        changed at target.

        :param docs_by_generation: A list of documents sorted by generation to
                                   send to target.
        :type docs_by_generation: list
        :param source_replica_uid: Unique identifier of replica at source.
        :type source_replica_uid: str
        :param last_known_generation: Last known generation of the target.
        :type last_known_generation: int
        :param last_known_trans_id: Last known transaction id of the target.
        :type last_known_trans_id: str
        :param return_doc_cb: Callback method to invoke when a document is
                              received.
        :type return_doc_cb: method
        :param ensure_callback: Callback for tests.
        :type ensure_callback: method.

        :return: Latest transaction generation and id of target.
        :rtype: tuple
        """
        print "Entering sync_exchange..."
        # Send docs changed at source.
        source_transaction_id = "TRANS-ID" # has to be unique.
        sync_id = get_sync_id()
        for doc, gen, trans_id in docs_by_generation:
            source_transaction_id, inserted = self.send_doc_info(
                source_replica_uid, sync_id, doc.doc_id, doc.rev, gen,
                doc.get_json(), self.source_current_gen,
                self.source_current_trans_id, last_known_generation,
                last_known_trans_id)
            if not inserted:
                # TODO: Maybe retry? or Report?
                pass

        # Intermediate PING-ACK. Also gets notified about incoming
        # docs beforehand.
        all_sent_req_struct = create_all_sent_request_msg(
            user_id=self.user_id, source_replica_uid=source_replica_uid,
            total_docs_sent=len(docs_by_generation), all_sent=True,
            target_last_known_generation=last_known_generation,
            target_last_known_trans_id=last_known_trans_id)
        iden_all_sent_req = proto.Identifier(
            type=proto.Identifier.ALL_SENT_REQUEST,
            all_sent_request=all_sent_req_struct)
        str_iden_all_sent_req = serialize_msg(iden_all_sent_req)

        import pdb
        pdb.set_trace()
        # Frame 1: AllSentRequest
        self.speaker.send([str_iden_all_sent_req])

        # Frame 1: AllSentResponse
        response = self.speaker.recv()[0]
        response = parse_response(response, "all_sent_response")

        # TODO: What to do with response.doc_info[] ; Maybe request
        # for each doc by id?
        docs_list = response.doc_info[:]

        docs_to_receive = len(response.doc_info)
        docs_received = 0
        while docs_to_receive != 0:
            doc_recvd = self.get_doc_at_target(source_replica_uid, sync_id,
                                               docs_received,
                                               last_known_generation,
                                               last_known_trans_id)
            if doc_recvd.get("doc_id"):
                docs_received += 1
                docs_to_receive -= 1
                doc = Document(doc_recvd["doc_id"], doc_recvd["doc_rev"],
                               doc_recvd["doc_content"])
                return_doc_cb(doc, doc_recvd["doc_generation"],
                              doc_recvd["target_generation"])

        return response.target_generation, response.target_trans_id


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

            # Unpacking response
            target_replica_uid, self.target_last_known_generation,\
                self.target_last_known_trans_id, source_last_known_generation,\
                source_last_known_trans_id = sync_info_response

            # Simulating docs_by_generation
            from u1db import Document
            from uuid import uuid4
            docs_by_generation = []
            for i in range(1, 6):
                doc_id = str(uuid4())
                doc_content = {"data": "Random bits of data."}
                doc_content = json.dumps(doc_content)
                doc = Document(doc_id=doc_id, rev=0, json=doc_content)
                trans_id = str(uuid4())
                docs_by_generation.append((doc, i, trans_id))

            # Dummy method to simulate sync_exchange smoothly. Will be removed.
            def return_doc_cb(*args):
                pass
            # Sync exchange.
            print "Sync Exchange: "
            print self.sync_exchange(docs_by_generation, source_replica_uid,
                                     source_last_known_generation,
                                     source_last_known_trans_id, return_doc_cb)

            record_sync_response =  self.record_sync_info(
                source_replica_uid, sync_info_response[3],
                sync_info_response[4])
            print record_sync_response

            self.sync_required = False
        else:
            # TODO: Some client side event that will indicate if sync
            # is instigated or not.
            # self.sync_required = client_event()
            self.sync_required = True

    ################### End of Application logic handlers. ####################

    def close(self):
        pass
