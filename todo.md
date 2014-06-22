TODO List + Pointers to Discuss before implementing
===================================================

todo
----

* might use mock in the future for tests.

discuss
-------

* ~~rename server.run() to server.start() and likewise in client and
  application classes to clear confusion from serversocket.run() and
  likewise from ClientSocket.run() and ApplicationSocket.run()~~

* application.ServerHandler: Currently a DEALER-ROUTER pair and uses
  __tcp__ as transport. Might be a better idea to use __ipc__
  transport instead. Seems faster than __tcp__. Need more research.

* Tier 1 - Tier 2 Communication: There might be a better alternative
  than DEALER-ROUTER. But seems to work for now.

* Force send an initial "HELLO" message from applciation.ServerHandler
  to server.Server.backend to register the connection_id on the server
  side zmq.ROUTER socket.

* ~~Rename Server.tearDown() to Server.stop() and likewise for Client
  and Application classes.~~

*  The callback functions, `handle_snd_update`, `handle_rcv_update`,
   etc. might be - `In the future we might want to change this
   description to something like "Insert incoming documents on local
   database replica".`

* `Speaker.run` and `Subscriber.run` might not override
  `ClientSocket.run` if there isn't anything else to do. Will remove
  if thats the case. It acts as a placeholder for now.

* Tackling multiple callbacks at once with some kind of lock - `Maybe
  we will want some lock here to prevent multiple updates to be
  checked in parallel? Not really sure about this, will depend on how
  we develop the syncing algorithm.`

* __IMPORTANT:__ Add authentication wrapper over `Publisher.subscribe()` and
  `Publisher.unsubscribe()` methods. Probably make this wrapper as a
  decorator for easier patching of other functions.

* __IMPORTANT:__ Find a way for
  `zmq_transport.u1db.zmq_target.ZMQSyncTarget.get_sync_info` to
  return the response after the request. Or else backwards
  compatibility is broken.

* Might rename package `zmq_transport` into `zmtp`. Concise. Sounds
  better. :)

* __Doc Chunking:__ String length in SendDocumentRequest is not
  limited or known now. Needs to be handled while implementing
  document chunking.

* __Parallelizing SendDoc and GetDoc:__ <db4>: This is cool because
  GetDocumentRequests can be parallelized, and we just enfoce
  insertion of the documents in the correct order in the client by
  using a lock or a queue. Maybe you can thing about a way to do that
  for PutDocumentRequests also, but I'm not sure how would be the best
  way to do it. Documents always have to be inserted in the correct
  order, either in source and in target, so the "other replica"
  metadata is correctly maintained. __Implement a lock enforced queue maybe.__

* __Utils module:__ Variables of dict info in get_target_info function
  need to be stored somewhere in a target_settings file.

* __Recover Sync Implentation:__ On a `DecodeError`, the code silently
  fails fow now. RecoverSync Implementation could fill this in.
  
* __Server Handler:__ Add functionality to do a db transaction in
  handle_put_sync_info_request.

* __Narrow down \__init\__.py__: Remove un-needed dependencies from
  u1db.\__init\__ module.
