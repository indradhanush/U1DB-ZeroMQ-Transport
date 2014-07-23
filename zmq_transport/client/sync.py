"""
ZMQ Synchronizer. This is the module that drives the sync at the client.
"""
# System imports
from threading import Lock

# Dependencies' imports
from u1db.errors import (
    DatabaseDoesNotExist,
    InvalidReplicaUID,
    InvalidTransactionId
)
from leap.soledad.client.sync import SoledadSynchronizer as Synchronizer


# Local Imports
from zmq_transport.config.u1db_settings import TARGET_REPLICA_UID_KEY

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

        print "Get Sync Info..."
        # get_sync_info
        # source_last_known_generation is the last generation of the
        # source that the target knows of. Similarly for
        # source_last_known_trans_id
        try:
            (self.target_replica_uid, target_latest_generation,
             target_latest_trans_id,
             source_last_known_generation,
             source_last_known_trans_id) =\
                 sync_target.get_sync_info(source_replica_uid)
        except DatabaseDoesNotExist:
            if not autocreate:
                raise
            else:
                # Never synced yet.
                self.target_replica_uid = None
                (target_latest_generation,
                 target_latest_generation) = (0, "")
                (source_last_known_generation,
                 source_last_known_trans_id) = (0, "")

        if self.target_replica_uid is None:
            def ensure_callback(replica_uid):
                self.target_replica_uid = replica_uid

        if self.target_replica_uid == source_replica_uid:
            raise InvalidReplicaUID

        print "Validating Last Known info of source that target has..."
        # Validate last known info about source present at target.
        self.source.validate_gen_and_trans_id(source_last_known_generation,
                                              source_last_known_trans_id)

        print "Finding changes..."
        # Find changes at source to send to target.
        (sync_target.source_current_gen, sync_target.source_current_trans_id,
         changes) = self.source.whats_changed(source_last_known_generation)

        print "Finding last known information of target known by source..."
        if self.target_replica_uid is None:
            (sync_target.target_last_known_generation,
            sync_target.target_last_known_trans_id) = (0, "")
        else:
            (sync_target.target_last_known_generation,
            sync_target.target_last_known_trans_id) =\
                self.source._get_replica_gen_and_trans_id(
                    self.target_replica_uid)

        if not changes and\
           sync_target.target_last_known_generation == target_latest_generation:
            if sync_target.target_last_known_trans_id != target_latest_trans_id:
                raise InvalidTransactionId
            return sync_target.source_current_gen

        print "Preparing changes to be sent..."
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

        print "Moving into Sync Exchange..."
        # sync_exchange
        try:
            new_gen, new_trans_id = sync_target.sync_exchange(
                docs_by_generation, source_replica_uid,
                self._insert_doc_from_target, ensure_callback=ensure_callback)

            # TODO: Override complete_sync to change the param being
            # passed from "my_gen" to "source_current_gen" ; Trivial.
            # May not be required.
            self._syncing_info = {
                TARGET_REPLICA_UID_KEY: self.target_replica_uid,
                "new_gen": new_gen,
                "new_trans_id": new_trans_id,
                "my_gen": sync_target.source_current_gen
            }

            # TODO: Implement defer_decryption in ZMQSyncTarget
            # if defer_decryption and not sync_target.has_syncdb():
            #     defer_decryption = False
            print "Moving into complete sync..."
            self.complete_sync()
        except Exception as e:
            # TODO: Log this.
            print e
        finally:
            sync_target.stop()

        return sync_target.source_current_gen
