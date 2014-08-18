"""
Test module for zmq_transport.u1db.sync
"""

# System imports
import unittest

# Dependencies' imports
from mock import Mock

# Local imports
from zmq_transport.u1db.sync import SyncExchange


class TestSyncExchange(unittest.TestCase):
    """
    Test suite for zmq_transport.u1db.sync.SyncExchange
    """
    def setUp(self):
        self.sync_exchange = SyncExchange(Mock(), Mock(), Mock())

    def test_get_docs(self):
        """
        Tests SyncExchange.get_docs
        """
        self.sync_exchange._db.get_docs = Mock(return_value="Mocked response")
        retval = self.sync_exchange.get_docs(Mock())
        self.assertEqual(retval, "Mocked response")

    def test_get_generation_info(self):
        """
        Tests SyncExchange.get_generation_info
        """
        self.sync_exchange._db._get_generation_info = Mock(
            return_value="Mocked response")
        retval = self.sync_exchange.get_generation_info()
        self.assertEqual(retval, "Mocked response")

    def tearDown(self):
        self.sync_exchange = None
