class KeyValueMsg(object):
    """
    Experimental Key Value Message Store.
    Inspired from http://zguide.zeromq.org/py:kvsimple and 
    http://zguide.zeromq.org/py:kvmsg
    
    Message Format:
    Frame 0: Unique Key
    Frame 1: Value/Body
    """
    def __init__(self, key, body):
        self.key = key
        self.body = body

    @classmethod
    def parse_msg(cls, msg):
        """
        Parses a multipart message.
        """
        key, body = msg
        return cls(key, body)

