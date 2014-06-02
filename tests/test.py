# System Imports
import sys
import os
import unittest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

# ZMQ Imports
import zmq

# Local Imports
from server import Server, ClientHandler, ApplicationHandler, Publisher
from client import Client, Speaker, Subscriber
from application import Application, ServerHandler
from settings import *

class ZMQTest(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        unittest.TestCase.__init__(self, *args, **kwargs)
        self.msg = "Hello World!"


class ServerTest(ZMQTest):

    def setUp(self):
        self.server = Server(ENDPOINT_APPLICATION_HANDLER,
                             ENDPOINT_CLIENT_HANDLER,
                             ENDPOINT_PUBLISHER)

    def test_server_init(self):
        self.assertIsInstance(self.server, Server,
                              "Instance is not of type Server.")
        self.assertIsInstance(self.server.frontend, ClientHandler,
                              "Instance is not of type ClientHandler.")
        self.assertIsInstance(self.server.backend, ApplicationHandler,
                              "Instance is not of type ApplicationHandler.")
        self.assertIsInstance(self.server.publisher, Publisher,
                              "Instance is not of type Publisher.")

    def test_server_frontend_send(self):
        """
        See: http://zeromq.github.io/pyzmq/api/zmq.html#zmq.Socket.send
        """
        ret = self.server.frontend.socket.send(self.msg)
        self.assertIsNone(ret, msg="zmq.Socket.send failed on server.frontend")

    def test_server_frontend_recv(self):
        """
        http://zeromq.github.io/pyzmq/api/zmq.html#zmq.Socket.recv
        """
        pass

    def test_server_backend_send(self):
        """
        See: http://zeromq.github.io/pyzmq/api/zmq.html#zmq.Socket.send
        """
        ret = self.server.backend.socket.send(self.msg)
        self.assertIsNone(ret, msg="zmq.Socket.send failed on server.backend")

    def test_server_backend_recv(self):
        """
        http://zeromq.github.io/pyzmq/api/zmq.html#zmq.Socket.recv
        """
        pass

    def test_server_publisher_send(self):
        """
        See: http://zeromq.github.io/pyzmq/api/zmq.html#zmq.Socket.send
        """
        ret = self.server.publisher.socket.send(self.msg)
        self.assertIsNone(ret, msg="zmq.Socket.send failed on server.publisher")


class ApplicationTest(ZMQTest):

    def setUp(self):
        self.application = Application(ENDPOINT_APPLICATION_HANDLER)

    def test_application_init(self):
        self.assertIsInstance(self.application, Application,
                              "Instance is not of type Application.")


class ClientTest(ZMQTest):

    def setUp(self):
        self.client = Client(ENDPOINT_CLIENT_HANDLER,
                             ENDPOINT_PUBLISHER)
        # TODO: Replace self.server with mock.
        self.server = Server(ENDPOINT_APPLICATION_HANDLER,
                             ENDPOINT_CLIENT_HANDLER,
                             ENDPOINT_PUBLISHER)

    def test_client_init(self):
        self.assertIsInstance(self.client, Client,
                              "Instance is not of type Client.")
        self.assertIsInstance(self.client.speaker, Speaker,
                              "Instance is not of type Speaker.")
        self.assertIsInstance(self.client.updates, Subscriber,
                              "Instance is not of type Subscriber.")

    def test_client_speaker_send(self):
        self.server.frontend.run()
        speaker = self.client.speaker
        speaker.socket.connect(speaker.endpoint)
        speaker.socket.setsockopt(zmq.SNDTIMEO, 1000)
        ret = speaker.socket.send(self.msg)
        self.assertIsNone(ret, msg="zmq.Socket.send failed on client.speaker")

    def test_client_speaker_recv(self):
        pass

    def test_client_updates_recv(self):
        pass


if __name__ == "__main__":
    unittest.main()

