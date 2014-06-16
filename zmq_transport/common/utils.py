"""
Common Utilities.
"""

# Local Imports
from zmq_transport.common import message_pb2 as proto


def serialize_msg(protobuf_type, **kwargs):
    """
    Creates a protobuf message structure defined in module
    zmq_transport.commmon.messsage_pb2, from paramaters supplied in kwargs.

    :param protobuf_type: Type of message structure.
    :type protobuf_type: str
    :param kwargs: A dictionary containing key value pairs of attributes and
    their respective values of SubscribeRequest message structure.
    :param kwargs: dict

    :returns: A serialized string created out of protobuf_type message structure.
    :type: str
    """
    msg_struct = getattr(proto, protobuf_type)()
    for key, value in kwargs.items():
        setattr(msg_struct, key, value)

    return msg_struct.SerializeToString()


def deserialize_msg(protobuf_type, msg):
    """
    Creates an instance of protobuf_type from the given message.

    :param protobuf_type: Type of message structure
    :type protobuf_type: str
    :param msg: Message to be parsed.
    :type msg: str

    :returns: An instance of a message structure defined in
    zmq_transport.common.message_pb2 module.
    :type: Intance of one of zmq_transport.common.message_pb2
    """
    msg_struct = getattr(proto, protobuf_type)()
    msg_struct.ParseFromString(msg)
    return msg_struct

