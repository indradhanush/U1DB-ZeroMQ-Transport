"""
Extends default U1DB components and adds to them as and where necessary.
"""
from u1db import sync


class SyncExchange(sync.SyncExchange):
    """
    Extends u1db.remote.sync.SyncExchange
    """
    def get_docs(self, changed_doc_ids, check_for_conflicts=True,
                 include_deleted=False):
        """
        Helper utility to provide access to private instance
        variable self._db.
        """
        return self._db.get_docs(changed_doc_ids, check_for_conflicts,
                                 include_deleted)

    def get_generation_info(self):
        """
        Wrapper to access private method _get_generation_info of private
        attribute _db.

        :return: A tuple containing the docs by generation, the updated
                 target generation and the transaction id.
        :rtype: tuple
        """
        return self._get_generation_info()
