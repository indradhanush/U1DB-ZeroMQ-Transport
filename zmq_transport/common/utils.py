"""
Common Utilities.
"""
# System Imports
import uuid
try:
    import simplejson as json
except ImportError:
    import json

# Protobuf Imports
from google.protobuf.message import DecodeError

# Local Imports
from zmq_transport.common import message_pb2 as proto


######################## Start of Protobuf utilities. ########################

def _create_protobuf_msg(protobuf_type, **kwargs):
    """
    Creates a protobuf message defined in message.proto
    :param protobuf_type: Type of message structure.
    :type protobuf_type: str
    :param kwargs: A dictionary containing key value pairs of attributes and
                   their respective values of "protobuf_type" message structure.
    :type kwargs: dict

    :return: A protobuf message struct.
    :rtype: zmq_transport.common.message_pb2
    """
    msg_struct = getattr(proto, protobuf_type)()
    for key, value in kwargs.items():
        setattr(msg_struct, key, value)
    return msg_struct


def create_subscribe_request_msg(**kwargs):
    """
    Creates a zmq_transport.common.message_pb2.SubscribeRequest message
    structure.

    :param kwargs: A dictionary containing key value pairs of attributes and
                   their respective values of SubscribeRequest message
                   structure.
    :type kwargs: dict

    :return: SubscribeRequest message.
    :rtype: zmq_transport.common.message_pb2.SubscribeRequest
    """
    return _create_protobuf_msg("SubscribeRequest", **kwargs)


def create_unsubscribe_request_msg(**kwargs):
    """
    Creates a zmq_transport.common.message_pb2.UnsubscribeRequest message
    structure.

    :param kwargs: A dictionary containing key value pairs of attributes and
                   their respective values of UnsubscribeRequest message
                   structure.
    :type kwargs: dict

    :return: UnsubscribeRequest message.
    :rtype: zmq_transport.common.message_pb2.UnsubscribeRequest
    """
    return _create_protobuf_msg("UnsubscribeRequest", **kwargs)


def create_sync_type_msg(**kwargs):
    """
    Creates a zmq_transport.common.message_pb2.SyncType message structure.

    :param kwargs: A dictionary containing key value pairs of attributes and
                   their respective values of SyncType message structure.
    :type kwargs: dict

    :return: SyncType message.
    :rtype: zmq_transport.common.message_pb2.SyncType
    """
    return _create_protobuf_msg("SyncType", **kwargs)


def create_zmq_verb_msg(**kwargs):
    """
    Creates a zmq_transport.common.message_pb2.ZMQVerb message structure.

    :param kwargs: A dictionary containing key value pairs of attributes and
                   their respective values of ZMQVerb message structure.
    :type kwargs: dict

    :return: ZMQVerb message.
    :rtype: zmq_transport.common.message_pb2.ZMQVerb
    """
    return _create_protobuf_msg("ZMQVerb", **kwargs)


def create_get_sync_info_request_msg(**kwargs):
    """
    Creates a zmq_transport.common.message_pb2.GetSyncInfoRequest message
    structure.

    :param kwargs: A dictionary containing key value pairs of attributes and
                   their respective values of GetSyncInfoRequest message
                   structure.
    :type kwargs: dict

    :return: GetSyncInfoRequest message.
    :rtype: zmq_transport.common.message_pb2.GetSyncInfoRequest
    """
    return _create_protobuf_msg("GetSyncInfoRequest", **kwargs)


def create_get_sync_info_response_msg(**kwargs):
    """
    Creates a zmq_transport.common.message_pb2.GetSyncInfoResponse message
    structure.

    :param kwargs: A dictionary containing key value pairs of attributes and
                   their respective values of GetSyncInfoResponse message
                   structure.
    :type kwargs: dict

    :return: GetSyncInfoResponse message.
    :rtype: zmq_transport.common.message_pb2.GetSyncInfoResponse
    """
    return _create_protobuf_msg("GetSyncInfoResponse", **kwargs)


def create_send_document_request_msg(**kwargs):
    """
    Creates a zmq_transport.common.message_pb2.SendDocumentRequest message
    structure.

    :param kwargs: A dictionary containing key value pairs of attributes and
                   their respective values of SendDocumentRequest message
                   structure.
    :type kwargs: dict

    :return: SendDocumentRequest message.
    :rtype: zmq_transport.common.message_pb2.SendDocumentRequest
    """
    return _create_protobuf_msg("SendDocumentRequest", **kwargs)


def create_send_document_response_msg(**kwargs):
    """
    Creates a zmq_transport.common.message_pb2.SendDocumentResponse message
    structure.

    :param kwargs: A dictionary containing key value pairs of attributes and
                   their respective values of SendDocumentResponse message
                   structure.
    :type kwargs: dict

    :return: SendDocumentResponse message.
    :rtype: zmq_transport.common.message_pb2.SendDocumentResponse
    """
    return _create_protobuf_msg("SendDocumentResponse", **kwargs)


def create_doc_info_msg(**kwargs):
    """
    Creates a zmq_transport.common.message_pb2.DocInfo message
    structure.

    :param kwargs: A dictionary containing key value pairs of attributes and
                   their respective values of DocInfo message
                   structure.
    :type kwargs: dict

    :return: DocInfo message.
    :rtype: zmq_transport.common.message_pb2.DocInfo
    """
    return _create_protobuf_msg("DocInfo", **kwargs)


def create_all_sent_request_msg(**kwargs):
    """
    Creates a zmq_transport.common.message_pb2.AllSentRequest message
    structure.

    :param kwargs: A dictionary containing key value pairs of attributes and
                   their respective values of AllSentRequest message
                   structure.
    :type kwargs: dict

    :return: AllSentRequest message.
    :rtype: zmq_transport.common.message_pb2.AllSentRequest
    """
    return _create_protobuf_msg("AllSentRequest", **kwargs)


