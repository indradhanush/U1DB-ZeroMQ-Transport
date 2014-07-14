"""
ZMQ Synchronizer. This is the module that drives the sync at the client.
"""
# System imports
from threading import Lock

# Dependencies' imports
from u1db.errors import (
    DatabaseDoesNotExist,
    InvalidReplicaUID
)
from leap.soledad.client.sync import SoledadSynchronizer as Synchronizer


class ZMQSynchronizer(Synchronizer):
    """
    Extends leap.soledad.client.sync.SoledadSynchronizer
    """
    syncing_lock = Lock()

    def _sync(self, autocreate=False, defer_decryption=True):
        """
        Overrides SoledadSynchronizer._sync
        """
        sync_target = self.sync_target
        ensure_callback = None
        source_replica_uid = self.source._replica_uid

        # get_sync_info
        try:
            (self.target_replica_uid, target_latest_generation,
             target_latest_trans_id, source_last_known_generation,
             source_last_known_trans_id) =\
                 sync_target.get_sync_info(source_replica_uid)
            print source_last_known_trans_id
        except DatabaseDoesNotExist:
            if not autocreate:
                raise
            else:
                # Never synced yet.
                self.target_replica_uid = None
                (target_latest_generation,
                 target_latest_trans_id) = (0, "")
                (source_last_known_generation,
                 source_last_known_trans_id) = (0, "")

        if self.target_replica_uid is None:
            def ensure_callback(replica_uid):
                self.target_replica_uid = replica_uid

        if self.target_replica_uid == source_replica_uid:
            raise InvalidReplicaUID

        self.source.validate_gen_and_trans_id(source_last_known_generation,
                                              source_last_known_trans_id)

        (sync_target.source_current_gen, sync_target.source_current_trans_id,
         changes) = self.source.whats_changed(source_last_known_generation)

        if self.target_replica_uid is None:
            target_latest_generation, target_latest_trans_id = (0, "")
        else:
            target_last_known_generation, target_last_known_trans_id =\
                self.source._get_replica_gen_and_trans_id(
                    self.target_replica_uid)


        if not changes and\
           target_last_known_generation == target_latest_generation:
            if target_last_known_trans_id != target_latest_trans_id:
                raise InvalidTransactionID
            return sync_target.source_current_gen

        changed_doc_ids = [doc_id for doc_id, _, _ in changes]
        docs_to_send = self.source.get_docs(changed_doc_ids,
                                            check_for_conflicts=False,
                                            include_deleted=True)
        docs_by_generation = []
        i = 0
        for doc in docs_to_send:
            _, gen, trans_id = changes[i]
            docs_by_generation.append((doc, gen, trans_id))
            i += 1

        # sync_exchange
        try:
            new_gen, new_trans_id = sync_target.sync_exchange(
                docs_by_generation, source_replica_uid,
                target_last_known_generation, target_last_known_trans_id,
                self._insert_doc_from_target, ensure_callback=ensure_callback)

            # TODO: Override complete_sync to change the param being
            # passed from "my_gen" to "source_current_gen" ; Trivial.
            # May not be required.
            self._syncing_info = {
                TARGET_REPLICA_UID_KEY: self.target_replica_uid,
                "new_gen": new_gen,
                "new_trans_id": new_trans_id,
                "my_gen": source_current_gen
            }

            # TODO: Implement defer_decryption in ZMQSyncTarget
            # if defer_decryption and not sync_target.has_syncdb():
            #     defer_decryption = False
            self.complete_sync()
        except Exception as e:
            # TODO: Log this.
            print e
        finally:
            sync_target.stop()

        return sync_target.source_current_gen




