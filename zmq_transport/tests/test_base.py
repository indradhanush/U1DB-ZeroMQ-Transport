# System Imports
import unittest
import mock

# ZeroMQ Imports
import zmq
from zmq.eventloop.zmqstream import ZMQStream
from zmq.eventloop.ioloop import IOLoop

# Local Imports
from zmq_transport.common.zmq_base import (
    ZMQBaseSocket,
    ZMQBaseComponent
)


class ZMQBaseSocketTest(unittest.TestCase):
    """
    Test class for zmq_transport.common.zmq_base.ZMQBaseSocket
    """
    def __init__(self, *args, **kwargs):
        unittest.TestCase.__init__(self, *args, **kwargs)
        self.endpoint = "tcp://127.0.0.1:6789"

    def test_zmqBaseSocket_run(self):
        """
        Tests ZMQBaseSocket.run
        """
        # Mocking zmq
        context = mock.Mock(spec_set=zmq.Context)
        socket = mock.Mock(spec_set=zmq.ROUTER)
        server_sock = ZMQBaseSocket(context.socket(socket), self.endpoint)
        server_sock.run()

    def tearDown(self):
        pass


