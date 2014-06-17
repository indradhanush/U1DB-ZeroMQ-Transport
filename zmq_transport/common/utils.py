"""
Common Utilities.
"""

# Local Imports
from zmq_transport.common import message_pb2 as proto


def _create_protobuf_msg(protobuf_type, **kwargs):
    """
    Creates a protobuf message defined in message.proto
    :param protobuf_type: Type of message structure.
    :type protobuf_type: str
    :param kwargs: A dictionary containing key value pairs of attributes and
    their respective values of "protobuf_type" message structure.
    :param kwargs: dict

    :returns: A protobuf message struct.
    """
    msg_struct = getattr(proto, protobuf_type)()
    for key, value in kwargs.items():
        setattr(msg_struct, key, value)
    return msg_struct

def create_subscribe_request_msg(**kwargs):
    """
    Creates a zmq_transport.common.message_pb2.SubscribeRequest message structure.

    :param kwargs: A dictionary containing key value pairs of attributes and
    their respective values of SubscribeRequest message structure.
    :param kwargs: dict

    :returns: zmq_transport.common.message_pb2.SubscribeRequest instance.
    """
    return _create_protobuf_msg("SubscribeRequest", **kwargs)


def create_unsubscribe_request_msg(**kwargs):
    """
    Creates a zmq_transport.common.message_pb2.UnsubscribeRequest message structure.

    :param kwargs: A dictionary containing key value pairs of attributes and
    their respective values of UnsubscribeRequest message structure.
    :param kwargs: dict

    :returns: zmq_transport.common.message_pb2.UnsubscribeRequest instance.
    """
    return _create_protobuf_msg("UnsubscribeRequest", **kwargs)


def create_sync_type_msg(**kwargs):
    """
    Creates a zmq_transport.common.message_pb2.SyncType message structure.

    :param kwargs: A dictionary containing key value pairs of attributes and
    their respective values of SyncType message structure.
    :param kwargs: dict

    :returns: zmq_transport.common.message_pb2.SyncType instance.
    """
    return _create_protobuf_msg("SyncType", **kwargs)


def create_zmq_verb_msg(**kwargs):
    """
    Creates a zmq_transport.common.message_pb2.ZMQVerb message structure.

    :param kwargs: A dictionary containing key value pairs of attributes and
    their respective values of ZMQVerb message structure.
    :param kwargs: dict

    :returns: zmq_transport.common.message_pb2.ZMQVerb instance.
    """
    return _create_protobuf_msg("ZMQVerb", **kwargs)


def create_get_sync_info_request_msg(**kwargs):
    """
    Creates a zmq_transport.common.message_pb2.GetSyncInfoRequest message structure.

    :param kwargs: A dictionary containing key value pairs of attributes and
    their respective values of GetSyncInfoRequest message structure.
    :param kwargs: dict

    :returns: zmq_transport.common.message_pb2.GetSyncInfoRequest instance.
    """
    return _create_protobuf_msg("GetSyncInfoRequest", **kwargs)


def create_get_sync_info_response_msg(**kwargs):
    """
    Creates a zmq_transport.common.message_pb2.GetSyncInfoResponse message structure.

    :param kwargs: A dictionary containing key value pairs of attributes and
    their respective values of GetSyncInfoResponse message structure.
    :param kwargs: dict

    :returns: zmq_transport.common.message_pb2.GetSyncInfoResponse instance.
    """
    return _create_protobuf_msg("GetSyncInfoResponse", **kwargs)


def create_send_document_request_msg(**kwargs):
    """
    Creates a zmq_transport.common.message_pb2.SyncDocumentRequest message structure.

    :param kwargs: A dictionary containing key value pairs of attributes and
    their respective values of SyncDocumentRequest message structure.
    :param kwargs: dict

    :returns: zmq_transport.common.message_pb2.SyncDocumentRequest instance.
    """
    return _create_protobuf_msg("SendDocumentRequest", **kwargs)


def create_send_document_response_msg(**kwargs):
    """
    Creates a zmq_transport.common.message_pb2.SyncDocumentResponse message structure.

    :param kwargs: A dictionary containing key value pairs of attributes and
    their respective values of SyncDocumentResponse message structure.
    :param kwargs: dict

    :returns: zmq_transport.common.message_pb2.SyncDocumentResponse instance.
    """
    return _create_protobuf_msg("SendDocumentResponse", **kwargs)


def create_get_document_request_msg(**kwargs):
    """
    Creates a zmq_transport.common.message_pb2.GetDocumentRequest message structure.

    :param kwargs: A dictionary containing key value pairs of attributes and
    their respective values of GetDocumentRequest message structure.
    :param kwargs: dict

    :returns: zmq_transport.common.message_pb2.GetDocumentRequest instance.
    """
    return _create_protobuf_msg("GetDocumentRequest", **kwargs)


def create_get_document_response_msg(**kwargs):
    """
    Creates a zmq_transport.common.message_pb2.GetDocumentResponse message structure.

    :param kwargs: A dictionary containing key value pairs of attributes and
    their respective values of GetDocumentResponse message structure.
    :param kwargs: dict

    :returns: zmq_transport.common.message_pb2.GetDocumentResponse instance.
    """
    return _create_protobuf_msg("GetDocumentResponse", **kwargs)


def create_put_sync_info_request_msg(**kwargs):
    """
    Creates a zmq_transport.common.message_pb2.PutSyncInfoRequest message structure.

    :param kwargs: A dictionary containing key value pairs of attributes and
    their respective values of PutSyncInfoRequest message structure.
    :param kwargs: dict

    :returns: zmq_transport.common.message_pb2.PutSyncInfoRequest instance.
    """
    return _create_protobuf_msg("PutSyncInfoRequest", **kwargs)


def create_put_sync_info_response_msg(**kwargs):
    """
    Creates a zmq_transport.common.message_pb2.PutSyncInfoResponse message structure.

    :param kwargs: A dictionary containing key value pairs of attributes and
    their respective values of PutSyncInfoResponse message structure.
    :param kwargs: dict

    :returns: zmq_transport.common.message_pb2.PutSyncInfoResponse instance.
    """
    return _create_protobuf_msg("PutSyncInfoResponse", **kwargs)


def serialize_msg(msg_struct):
    """
    Serializes a protobuf message.

    :param msg_struct: A message structure defined in message.proto
    :type msg_struct: A protobuf message instance.

    :returns: A serialized string created out of msg_struct.
    :type: str
    """
    return msg_struct.SerializeToString()


def deserialize_msg(msg_struct, msg):
    """
    Parses a msg string and fills it into an instance of msg_struct.

    :param msg_struct: Type of message structure
    :type msg_struct: A protobuf message instance.
    :param msg: Message to be parsed.
    :type msg: str

    :returns: An instance of a message structure defined in
    zmq_transport.common.message_pb2 module.
    :type: Instance of one of zmq_transport.common.message_pb2
    """
    msg_struct.ParseFromString(msg)
    return msg_struct

