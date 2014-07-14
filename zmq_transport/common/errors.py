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


class WhatAreYouTryingToDo(ApplicationException):
    """
    Raised when improper set of arguments are passed to
    zmq_app.SyncResource.prepare_for_sync_exchange
    """
    pass