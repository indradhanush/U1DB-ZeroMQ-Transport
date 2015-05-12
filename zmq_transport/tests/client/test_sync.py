"""
Test module for zmq_transport.client.sync
"""

# System imports
import os
import unittest

# Dependencies' imports
from mock import (
    MagicMock,
    Mock
)
import u1db
from u1db.errors import (
    DatabaseDoesNotExist,
    InvalidReplicaUID,
    InvalidGeneration,
    InvalidTransactionId
)

# Local imports
from zmq_transport.client.sync import ZMQSynchronizer
from zmq_transport.u1db.zmq_target import ZMQSyncTarget
from zmq_transport.config.settings import (
    ENDPOINT_CLIENT_HANDLER,
    ENDPOINT_PUBLISHER,
    DATABASE_ROOT
)


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
        self.synchronizer = ZMQSynchronizer(self.source, self.sync_target)

        # self.patcher = patch("zmq_transport.client.sync.ZMQSynchronizer",
        #                      spec=True)
        # self.patcher.start()

    def test__sync(self):
        """
        Tests ZMQSynchronizer._sync
        """
        synchronizer = self.synchronizer
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

    def test__sync_step_get_sync_info_raises_DatabaseDoesNotExist(self):
        """
        Tests that ZMQSynchronizer._sync_step_get_sync_info raises
        DatabaseDoesNotExist exception.
        """
        synchronizer = self.synchronizer
        synchronizer.source_replica_uid = synchronizer.source._replica_uid
        synchronizer.sync_target.get_sync_info = Mock(
            side_effect=DatabaseDoesNotExist)
        with self.assertRaises(DatabaseDoesNotExist):
            synchronizer._sync_step_get_sync_info(False)

    def test__sync_step_get_sync_info_not_raises_DatabaseDoesNotExist(self):
        """
        Tests that ZMQSynchronizer._sync_step_get_sync_info encounters
        DatabaseDoesNotExist exception but does not raise as autocreate=True
        """
        synchronizer = self.synchronizer
        synchronizer.source_replica_uid = synchronizer.source._replica_uid
        synchronizer.sync_target.get_sync_info = Mock(
            side_effect=DatabaseDoesNotExist)
        (target_latest_generation, target_latest_trans_id,
         ensure_callback) = synchronizer._sync_step_get_sync_info(True)
        self.assertEqual(target_latest_generation, 0)
        self.assertEqual(target_latest_trans_id, "")
        self.assertIsNotNone(ensure_callback)

    def test__sync_step_get_sync_info_raises_InvalidReplicaUID(self):
        """
        Tests that ZMQSynchronizer._sync_step_get_sync_info raises
        InvalidReplicaUID exception.
        """
        synchronizer = self.synchronizer
        mocked_id = Mock()
        synchronizer.source_replica_uid = mocked_id
        synchronizer.sync_target.get_sync_info = Mock(
            return_value=(mocked_id, Mock(), Mock(), Mock(), Mock()))

        with self.assertRaises(InvalidReplicaUID):
            synchronizer._sync_step_get_sync_info(False)

    def test__sync_step_validate_info_at_target_raises_InvalidGeneration(self):
        """
        Tests that ZMQSynchronizer._sync_step_validate_info_at_target
        raises InvalidGeneration exception.
        """
        self.synchronizer.validate_gen_and_trans_id = Mock(
            side_effect=InvalidGeneration)
        with self.assertRaises(InvalidGeneration):
            self.synchronizer._sync_step_validate_info_at_target()

    def test__sync_step_validate_info_at_target_raises_InvalidTransactionId(
            self):
        """
        Tests that ZMQSynchronizer._sync_step_validate_info_at_target
        raises InvalidTransactionId exception.
        """
        self.synchronizer.validate_gen_and_trans_id = Mock(
            side_effect=InvalidTransactionId)
        self.synchronizer.sync_target.source_last_known_generation = 1
        with self.assertRaises(InvalidTransactionId):
            self.synchronizer._sync_step_validate_info_at_target()

    def test__sync_step_find_changes_to_send_if_target_replica_uid_is_None(
            self):
        """
        Tests ZMQSynchronizer._sync_step_find_changes_to_send when
        target_replica_uid is None
        """
        synchronizer = self.synchronizer
        synchronizer.source.whats_changed = Mock(return_value=(
            0, "", MagicMock()))
        retval = synchronizer._sync_step_find_changes_to_send(0, "")
        self.assertIsInstance(retval, list)
        self.assertEqual(retval, [])

    def test__sync_step_find_changes_to_send_if_target_replica_uid_is_not_None(
            self):
        """
        Tests ZMQSynchronizer._sync_step_find_changes_to_send when
        target_replica_uid is not None
        """
        synchronizer = self.synchronizer
        synchronizer.target_replica_uid = Mock()
        synchronizer.source._get_replica_gen_and_trans_id = Mock(
            return_value=(0, ""))
        synchronizer.source.whats_changed = Mock(return_value=(
            0, "", MagicMock()))
        retval = synchronizer._sync_step_find_changes_to_send(0, "")
        self.assertIsInstance(retval, list)
        self.assertEqual(retval, [])


    def test__sync_step_find_changes_to_send_if_changes_is_None(self):
        """
        Tests that ZMQSynchronizer._sync_step_find_changes_to_send
        returns sync_target.source_current_gen when changes is None and
        generation and transaction_id are valid.
        """
        synchronizer = self.synchronizer
        synchronizer.target_replica_uid = Mock()
        synchronizer.source.whats_changed = Mock(return_value=(0, "", None))
        synchronizer.source._get_replica_gen_and_trans_id = Mock(
            return_value=(0, ""))
        retval = synchronizer._sync_step_find_changes_to_send(0, "")
        self.assertEqual(retval, 0)

    def test__sync_step_find_changes_to_send_raises_InvalidTransactionId(self):
        """
        Tests that ZMQSynchronizer._sync_step_find_changes_to_send raises
        InvalidTransactionId exception.
        """
        synchronizer = self.synchronizer
        synchronizer.target_replica_uid = Mock()
        synchronizer.source.whats_changed = Mock(return_value=(0, "", None))
        mocked_gen = Mock()
        mocked_trans_id = Mock()
        synchronizer.source._get_replica_gen_and_trans_id = Mock(
            return_value=(mocked_gen, mocked_trans_id))
        with self.assertRaises(InvalidTransactionId):
            synchronizer._sync_step_find_changes_to_send(mocked_gen, "")

    def test__sync_step_find_changes_to_send(self):
        """
        Tests ZMQSynchronizer._sync_step_find_changes_to_send
        """
        synchronizer = self.synchronizer
        # List of 3-tuples
        mocked_gen = Mock(name="mocked generation")
        mocked_trans_id = Mock(name="mocked transaction_id")
        mocked_changes = [(Mock(), mocked_gen, mocked_trans_id)]
        synchronizer.source.whats_changed = Mock(return_value=(0, "", mocked_changes))
        mocked_doc = Mock(name="mocked document")
        synchronizer.source.get_docs = Mock(return_value=[mocked_doc])
        retval = synchronizer._sync_step_find_changes_to_send(0, "")
        self.assertIsInstance(retval, list)
        self.assertEqual(retval, [(mocked_doc, mocked_gen, mocked_trans_id)])

    def test__sync_step_sync_exchange(self):
        """
        Tests ZMQSynchronizer._sync_step_sync_exchange
        """
        synchronizer = self.synchronizer
        synchronizer.source_replica_uid = synchronizer.source._replica_uid
        synchronizer.sync_target.sync_exchange = Mock(
            return_value=(Mock(), Mock()))
        synchronizer.complete_sync = Mock()
        mocked_gen = Mock(name="mocked source current generation")
        synchronizer.sync_target.source_current_gen = mocked_gen
        retval = synchronizer._sync_step_sync_exchange(MagicMock(), Mock())
        self.assertEqual(retval, mocked_gen)

    def tearDown(self):
        self.synchronizer = None
        self.sync_target = None
        self.source.close()
        # self.patcher.stop()
