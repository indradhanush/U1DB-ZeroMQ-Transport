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


# TODO: Make KeyValueMsg as base class for SourceRequest and
# TargetResponse classes. Ignored for now because of lack of structure
# in KeyValueMsg class.
class SourceRequest(object):
    """
    Message structure for messages originating at source.
    """
    def __init__(self, source_replica_uid, source_replica_generation,
                 source_replica_trans_id, target_replica_last_known_generation,
                 target_replica_last_known_trans_id, doc_id, doc_rev,
                 doc_content):
        """
        Initialize a SourceRequest object.

        :param source_replica_uid:
        :type source_replica_uid:
        :param source_replica_generation:
        :type source_replica_generation:
        :param source_replica_trans_id:
        :type source_replica_trans_id:
        :param target_replica_last_known_generation:
        :type target_replica_last_known_generation:
        :param target_replica_last_known_trans_id:
        :type target_replica_last_known_trans_id:
        :param doc_id:
        :type doc_id:
        :param doc_rev:
        :type doc_rev:
        :param doc_content: Body of the document
        :type doc_content: str
        """
        self.source_replica_uid = source_replica_uid
        self.source_replica_generation = source_replica_generation
        self.source_replica_trans_id = source_replica_trans_id
        self.target_replica_last_known_generation = target_replica_last_known_generation
        self.target_replica_last_known_trans_id = target_replica_last_known_trans_id
        self.doc_id = doc_id
        self.doc_rev = doc_rev
        self.doc_content = doc_content


class TargetResponse(object):
    """
    Message structure for responses from Target.
    """
    def __init__(self, target_replica_uid, target_replica_generation,
                 target_replica_trans_id):
        """
        Initialize a TargetResponse object.

        :param target_replica_uid:
        :type target_replica_uid:
        :param target_replica_generation:
        :type target_replica_generation:
        :param target_replica_trans_id:
        :type target_replica_trans_id:
        """
        self.target_replica_uid = target_replica_uid
        self.target_replica_generation = target_replica_generation
        self.target_replica_trans_id = target_replica_trans_id

