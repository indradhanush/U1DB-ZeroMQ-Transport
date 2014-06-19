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
        :type socket: zmq.Context.socket
        :param endpoint: Endpoint to bind or connect the socket to.
        :type endpoint: str
        """
        self._socket = socket
        self._endpoint = endpoint

    def run(self):
        """
        Base mehod that connects or binds a socket to self._endpoint.
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

    def send(self, msg):
        """
        Wrapper over "socket.send_multipart()".

        :param msg: Message to be sent.
        :type msg: list
        """
        # Performing type checking as it is fairly easy to just send a
        # str in param msg.
        if not isinstance(msg, list):
            raise TypeError("param msg expected of <type 'list'>. Found %s." % (type(msg)))
        self._socket.send_multipart(msg)

    def recv(self):
        """
        Wrapper over "socket.recv_multipart()".

        :returns: Received message.
        :type: list
        """
        return self._socket.recv_multipart()

    def close(self):
        """
        Wrapper to close the socket.
        """
        self._socket.close()


class ZMQBaseComponent(object):
    """
    Base class for zmq components.
    """
    def __init__(self):
        """
        Initialize a ZMQBaseComponent instance.
        """
        self._context = zmq.Context()
        self._loop = None
        self.dataset = []

    def _prepare_reactor(self):
        """
        This method is responsible for initializing a "loop", wrapping sockets
        over ZNQStream and registering callback handlers.
        """
        raise NotImplementedError(self._prepare_reactor)

    def start(self):
        """
        This method starts the component.
        """
        raise NotImplementedError(self.start)

    def stop(self):
        """
        This method stops the component and makes for a clean exit.
        """
        raise NotImplementedError(self.stop)

