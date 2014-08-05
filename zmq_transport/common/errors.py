"""
Custom Errors for ZeroMQ Transport.
"""

class ServerException(Exception):
    """
    Base Server exception class.
    """
    def __init__(self, msg=None, **kwargs):
        self.msg = msg

    def __str__(self):
        return self.msg


class ConnectionIDNotSet(ServerException):
    """
    Raised when the connection_id is not set and the server attempts to
    send on that connection.
    """
    pass


class ClientException(Exception):
    """
    Base Client exception class.
    """
    def __init__(self, msg=None, **kwargs):
        self.msg = msg

    def __str__(self):
        return self.msg


class UserIDNotSet(ClientException):
    """
    Raised when the user_id is not set in the Client.
    """
    pass


class ApplicationException(Exception):
    """
    Base Application exception class.
    """
    def __init__(self, msg=None, **kwargs):
        self.msg = msg

    def __str__(self):
        return self.msg


class SyncError(ApplicationException):
    """
    Raised when an error occurs during the sync.
    """
    pass
