TODO List + Pointers to Discuss before implementing
===================================================

TODO
----

Discuss
-------

* Rename Server.run() to Server.start() and likewise in Client and Application classes to clear confusion from ServerSocket.run() and likewise from ClientSocket.run() and ApplicationSocket.run()

* application.ServerHandler: Currently a DEALER-ROUTER pair and uses __tcp__ as transport. Might be a better idea to use __ipc__ transport instead. Seems faster than __tcp__. Need more research.

* Tier 1 - Tier 2 Communication: There might be a better alternative than DEALER-ROUTER. But seems to work for now.
