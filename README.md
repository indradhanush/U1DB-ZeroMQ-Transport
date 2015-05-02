ZeroMQ Transport For U1DB Sync Protocol
==========================================

This is my Google Summer of Code - 14 project  with
[LEAP Encryption Access Project](http://leap.se/).

You may read the original proposal [here](http://www.google-melange.com/gsoc/proposal/public/google/gsoc2014/indradhanush/5668600916475904).

##Contributing##

* Understand the U1DB sync algorithm. Read
  [this](https://pythonhosted.org/u1db/conflicts.html#synchronisation-over-http).
* Consider reading the Report.md document first. It contains useful
  information about the progress and future work right from the time
  when the idea was born.
* Check out
  [todo.md](https://github.com/indradhanush/U1DB-ZeroMQ-Transport/blob/master/todo.md)
  to find out places where you can pitch in.
* Alternatively run ```cd zmq_transport/ && ack-grep -i todo``` from
   the project root to find __TODO__ lines in the code itself. Some of
   these are trivial while some demand some brainstorming. You are
   welcome to try out.
* Join us on #leap at
  [irc.freenode.net](https://webchat.freenode.net). The relevant
  people to ask about this are __db4(drebs)__, __kaliy__, and __dhanush__. We
  are very enthusiastic about this project. See you soon! :)
* We follow git-flow for development. If you are not aware about it read
a very good article on it [here](http://nvie.com/posts/a-successful-git-branching-model/).
* Fork the repo!
* ```git clone <repo url>```
* ```cd U1DB-ZeroMQ-Transport```
* ```virtualenv venv```
* ```source venv/bin/activate```
* __NOTE:__ Before you run the next step, pip 1.5 has broken the
  install of `u1db`, which is one of the dependencies. So to install
  it, you need to run the following command first and then move on
  (Sorry for the hassle until this is fixed):
* ```pip install --allow-external u1db --allow-unverified u1db
  --allow-external dirspec --allow-unverified dirspec u1db```
* ```pip install -r requirements.txt```
* Send a PR!
* Please make sure you are also adding the relevant tests and make
  sure that they pass in order to get the PR accepted.

##Running the tests##

Run ```./run_tests.sh``` from the project root.

##Running benchmarks##

* Enter the project root.
* Create prerequesite directories (One time only. Yay!) :
  + ```mkdir dumps```
  + ```mkdir database```
* ```source venv/bin/activate```
* Generate random files. The following commands will put 5 files, each
  of size 1 MB with random binary data generated using
  ```os.urandom()```. We are putting the files on both the
  ```source``` and the ```target``` directories.
  + ```python generate_random_file.py source 5 1```
  + ```python generate_random_file.py target 5 1```
* Create ```U1DB``` environment.
  + ```./reset_env.sh```
* Run sync via http:
  + ```python reference_implementation.py```
* Reset ```U1DB``` environment.
  + ```./reset_env.sh```
* To run sync via ZeroMQ transport, first open up 3 terminals, (byobu
  might be of help here) and run the following commands in the
  following sequence in each of them:
  + ```python server_runner.py```
  + ```python application_runner.py```
  + ```python client_runner.py```

Note: I agree its a bit tedious at the moment. I plan to make this as
easy as running a single command or two at most pretty soon. In fact
that's number 1 on my todo.
