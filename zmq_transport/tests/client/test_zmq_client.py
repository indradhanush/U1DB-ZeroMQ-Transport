"""
Test module for zmq_transport.client.zmq_client
"""
# System imports
import unittest

# Dependencies' imports
import zmq
from zmq.eventloop.ioloop import IOLoop
from zmq.eventloop.zmqstream import ZMQStream

# Local imports
from zmq_transport.client.zmq_client import (
    Speaker,
    ZMQClientBase,
    Subscriber
)
from zmq_transport.server.zmq_server import Server
from zmq_transport.config.settings import (
    ENDPOINT_CLIENT_HANDLER,
    ENDPOINT_PUBLISHER,
    ENDPOINT_APPLICATION_HANDLER,
)

class BaseClientTest(unittest.TestCase):
    """
    Base test class for zmq_transport.client.zmq_client tests.
    """
    pass


# class ClientSocketTest(BaseClientTest):
#     """
#     Test suite for zmq_client.ClientSocket
#     """
#     def setUp(self):
#         self.endpoint = ENDPOINT_CLIENT_HANDLER
#         self.context = zmq.Context()
#         self.req = self.context.socket(zmq.REQ)


#     def test___init__(self):
#         """
#         Tests ClientSocket.__init__
#         """
#         with patch.object(ClientSocket, "__init__") as mock_init:
#             mock_init.return_value = None
#             client_socket = ClientSocket(self.req, self.endpoint)
#             mock_init.assert_called_once_with(self.req, self.endpoint)

#     def test_run(self):
#         """
#         Tests ClientSocket.run
#         """
#         # with patch("zmq_transport.client.zmq_client.ClientSocket") as mock_client:
#         #     client_socket = mock_client(self.req, self.endpoint)
#         #     client_socket.run()
#         #     client_socket.run.assert_called_once()

#         # with patch.object(ClientSocket, "run") as mock_run:
#         #     mock_run.return_value = None
#         #     client_socket = ClientSocket(self.req, self.endpoint)
#         #     client_socket.run()
#         #     mock_run.assert_called_once()

#     def tearDown(self):
#         self.req.close()
#         self.context.term()


# class SpeakerTest(BaseClientTest):
#     """
#     Test suite for zmq_transport.client.zmq_client.Speaker
#     """
#     def setUp(self):
#         self.endpoint = ENDPOINT_CLIENT_HANDLER
#         self.context = zmq.Context()

#     def test___init__(self):
#         with patch.object(Speaker, "_socket.setsockopt") as mock_setsockopt:
#             speaker = Speaker(self.endpoint, self.context)
#             self.assertEqual(mock_setsockopt.call_args_list,

#     def tearDown(self):
#         pass


class SubscriberTest(BaseClientTest):
    """
    Space holder for tests for zmq_transport.client.zmq_client. Future
    of this part is unknown.
    """
    pass


class ZMQClientBaseTest(BaseClientTest):
    """
    Test suite for zmq_transport.client.zmq_client.ZMQClientBase
    """
    def setUp(self):
        self.client = ZMQClientBase(ENDPOINT_CLIENT_HANDLER,
                             ENDPOINT_PUBLISHER)
        # TODO: Replace self.server with mock.
        self.server = Server(ENDPOINT_APPLICATION_HANDLER,
                             ENDPOINT_CLIENT_HANDLER,
                             ENDPOINT_PUBLISHER)

    def test___init__(self):
        """
        Tests ZMQClientBase.__init__
        """
        self.assertIsInstance(self.client, ZMQClientBase,
                              "Instance is not of type ZMQClientBase.")
        self.assertIsInstance(self.client.speaker, Speaker,
                              "Instance is not of type Speaker.")
        self.assertIsInstance(self.client.updates, Subscriber,
                              "Instance is not of type Subscriber.")

    def test__prepare_reactor(self):
        """
        Tests ZMQClientBase._prepare_reactor
        """
        client = self.client
        client._prepare_reactor()
        self.assertIsInstance(client._loop, IOLoop)
        self.assertIsInstance(client.speaker._socket, ZMQStream)
        self.assertIsInstance(client.updates._socket, ZMQStream)

    def test_client_speaker_send(self):
        self.server.frontend.run()
        speaker = self.client.speaker
        speaker._socket.connect(speaker._endpoint)
        speaker._socket.setsockopt(zmq.SNDTIMEO, 1000)
        ret = speaker._socket.send("Hello World")
        self.assertIsNone(ret, msg="zmq.Socket.send failed on client.speaker")

    def test_client_speaker_recv(self):
        pass

    def test_client_updates_recv(self):
        pass
