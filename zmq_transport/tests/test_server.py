# System Imports
import unittest
import mock
from mock import patch

# ZeroMQ Imports
import zmq
from zmq.eventloop.ioloop import IOLoop

# Local Imports
import zmq_transport
from zmq_transport.server.zmq_server import (
    ServerSocket,
    ApplicationHandler,
    ClientHandler,
    Publisher,
    Server
)
from zmq_transport.config.settings import (
    ENDPOINT_APPLICATION_HANDLER,
    ENDPOINT_CLIENT_HANDLER,
    ENDPOINT_PUBLISHER
)


class BaseServerTest(unittest.TestCase):
    """
    Base test class for server.
    """
    def __init__(self, *args, **kwargs):
        unittest.TestCase.__init__(self, *args, **kwargs)
        self.endpoint = "tcp://127.0.0.1:6789"

    def tearDown(self):
        pass


class ServerSocketTest(BaseServerTest):
    """
    Test class for zmq_transport.server.zmq_server.ServerSocket
    """
    def test_serverSocket_run(self):
        """
        Tests ServerSocket.run
        """
        # Mocking zmq
        context = mock.Mock(spec_set=zmq.Context)
        socket = mock.Mock(spec_set=zmq.ROUTER)
        server_sock = ServerSocket(context.socket(socket), self.endpoint)
        server_sock.run()


class ApplicationHandlerTest(BaseServerTest):
    """
    Test class for zmq_transport.server.zmq_server.ApplicationHandler
    """
    def test_applicationHandler_run(self):
        """
        Tests ApplicationHandler.run
        """
        # Mocking zmq
        context = mock.Mock(spec_set=zmq.Context)
        app_sock = ApplicationHandler(self.endpoint, context)
        app_sock.run()


class ClientHandlerTest(BaseServerTest):
    """
    Test class for zmq_transport.server.zmq_server.ClientHandler
    """
    def test_clientHandler_run(self):
        """
        Tests ClientHandler.run
        """
        # Mocking zmq
        context = mock.Mock(spec_set=zmq.Context)
        client_sock = ClientHandler(self.endpoint, context)
        client_sock.run()


class PublisherTest(BaseServerTest):
    """
    Test class for zmq_transport.server.zmq_server.Publisher
    """
    def test_publisher_run(self):
        """
        Tests Publisher.run
        """
        # Mocking zmq
        context = mock.Mock(spec_set=zmq.Context)
        pub_mock = Publisher(self.endpoint, context)
        pub_mock.run()


class ServerTest(BaseServerTest):
    """
    Test class for zmq_transport.server.zmq_server.Server
    """
    def setUp(self):
        self.frontend_patcher = patch(
            "zmq_transport.server.zmq_server.ClientHandler")
        self.backend_patcher = patch(
            "zmq_transport.server.zmq_server.ApplicationHandler")
        self.publisher_patcher = patch(
            "zmq_transport.server.zmq_server.Publisher")

        self.frontend_mock = self.frontend_patcher.start()
        self.backend_mock = self.backend_patcher.start()
        self.publisher_mock = self.publisher_patcher.start()


    def check_mocks(self, server):
        # Check if classes were correctly mocked.
        assert zmq_transport.server.zmq_server.ClientHandler is\
            self.frontend_mock
        assert zmq_transport.server.zmq_server.ApplicationHandler is\
            self.backend_mock
        assert zmq_transport.server.zmq_server.Publisher is\
            self.publisher_mock

        assert server.frontend is self.frontend_mock
        assert server.backend is self.backend_mock
        assert server.publisher is self.publisher_mock


    def test_server__prepare_reactor(self):
        """
        Tests Server._prepare_reactor
        """
        server = Server(ENDPOINT_APPLICATION_HANDLER, ENDPOINT_CLIENT_HANDLER,
                        ENDPOINT_PUBLISHER)

        # Patch Server instance.
        server._context = mock.Mock(spec_set=zmq.Context)
        server._loop = mock.Mock(spec_set=IOLoop)

        server.frontend = self.frontend_mock
        server.backend = self.backend_mock
        server.publisher = self.publisher_mock

        self.check_mocks(server)

        with patch("zmq.eventloop.zmqstream.ZMQStream") as zmqstream_mock:
            server._prepare_reactor()

            # TODO: Check if zmqstream_mock is called withing wrap_zmqstream
            self.assertEqual(server.frontend.wrap_zmqstream.called, True)
            self.assertEqual(server.publisher.wrap_zmqstream.called, True)
            self.assertEqual(server.backend.wrap_zmqstream.called, True)

            expected = [(("on_send", server.handle_snd_update_client), ),
                        (("on_recv", server.handle_rcv_update_client), )]
            self.assertEqual(server.frontend.register_handler.call_args_list,
                             expected)

            expected = [(("on_send", server.handle_snd_update_client), )]
            self.assertEqual(server.publisher.register_handler.call_args_list,
                             expected)

            expected = [(("on_send", server.handle_snd_update_app), ),
                        (("on_recv", server.handle_rcv_update_app), )]
            self.assertEqual(server.backend.register_handler.call_args_list,
                             expected)

    def tearDown(self):
        self.frontend_patcher.stop()
        self.backend_patcher.stop()
        self.publisher_patcher.stop()

