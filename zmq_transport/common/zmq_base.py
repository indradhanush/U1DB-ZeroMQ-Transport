# ZeroMQ Imports
import zmq
from zmq.eventloop.zmqstream import ZMQStream


class ZMQBaseSocket(object):
    """
    Base socket class for zmq sockets.
    """
    def __init__(self, socket, endpoint):
        """
        :param socket: ZeroMQ socket.
        :type: zmq.context.socket instance.
        :param endpoint: Endpoint to bind or connect the socket to.
        :type endpoint: str
        """
        self._socket = socket
        self._endpoint = endpoint

    def run(self):
        """
        Base method that connects or binds a socket to self._endpoint.
        Sub classes must override this method.
        """
        raise NotImplementedError(self.run)

    def wrap_zmqstream(self):
        """
        Wraps self._socket into ZMQStream socket.
        """
        self._socket = ZMQStream(self._socket)

    def register_handler(self, method, callback, *args, **kwargs):
        """
        Registers a callback for a particular method.

        :param method: The method to which the callback will be attached.
        :type method: str
        :param callback: The callback method.
        :type callback: function
        """
        assert isinstance(self._socket, ZMQStream), "Not a ZMQStream socket."
        getattr(self._socket, method)(callback)

    # def send(self, msg):
    #     """
    #     Wrapper over "socket.send()".

    #     :param msg: Message to be sent.
    #     :type msg: str
    #     """
    #     raise NotImplementedError(self.send)

    # def send_multipart(self, msg):
    #     """
    #     Wrapper over "socket.send_multipart()".

    #     :param msg: Message to be sent.
    #     :type msg: str
    #     """
    #     raise NotImplementedError(self.send_multipart)

    def close(self):
        """
        Wrapper to close the socket.
        """
        self._socket.close()

