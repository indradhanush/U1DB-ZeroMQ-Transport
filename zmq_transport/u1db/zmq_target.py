"""
SyncTarget API implementation to a remote ZMQ server.
"""

# ZMQ imports
import zmq
from zmq.eventloop.ioloop import PeriodicCallback

# Local Imports
from zmq_transport.client.zmq_client import ZMQClientBase
from zmq_transport.common import message_pb2 as proto
from zmq_transport.common.utils import create_zmq_verb_msg, create_sync_type_msg,\
    create_get_sync_info_request_msg, serialize_msg, deserialize_msg, get_sync_id
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
        Returns the sync state.
        Note: Doesnt return anything now. BROKEN.
        """
        sync_id = get_sync_id()
        sync_info_struct = create_get_sync_info_request_msg(
            source_replica_uid=source_replica_uid, sync_id=sync_id)
        str_sync_info = serialize_msg(sync_info_struct)

        sync_type_struct = create_sync_type_msg(sync_type="sync-from")
        str_sync_type = serialize_msg(sync_type_struct)

        zmq_verb_struct = create_zmq_verb_msg(verb=proto.ZMQVerb.GET)
        str_zmq_verb = serialize_msg(zmq_verb_struct)
        to_send = [str_zmq_verb, str_sync_type, str_sync_info]

        self.speaker._socket.send_multipart(to_send)
        return self.speaker.recv()


    ################### Start of Application logic handlers. ##################

    def check_new_sync(self):
        """
        Method to check if new sync is required.
        """
        if self.sync_required:
            print "Check New Sync...", self.get_sync_info("S_ID")
            self.sync_required = False
        else:
            self.sync_required = True

    ################### End of Application logic handlers. ####################

