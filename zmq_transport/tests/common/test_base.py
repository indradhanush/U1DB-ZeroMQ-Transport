"""
Test module for zmq_transport.common.zmq_base
"""

# System Imports
import unittest

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
    def setUp(self):
        self.endpoint = "tcp://127.0.0.1:6789"

        # Mocking zmq
        self.context = zmq.Context()
        self.server_sock = ZMQBaseSocket(self.context.socket(zmq.ROUTER),
                                         self.endpoint)

    def init_client(self):
        """
        Initializes a dummy client for testing send and receive
        operations.

        :return: A DEALER socket encapsulated in a ZMQBaseSocket
                 instance.
        :rtype: zmq_transport.common.ZMQBaseSocket
        """
        test_client = ZMQBaseSocket(self.context.socket(zmq.DEALER),
                                    self.endpoint)
        test_client._socket.connect(test_client._endpoint)

        return test_client

    def test_run(self):
        """
        Tests ZMQBaseSocket.run
        """
        with self.assertRaises(NotImplementedError):
            self.server_sock.run()

    def test_wrap_zmqstream(self):
        """
        Tests ZMQBaseSocket.wrap_zmqstream
        """
        self.server_sock.wrap_zmqstream()
        self.assertIsInstance(self.server_sock._socket, ZMQStream)

    def test_register_handler(self):
        """
        Tests ZMQBaseSocket.register_handler
        """
        pass

    def test_send(self):
        """
        Tests ZMQBaseSocket.send
        """
        test_client = self.init_client()
        test_client._socket.setsockopt(zmq.LINGER, 0)
        test_msg = ["Hello", "World"]
        try:
            ret = test_client.send(test_msg)
        except:
            self.fail("ZMQBaseSocket.send is failing.")
        finally:
            test_client.close()

    # TODO: Find a way to do this.
    # def test_recv(self):
    #     test_client = self.init_client()
    #     test_msg = ["Hello", "World"]
    #     test_client.send(test_msg)

    #     poller = zmq.Poller()
    #     poller.register(self.server_sock._socket, zmq.POLLIN)
    #     self.server_sock._socket.setsockopt(zmq.LINGER, 0)
    #     while True:
    #         socks = dict(poller.poll())

    #         if socks.get(self.server_sock._socket) == zmq.POLLIN:
    #             msg = self.server_sock.recv()
    #             self.assertEqual(test_msg, msg)
    #             return

    def test_close(self):
        self.server_sock.close()
        self.assertEqual(self.server_sock._socket.closed, True)

    def tearDown(self):
        self.server_sock.close()
        self.context.term()


class ZMQBaseComponentTest(unittest.TestCase):
    """
    Test class for zmq_transport.common.zmq_base.ZMQBaseComponent
    """
    def setUp(self):
        self.component = ZMQBaseComponent()

    def test__prepare_reactor(self):
        """
        Tests ZMQBaseComponent._prepare_reactor
        """
        with self.assertRaises(NotImplementedError):
            self.component._prepare_reactor()

    def test_start(self):
        """
        Tests ZMQBaseComponent.start
        """
        with self.assertRaises(NotImplementedError):
            self.component.start()

    def test_stop(self):
        """
        Tests ZMQBaseComponent.stop
        """
        with self.assertRaises(NotImplementedError):
            self.component.stop()