def create_all_sent_response_msg(items=[], **kwargs):
    """
    Creates a zmq_transport.common.message_pb2.AllSentResponse message
    structure.

    :param items: A list of tuples of length 2.
    :type items: list
    :param kwargs: A dictionary containing key value pairs of attributes and
                   their respective values of AllSentResponse message
                   structure.
    :type kwargs: dict

    :return: AllSentResponse message.
    :rtype: zmq_transport.common.message_pb2.AllSentResponse
    """
    msg_struct = _create_protobuf_msg("AllSentResponse", **kwargs)
    for item in items:
        doc_info = msg_struct.doc_info.add()
        doc_info.doc_id = item[0]
        doc_info.doc_generation = item[1]

    return msg_struct


def create_get_document_request_msg(**kwargs):
    """
    Creates a zmq_transport.common.message_pb2.GetDocumentRequest message
    structure.

    :param kwargs: A dictionary containing key value pairs of attributes and
                   their respective values of GetDocumentRequest message
                   structure.
    :type kwargs: dict

    :return: GetDocumentRequest message.
    :rtype: zmq_transport.common.message_pb2.GetDocumentRequest
    """
    return _create_protobuf_msg("GetDocumentRequest", **kwargs)


def create_get_document_response_msg(**kwargs):
    """
    Creates a zmq_transport.common.message_pb2.GetDocumentResponse message
    structure.

    :param kwargs: A dictionary containing key value pairs of attributes and
                   their respective values of GetDocumentResponse message
                   structure.
    :type kwargs: dict

    :return: GetDocumentResponse message.
    :rtype: zmq_transport.common.message_pb2.GetDocumentResponse
    """
    return _create_protobuf_msg("GetDocumentResponse", **kwargs)


def create_put_sync_info_request_msg(**kwargs):
    """
    Creates a zmq_transport.common.message_pb2.PutSyncInfoRequest message
    structure.

    :param kwargs: A dictionary containing key value pairs of attributes and
                   their respective values of PutSyncInfoRequest message
                   structure.
    :type kwargs: dict

    :return: PutSyncInfoRequest message.
    :rtype: zmq_transport.common.message_pb2.PutSyncInfoRequest
    """
    return _create_protobuf_msg("PutSyncInfoRequest", **kwargs)


def create_put_sync_info_response_msg(**kwargs):
    """
    Creates a zmq_transport.common.message_pb2.PutSyncInfoResponse message
    structure.

    :param kwargs: A dictionary containing key value pairs of attributes and
                   their respective values of PutSyncInfoResponse message
                   structure.
    :type kwargs: dict

    :return: PutSyncInfoResponse message.
    :rtype: zmq_transport.common.message_pb2.PutSyncInfoResponse
    """
    return _create_protobuf_msg("PutSyncInfoResponse", **kwargs)


def serialize_msg(msg_struct):
    """
    Serializes a protobuf message.

    :param msg_struct: A message structure defined in message.proto
    :type msg_struct: A protobuf message instance.

    :return: A serialized string created out of msg_struct.
    :rtype: str
    """
    return msg_struct.SerializeToString()


def deserialize_msg(msg_struct, msg):
    """
    Parses a msg string and fills it into an instance of msg_struct.

    :param msg_struct: Type of message structure
    :type msg_struct: str
    :param msg: Message to be parsed.
    :type msg: str

    :return: An instance of a message structure defined in message_pb2 module.
    :rtype: zmq_transport.common.message_pb2
    """
    msg_struct = getattr(proto, msg_struct)()
    msg_struct.ParseFromString(msg)
    return msg_struct


def parse_response(response, attribute):
    """
    Parses the response.

    :param response: Response string for parsing.
    :type response: str
    :param attribute: Attribute of message structure.
    :type attribute: str

    :return: A protobuf message structure.
    :rtype: zmq_transport.common.message_pb2
    """
    try:
        iden_struct = deserialize_msg("Identifier", response)
    except DecodeError, e:
        print "Expected response of type Identifier.", e
    else:
        return getattr(iden_struct, attribute)

######################### End of Protobuf utilities. #########################

########################## Start of U1DB utilities. ##########################

def get_sync_id():
    """
    Helper function to generate a unique sync_id.

    :return: A unique id generated from uuid.uuid4
    :rtype: str
    """
    return str(uuid.uuid4())


def get_target_info():
    """
    Helper function to get the current target replica info.

    :return: Target information.
    :rtype: dict
    """
    info = {}
    info["target_replica_uid"] = str(uuid.uuid4())
    info["target_replica_generation"] = 12
    info["target_replica_trans_id"] = str(uuid.uuid4())

    return info


def get_source_info():
    """
    Helper function to get the the source replica information at the target.

    :return: Source information.
    :rtype: dict
    """
    info = {}
    info["source_last_known_generation"] = 8
    info["source_last_known_trans_id"] = str(uuid.uuid4())

    return info


def get_doc_info():
    """
    TODO: Should return information about a document. Arbit now.
    """
    doc_id = str(uuid.uuid4())
    doc_rev = 5
    doc_generation = 18
    doc_content = {"data": "Random garbled text for simulation."}
    doc_content = json.dumps(doc_content)
    return (doc_id, doc_rev, doc_generation, doc_content)


def get_source_replica_uid():
    """
    Helper funtion to return source_replica_uid.
    """
    # TODO: Implement functionality. Arbit now.
    return "S-ID"

########################### End of U1DB utilities. ###########################

