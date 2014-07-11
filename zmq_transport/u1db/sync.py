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
        self._db.get_docs(changed_doc_ids, check_for_conflicts, include_deleted)

