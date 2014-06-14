TODO List + Pointers to Discuss before implementing
===================================================

TODO
----

* Might use mock in the future for tests.

Discuss
-------

* ~~Rename Server.run() to Server.start() and likewise in Client and
  Application classes to clear confusion from ServerSocket.run() and
  likewise from ClientSocket.run() and ApplicationSocket.run()~~

* application.ServerHandler: Currently a DEALER-ROUTER pair and uses
  __tcp__ as transport. Might be a better idea to use __ipc__
  transport instead. Seems faster than __tcp__. Need more research.

* Tier 1 - Tier 2 Communication: There might be a better alternative
  than DEALER-ROUTER. But seems to work for now.

* Force send an initial "HELLO" message from applciation.ServerHandler
  to server.Server.backend to register the connection_id on the server
  side zmq.ROUTER socket.

* ~~Rename Server.tearDown() to Server.stop() and likewise for Client and Application classes.~~

*  The callback functions, `handle_snd_update`, `handle_rcv_update`,
   etc. might be - `In the future we might want to change this description to something like "Insert incoming documents on local database replica".`

* `Speaker.run` and `Subscriber.run` might not override
  `ClientSocket.run` if there isn't anything else to do. Will remove
  if thats the case. It acts as a placeholder for now.

* Tackling multiple callbacks at once with some kind of lock - `Maybe we will want some lock here to prevent multiple updates to be checked in parallel? Not really sure about this, will depend on how we develop the syncing algorithm.`

