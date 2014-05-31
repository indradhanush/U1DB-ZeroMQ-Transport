# System Imports
import sys
import os
import unittest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

# Local Imports
from server import Server, ClientHandler, ApplicationHandler, Publisher
from client import Client, Speaker, Subscriber
from application import Application, ServerHandler
from settings import *

class ZMQTest(unittest.TestCase):
    pass


class ServerTest(ZMQTest):

    def setUp(self):
        self.server = Server(ENDPOINT_APPLICATION_HANDLER,
                             ENDPOINT_CLIENT_HANDLER,
                             ENDPOINT_PUBLISHER)
        self.application = Application(ENDPOINT_APPLICATION_HANDLER)
        self.client = Client(ENDPOINT_CLIENT_HANDLER,
                             ENDPOINT_PUBLISHER)


    def test_server_init(self):
        self.assertEqual(type(self.server), Server,
                         "Instance is not of type Server.")
        self.assertEqual(type(self.server.frontend), ClientHandler,
                         "Instance is not of type ClientHandler.")
        self.assertEqual(type(self.server.backend), ApplicationHandler,
                         "Instance is not of type ApplicationHandler.")
        self.assertEqual(type(self.server.publisher), Publisher,
                         "Instance is not of type Publisher.")

    def test_application_init(self):
        self.assertEqual(type(self.application), Application,
                         "Instance is not of type Application.")

    def test_client_init(self):
        self.assertEqual(type(self.client), Client,
                         "Instance is not of type Client.")
        self.assertEqual(type(self.client.speaker), Speaker,
                         "Instance is not of type Speaker.")
        self.assertEqual(type(self.client.updates), Subscriber,
                         "Instance is not of type Subscriber.")

    def test_server_frontend(self):
        pass


if __name__ == "__main__":
    unittest.main()

