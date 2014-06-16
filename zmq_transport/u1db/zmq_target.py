"""
SyncTarget API implementation to a remote ZMQ server.
"""

# Local Imports
from zmq_transport.client.zmq_client import ZMQClientBase
from zmq_transport.common import message_pb2 as proto
from zmq_transport.common.utils import serialize_msg, deserialize_msg


class ZMQSyncTarget(ZMQClientBase, SyncTarget):
    """
    Implements the SyncTarget API to a remote ZMQ server.
    """
    # def __init__(self, endpoints):
    #     """
    #     Initializes ZMQSyncTarget instance.
        
    #     :param endpoints: list of endpoints. endpoints[0] is endpoint_client_handler and
    #                       endpoints[1] is endpoint_publisher
    #     :type endpoints: list
    #     """
    #     if isinstance(endpoints, list):
    #         assert (len(endpoints) == 2), "Length of endpoints must be 2."
    #         ZMQClientBase.__init__(self, endpoints[0], endpoint[1])
    #         self.endpoints = endpoints
    #     else:
    #         raise TypeError("Expected type(endpoints) list. Got %s" % (type(endpoints)))
        
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
        Returns the sync state.
        """
        str_source_replica_uid = serialize_msg("SourceRequest",
                                        source_replica_uid=source_replica_uid)
        str_sync_type = serialized_msg("SyncType", sync_type="sync-from")
        str_zmq_verb = serialize_msg("ZMQVerb", verb=proto.ZMQVerb.GET)
        self.speaker.send([str_zmq_verb, str_sync_type, str_source_replica_uid])

        # TODO: Find a way to return the response of the above request.
        # return async_response





