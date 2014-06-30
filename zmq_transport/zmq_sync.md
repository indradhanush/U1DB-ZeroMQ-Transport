ZMQ Based Sync Protocol
======================

__This Document explains in a step by step manner the entire U1DB sync
protocol based on ZeroMQ.__

## Terminologies ##

__Client Side Architecture:__

* A blocking __REQ__ socket: This was chosen to implement a lock-step
  fashioned protocol.

__Server Side Architecture:__

* A ROUTER socket: This will handle any incoming requests from clients.


__Source:__ The component initiating a sync is referred to as source.

__Target:__ The component against which the sync has been initiated is
referred to as the target.

But, for the sake of simplicity, we will consider the __Client__ as
the __Source__ and the __Server__ as the __Target__. Also, __SOLEDAD__
implementation allows sync to be initiated only from the __Client__
end. Thus this approach keeps it simple.


### The Protocol ###

1. __get\_sync\_info :__
   * Source will send a __GetSyncInfoRequest__ to request the
     information regarding last time it had synced with the Target.

   * Target will respond with a __GetSyncInfoResponse__.

2. __sync\_exchange:__ This is a two step operation in which, first
   the source sends all the documents that have changed at source
   followed by the target sending all the documents changed at target.
   I. Source will send the docs that have changed.
     + For each doc, source sends a SendDocumentRequest containing the
       doc content, generation, id etc.
     + The target replies with SendDocumentResponse containing a flag
       that it was inserted or not.

   II. Target will send the docs that have changed at target.
     + First, target will send a list of the documents that it is
       about to send. So for N docs, it will send a list of N
       elements, where each element will be a tuple containing:
       + doc_id
       + doc_generation
     + For each element in the list received, the source will send a
       GetDocumentRequest for that document.
     + The target will reply with the contents of the document, id,
       generation etc. packed in a GetDocumentResponse message.

3. __record\_sync\_exchange:__ This is the last stage of the sync.
   * Source will send a __PutSyncInfoRequest__ message to store its
     latest sync state with the target such that, next time they sync,
     the target knows the last point the source left off at.

   * The target replies with a __PutSyncInfoResponse__ to confirm that
     it recorded the information.

