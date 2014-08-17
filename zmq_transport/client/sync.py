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

# Local imports
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
        self.source_replica_uid = self.source._replica_uid

        (target_latest_generation, target_latest_trans_id,
         ensure_callback) = self._sync_step_get_sync_info(autocreate)

        self._sync_step_validate_info_at_target()
        docs_by_generation = self._sync_step_find_changes_to_send(
            target_latest_generation, target_latest_trans_id)
        source_current_gen = self._sync_step_sync_exchange(
            docs_by_generation, ensure_callback)

        return source_current_gen

    def _sync_step_get_sync_info(self, autocreate):
        """
        Method to go through the get_sync_info step of the entire sync
        process.
        """
        # get_sync_info
        # source_last_known_generation is the last generation of the
        # source that the target knows of. Similarly for
        # source_last_known_trans_id
        ensure_callback = None
        sync_target = self.sync_target
        try:
            (self.target_replica_uid, target_latest_generation,
             target_latest_trans_id,
             sync_target.source_last_known_generation,
             sync_target.source_last_known_trans_id) =\
                 sync_target.get_sync_info(self.source_replica_uid)
        except DatabaseDoesNotExist:
            if not autocreate:
                raise
            else:
                # Never synced yet.
                self.target_replica_uid = None
                (target_latest_generation,
                 target_latest_generation) = (0, "")
                (sync_target.source_last_known_generation,
                 sync_target.source_last_known_trans_id) = (0, "")

        if self.target_replica_uid is None:
            def ensure_callback(replica_uid):
                self.target_replica_uid = replica_uid

        if self.target_replica_uid == self.source_replica_uid:
            raise InvalidReplicaUID

        return target_latest_generation, target_latest_trans_id, ensure_callback

    def _sync_step_validate_info_at_target(self):
        # Validate last known info about source present at target.
        sync_target = self.sync_target
        self.source.validate_gen_and_trans_id(
            sync_target.source_last_known_generation,
            sync_target.source_last_known_trans_id)

    def _sync_step_find_changes_to_send(self, target_latest_generation,
                                        target_latest_trans_id):
        sync_target = self.sync_target
        # Find changes at source to send to target.
        (sync_target.source_current_gen,
         sync_target.source_current_trans_id,
         changes) = self.source.whats_changed(
             sync_target.source_last_known_generation)

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

        return docs_by_generation

    def _sync_step_sync_exchange(self, docs_by_generation, ensure_callback):
        # sync_exchange
        sync_target = self.sync_target
        try:
            # TODO: Returns the new target gen and trans_id but it is
            # already set as sync_target.target_last_known_generation
            # and sync_target.target_last_known_trans_id ; Discuss?
            new_gen, new_trans_id = sync_target.sync_exchange(
                docs_by_generation, self.source_replica_uid,
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
            self.complete_sync()
        except Exception as e:
            # TODO: Log this.
            print e
        finally:
            sync_target.stop()

        return sync_target.source_current_gen
