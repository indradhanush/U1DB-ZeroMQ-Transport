GSoC Conclusion Report
======================

This document contains a brief summary of the entire project that
summarises the entire process and presents a brief outline of the
goals that were set at the start of the coding period and how much was
achieved over the summer. It also lays out the challenges that were
faced and how they were tackled, not to mention also the reason behind
the decisions taken. Apart from pointing out where does it stand, it
also lays out essential pointers for future work on this.

It also serves as a very good starting point to understand more about
the motivation behind the project, the approach and the way forward if
you are enthusiastic about contributing to it.

##About the Project##

###Goals set during application phase###

The initial goals set during the application phase were:

* To implement the ZeroMQ transport. This involved implementing the
  ZeroMQ equivalent of the following modules from the u1db reference
  implementation:
  + ```u1db.remote.http_client``` - This is the base module
    implementing the client side.
  + ```u1db.remote.http_target``` - This is the ```SyncTarget``` API
    implementation that accesses the target replica over HTTP.
  + ```u1db.remote.http_app``` - This is the module that provides an
    interface to interact with the underlying application on the
    server side.

* To implement a __Selective Sync__ protocol: This was supposed to let
  clients selectively choose documents to sync with the target
  replica.

* To implement a __Resume Sync__ protocol: This was supposed to handle
  interruptions elegantly and pick up the sync from exactly where it
  left.

* __Security__: The entire transport is supposed to be encrypted and
  CurveZMQ was supposed to be used here.


###Achievements under GSoC coding period and difficulties faced###

In retrospection, I seem to have underestimated the scope of the
entire project and I was able to only get the ZeroMQ transport
working. The good news is that I have tested the transport under
different workloads and found it to successfully complete the sync
process. At the time of writing this document, the code coverage
stands at 95%.

####Challenges faced####

The first and foremost challenge was to maintain backwards
compatibility with the reference implementation. Now the challenge
mostly lay in making this asynchronous nature of the tools of choice
backwards compatible. One such example can be given in the context of
```u1db.remote.http_target.HTTPSyncTarget.get_sync_info```. This
method's implementation is such that the method makes the call to the
server and only returns when the server returns the information
requested. Thus it was difficult to do this in an asynchronous client.

__The Hardest Decision__: Arguably, the most tough decision that we
had to take was to switch to a blocking client. Yes, I agree its not
the best solution probably, but in the absence of twisted styled
deferreds, the only solution to enforce a __lock-step__ sync was to
make the client blocking. One thing to note is that the client socket
is using the ```ZMQ_REQ_CORRELATE``` option and it is set to __1__
which forces the client to match incoming responses with the requests
it has just sent. If a response does not match up with the latest
request, then it is silently dropped.

#####Architectural Design#####

It would be wrong to go any further without discussing about the
underlying design that powers this transport. So without much ado,
here's a brief comparison of the approach that was intended to be and
the final design that emerged at the end of the coding period:

__How it started__: The initial idea was to maintain a ROUTER-DEALER
channel for clients wanting to sync up with the target replica and a
PUSH-PUB channel for the use case when the server wanted to publish
updates on a larger scale to a number of clients.

__What it turned into__: Few weeks into the coding period I was
struggling to get to a design that would suit best for U1DB sync
protocol. I had a ROUTER-DEALER + PUSH-PUB combo ready, but I was
pondering upon what might be the possible cases to which this design
might __not__ suit. At the same time I was also confused about
implementing a PUSH-PULL nature of communication.

I had divided the entire architecture into 3 tiers:

* __Client tier (Tier-3):__ Tier-3 is formed by the client. I don't
  think much needs to be said about this at this point.

* __Server tier (Tier-2):__ From the client's perspective, the Tier-2
  acts like a server. Essentially it is more like a Broker that acts
  like a relay node between the Tier-1 and Tier-3. This makes it easy
  to configure clients as they only need to know about the address of
  this Tier-2 node. Everything else is managed by this tier itself.

* __Application tier (Tier-1):__ This is the tier that holds the
  actual U1DB application and the target replica. Again, the
  application node need only know the address of the Server tier and
  forget about managing any clients.

In my view, this is a very simple approach of separating the
application logic with handling multiple clients that will go a long
way into scaling the infrastructure in the future. More discussion
about this follows in the __Future Work__ section.

This design looks very similar to the
[Majordomo Protocol](http://zguide.zeromq.org/py:all#Service-Oriented-Reliable-Queuing-Majordomo-Pattern)
as described in the [ZeroMQ docs](http://zguide.zeromq.org/).

This is when I was advised to start working on implementing the sync
protocol in the ZeroMQ way and only then I would be able to best judge
on what would be fit where. This came true almost instantly when, on
implementing the __zmq_target__ module, I had to override the default
DEALER socket in the client tier and replace it with a blocking REQ
socket. This was to maintain backwards compatibility. I have already
discussed about this in the __Challenges Faced__ section.


###Points to ponder upon###

* __The architectural design__: This Majordomo like design will be
  particularly very helpful once service oriented application nodes
  are added on Tier-1. That way we can keep the service oriented nodes
  transparent from all the clients. This handling of service based
  distribution of requests from the client will be the job of the
  Broker node that sits between the Application and the Client tiers.

* __Message Serialization__: My initial choice for serialization was
  [Capn'Proto](http://kentonv.github.io/capnproto/) as they seemed to
  be much faster than
  [Google's Protocol Buffers](https://developers.google.com/protocol-buffers/)
  but it appeared that it is still experimental and there were a lot
  of places where it might create some problems. So I chose to go with
  the trusted and reliable Protocol Buffers.

* __RPC via Protobuf messages__: Using RPC might be a better way of
  executing the individual sync-steps. But honestly I dont see any
  problems in the current implementation. I am noting this down just
  in case anything emerges out of this.


###Future Work###

In the decreasing order of preference:

* Making it easy to run unittests and also simplify the provision to run
  benchmarks against various loads.
* Simulate concurrent clients in both the benchmarking scripts: HTTP
  and ZeroMQ transport.
* Improving test coverage and replacing older tests with as much
  mocking as possible and as much as it may make sense.
* Adding encryption to the transport.
* Parallelize the client - This would mean breaking backwards
compatibility with the reference implementation. Thus it might be a
good idea to maintain two separate versions. One would be a blocking
one and the other with a parallelized client.
* Selective Sync - This might need implementing a shared queue kind of
  system that would queue only the selected tasks (documents) for the sync.
* Resume Sync - Implementing this is a little tricky as the
  application tier will have to maintain states for each client's sync
  process to pick up from where it left last.
