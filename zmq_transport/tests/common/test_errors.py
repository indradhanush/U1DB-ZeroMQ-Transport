"""
Test module for zmq_transport.common.errors
"""

# System imports
import unittest

# Local imports
from zmq_transport.common.errors import (
    ServerException,
    ConnectionIDNotSet,
    ClientException,
    UserIDNotSet,
    ApplicationException,
    SyncError
)


class BaseExceptionTest(unittest.TestCase):
    """
    Base test class for exception tests.
    """
    pass


class TestServerException(BaseExceptionTest):
    """
    Test suite for zmq_transport.common.errors.ServerException
    """
    def setUp(self):
        self.exception = ServerException("Test Message")

    def test___init__(self):
        """
        Tests ServerException.__init__()
        """
        self.assertEqual(self.exception.msg, "Test Message")

    def test___str__(self):
        """
        Tests ServerException.__str__()
        """
        self.assertEqual(self.exception.__str__(), "Test Message")


class TestConnectionIDNotSet(BaseExceptionTest):
    """
    Test suite for zmq_transport.common.errors.ConnectionIDNotSet
    """
    def setUp(self):
        self.exception = ConnectionIDNotSet("Test Message")

    def test___init__(self):
        """
        Tests ConnectionIDNotSet.__init__()
        """
        self.assertEqual(self.exception.msg, "Test Message")

    def test___str__(self):
        """
        Tests ConnectionIDNotSet.__str__()
        """
        self.assertEqual(self.exception.__str__(), "Test Message")


class TestClientException(BaseExceptionTest):
    """
    Test suite for zmq_transport.common.errors.ClientException
    """
    def setUp(self):
        self.exception = ClientException("Test Message")

    def test___init__(self):
        """
        Tests ClientException.__init__()
        """
        self.assertEqual(self.exception.msg, "Test Message")

    def test___str__(self):
        """
        Tests ClientException.__str__()
        """
        self.assertEqual(self.exception.__str__(), "Test Message")


class TestUserIDNotSet(BaseExceptionTest):
    """
    Test suite for zmq_transport.common.errors.UserIDNotSet
    """
    def setUp(self):
        self.exception = UserIDNotSet("Test Message")

    def test___init__(self):
        """
        Tests UserIDNotSet.__init__()
        """
        self.assertEqual(self.exception.msg, "Test Message")

    def test___str__(self):
        """
        Tests UserIDNotSet.__str__()
        """
        self.assertEqual(self.exception.__str__(), "Test Message")


class TestApplicationException(BaseExceptionTest):
    """
    Test suite for zmq_transport.common.errors.ApplicationException
    """
    def setUp(self):
        self.exception = ApplicationException("Test Message")

    def test___init__(self):
        """
        Tests ApplicationException.__init__()
        """
        self.assertEqual(self.exception.msg, "Test Message")

    def test___str__(self):
        """
        Tests ApplicationException.__str__()
        """
        self.assertEqual(self.exception.__str__(), "Test Message")


class TestSyncError(BaseExceptionTest):
    """
    Test suite for zmq_transport.common.errors.SyncError
    """
    def setUp(self):
        self.exception = SyncError("Test Message")

    def test___init__(self):
        """
        Tests SyncError.__init__()
        """
        self.assertEqual(self.exception.msg, "Test Message")

    def test___str__(self):
        """
        Tests SyncError.__str__()
        """
        self.assertEqual(self.exception.__str__(), "Test Message")
