# ZeroMQ Imports
import zmq
from zmq.eventloop.zmqstream import ZMQStream
from zmq.eventloop.ioloop import IOLoop, PeriodicCallback

# Local Imports
from zmq_transport.config import settings
from zmq_transport.common.message import KeyValueMsg
from zmq_transport.common.zmq_base import ZMQBaseSocket

class ApplicationSocket(ZMQBaseSocket):
    """
    Base class for sockets at SOLEDAD.
    """
    def __init__(self, socket, endpoint):
        """
        :param socket: ZeroMQ socket.
        :type: zmq.context.socket instance.
        :param endpoint: Endpoint to bind or connect the socket to.
        :type endpoint: str
        """
        ZMQBaseSocket.__init__(self, socket, endpoint)

    # def run(self):
    #     """
    #     Initiates socket connections. Base class implementations must over
    #     ride
    #     this method.
    #     """
    #     pass


# TODO: zmq.DEALER socket for now. Maybe a PUSH/PULL combo later on.
# See: IRC logs: http://bit.ly/1tczZJC
# TODO: Or a ROUTER/DEALER combo. 
# See: IRC logs: http://bit.ly/1ijJxNJ
class ServerHandler(ApplicationSocket):
    """
    zmq.DEALER socket.
    Used for handling data from Application Logic to send to zmq.PUB socket
    at the server.
    """
    def __init__(self, endpoint, context):
        """
        :param endpoint: Endpoint to bind or connect the socket to.
        :type endpoint: str
        :param context: ZeroMQ Context.
        :type context: zmq.Context instance.
        """
        ApplicationSocket.__init__(self, context.socket(zmq.DEALER), endpoint)
        
    def run(self):
        """
        Overrides ApplicationSocket.run() method.
        """
        self._socket.connect(self._endpoint)


class Application(object):
    """
    Application instance. Uses a ServerHandler instance.
    """
    def __init__(self, endpoint):
        """
        Initialize instance of type Application.

        :param endpoint: Endpoint of Server.
        :type endpoint: str
        """
        self._context = zmq.Context()
        self._loop = None
        self.server_handler = ServerHandler(endpoint, self._context)
        self.dataset = []

    def _prepare_reactor(self):
        """
        Prepares the reactor by wrapping sockets over ZMQStream and registering
        handlers.
        """
        self._loop = IOLoop.instance()
        self.server_handler.wrap_zmqstream()
        self.server_handler.register_handler("on_send", self.handle_snd_update)
        self.server_handler.register_handler("on_recv", self.handle_rcv_update)
        self.check_updates_callback = PeriodicCallback(self.check_updates, 1000)

    def start(self):
        """
        Method to start the application.
        """
        self._prepare_reactor()
        self.server_handler.run()
        self.server_handler._socket.send("PING-APP")
        self.check_updates_callback.start()
        # Random data for test.
        self.dataset = ["DATA - %d" % (i) for i in range(1, 10)]
        try:
            self._loop.start()
        except KeyboardInterrupt:
            print "<APPLICATION> Interrupted."

    ########################## Start of callbacks. ############################

    def handle_snd_update(self, msg, status):
        """
        Callback function to make any application level changes after Update/Request has been
        sent via DEALER socket to Server.

        :param msg: Raw/Serialized message that was sent.
        :type msg: list
        :param status: return result of socket.send_multipart(msg)
        :type status: MessageTracker or None ; See: http://zeromq.github.io/pyzmq/api/generated/zmq.eventloop.zmqstream.html#zmq.eventloop.zmqstream.ZMQStream.on_send
        """
        print "<APPLICATION> Sent: ", msg[0]

    def handle_rcv_update(self, msg):
        """
        Callback to handle incoming updates on DEALER sockets.

        :param msg: Raw Message received.
        :type: list
        """
        print "<APPLICATION> Received: ", msg[0]
        self.dataset.append(msg[0])

    def check_updates(self):
        """
        Method to regularly check new updates in self.dataset
        """
        if self.dataset:
            for data in self.dataset:
                print data
                self.server_handler._socket.send_multipart([data])
                self.dataset.remove(data)

    ########################### End of callbacks. #############################

    def stop(self):
        """
        :param socket: ZeroMQ socket.
        :type: zmq.context.socket instance.
        :param endpoint: Endpoint to bind or connect the socket to.
        :type endpoint: str
        """
        # TODO: First complete any pending tasks in self.dataset and
        # send "TERM" signal to connected components.
        self._loop.stop()
        self.server_handler.close()
        self._context.destroy()
        self.server_handler = None
        self._context = None
        self.dataset = []

def simulator(socket, n):
    """Simulates updates to Publisher. For testing purposes."""
    from random import randint
    key = b"TEST"

    for i in xrange(n):
        request_string = b"Random Update from SOLEDAD side DEALER %d." % (randint(1, 100))
        socket.send(request_string)
        # socket.send_multipart([key, request_string])
        
    print "Updates Sent."

