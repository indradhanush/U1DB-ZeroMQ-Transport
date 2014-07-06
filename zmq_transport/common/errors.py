"""
Custom Errors for ZeroMQ Transport.
"""

class ServerException(Exception):
    """
    Base Server exception class.
    """
    pass


class ConnectionIDNotSet(ServerException):
    """
    Raised when the connection_id is not set and the server attempts to
    send on that connection.
    """
    def __init__(self, msg=None, **kwargs):
        self.msg = msg

    def __str__(self):
        return self.msg

