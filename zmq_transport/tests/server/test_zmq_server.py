"""
Test module for zmq_transport.server.zmq_server
"""

# System imports
import unittest

# Dependencies' imports
import zmq
from zmq.eventloop.ioloop import IOLoop
from zmq.eventloop.zmqstream import ZMQStream

# Local imports
from zmq_transport.server.zmq_server import (
    Server,
    ApplicationHandler,
    ClientHandler,
    Publisher
)
from zmq_transport.common.errors import (
    ConnectionIDNotSet
)
from zmq_transport.config.settings import (
    ENDPOINT_APPLICATION_HANDLER,
    ENDPOINT_CLIENT_HANDLER,
    ENDPOINT_PUBLISHER
)


class BaseServerTest(unittest.TestCase):
    """
    Base test class for zmq_transport.server.zmq_server tests.
    """
    pass


class ApplicationHandlerTest(BaseServerTest):
    """
    Test suite for zmq_transport.common.zmq_server.ApplicationHandler
    """
    def setUp(self):
        self.context = zmq.Context()
        self.app_handler = ApplicationHandler("tcp://127.0.0.1:9999",
                                              self.context)
    def test_set_connection_id(self):
        """
        Tests ApplicationHandler.set_connection_id
        """
        self.app_handler.set_connection_id("Random garbage")
        self.assertEqual(self.app_handler._connection_id, "Random garbage")
        self.app_handler.set_connection_id("New garbage", force_update=True)
        self.assertEqual(self.app_handler._connection_id, "New garbage")

    def test_get_connection_id(self):
        """
        Tests ApplicationHandler.get_connection_id
        """
        self.app_handler.set_connection_id("Random garbage")
        self.assertEqual(self.app_handler.get_connection_id(), "Random garbage")

    def test_send(self):
        """
        Tests ApplicationHandler.send
        """
        with self.assertRaises(ConnectionIDNotSet):
            self.app_handler.send("hello world!")
        self.app_handler.run()
        self.app_handler.set_connection_id("\\x0xxxyyyzzz")
        self.app_handler.send("hello world!")
        self.app_handler.send(["hello", "world"])

class ServerTest(BaseServerTest):
    """
    Test suite for zmq_transport.server.zmq_server.Server tests.
    """
    def setUp(self):
        self.server = Server(ENDPOINT_APPLICATION_HANDLER,
                             ENDPOINT_CLIENT_HANDLER,
                             ENDPOINT_PUBLISHER)

    def init_dummy_units(self):
        self.context = zmq.Context()
        self.dummy_client = self.context(zmq.DEALER)
        self.dummy_client.connect(ENDPOINT_CLIENT_HANDLER)

    def test___init__(self):
        """
        Tests Server.__init__
        """
        self.assertIsInstance(self.server, Server,
                              "Instance is not of type Server.")
        self.assertIsInstance(self.server.frontend, ClientHandler,
                              "Instance is not of type ClientHandler.")
        self.assertIsInstance(self.server.backend, ApplicationHandler,
                              "Instance is not of type ApplicationHandler.")
        self.assertIsInstance(self.server.publisher, Publisher,
                              "Instance is not of type Publisher.")

    def test__prepare_reactor(self):
        self.server._prepare_reactor()
        self.assertIsInstance(self.server._loop, IOLoop)
        self.assertIsInstance(self.server.frontend._socket, ZMQStream)
        self.assertIsInstance(self.server.publisher._socket, ZMQStream)
        self.assertIsInstance(self.server.backend._socket, ZMQStream)

    # def test_handle_rcv_update_client(self):
    #     """
    #     Tests Server.handle_rcv_update_client
    #     """
    #     self.server._prepare_reactor()

    # def test_frontend_on_send_handler(self):
    #     pass
