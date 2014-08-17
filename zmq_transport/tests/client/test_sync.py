"""
Test module for zmq_transport.client.sync
"""

# System imports
import os
import unittest

# Dependencies' imports
from mock import (
    patch,
    MagicMock,
    Mock
)
import u1db
from u1db.errors import DatabaseDoesNotExist

# Local imports
from zmq_transport.client.sync import ZMQSynchronizer
from zmq_transport.u1db.zmq_target import ZMQSyncTarget
from zmq_transport.config.settings import (
    ENDPOINT_CLIENT_HANDLER,
    ENDPOINT_PUBLISHER,
    DATABASE_ROOT
)
from zmq_transport.common.utils import get_sync_id

class BaseSynchronizerTest(unittest.TestCase):
    """
    Base class for tests for zmq_transport.client.sync
    """
    pass


class ZMQSynchronizerTest(BaseSynchronizerTest):
    """
    Test suite for zmq_transport.client.sync.ZMQSynchronizer
    """
    def setUp(self):
        self.sync_target = ZMQSyncTarget([ENDPOINT_CLIENT_HANDLER,
                                          ENDPOINT_PUBLISHER])
        self.source = u1db.open(os.path.join(
            DATABASE_ROOT, "source-USER-1.u1db"), create=False)

        # self.patcher = patch("zmq_transport.client.sync.ZMQSynchronizer", spec=True)
        # self.patcher.start()

    def test__sync(self):
        """
        Tests ZMQSynchronizer._sync
        """
        # synchronizer = ZMQSynchronizer(self.source, self.sync_client)

        synchronizer = ZMQSynchronizer(self.source, self.sync_target)

        synchronizer._sync_step_get_sync_info = MagicMock(
            name="_sync_step_get_sync_info")
        synchronizer._sync_step_get_sync_info.return_value = (0, "", None)
        synchronizer._sync_step_validate_info_at_target = MagicMock(
            name="_sync_step_validate_info_at_target")
        synchronizer._sync_step_find_changes_to_send = MagicMock(
            name="_sync_step_find_changes_to_send")
        synchronizer._sync_step_find_changes_to_send.return_value = []
        synchronizer._sync_step_sync_exchange = MagicMock(
            name="_sync_step_sync_exchange")
        synchronizer._sync_step_sync_exchange.return_value = 0
        synchronizer._sync()
        synchronizer._sync_step_get_sync_info.assert_called_once_with(False)
        synchronizer._sync_step_validate_info_at_target.assert_called_once()
        synchronizer._sync_step_find_changes_to_send.assert_called_once_with(0,
                                                                             "")
        synchronizer._sync_step_sync_exchange.assert_called_once_with([], None)

    def test__sync_step_get_sync_info(self):
        """
        Tests ZMQSynchronizer._sync_step_get_sync_info
        """
        pass
        # with patch("zmq_transport.u1db.zmq_target.ZMQSyncTarget") as mock_target:
        #     sync_target = mock_target.return_value
        #     sync_target = ZMQSyncTarget([ENDPOINT_CLIENT_HANDLER,
        #                                  ENDPOINT_PUBLISHER])

        #     synchronizer = ZMQSynchronizer(self.source, sync_target)
        #     synchronizer.source_replica_uid = synchronizer.source._replica_uid
        #     synchronizer.sync_id = get_sync_id()
        #     synchronizer._sync_step_get_sync_info(False)


        # synchronizer._sync_step_get_sync_info = Mock(
        #     side_effect=DatabaseDoesNotExist)
        # synchronizer._sync_step_get_sync_info(False)

    def tearDown(self):
        self.sync_target = None
        self.source.close()
        # self.patcher.stop()
