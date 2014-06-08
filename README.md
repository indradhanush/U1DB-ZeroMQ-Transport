Alternate Transport For U1DB Sync Protocol
==========================================

This is my GSOC - 14 project with LEAP Encryption Access Project.

More details about it can be found in my [proposal](http://www.google-melange.com/gsoc/proposal/public/google/gsoc2014/indradhanush/5668600916475904).

Changes to the project outline made after the proposal are being maintained [here](https://docs.google.com/document/d/1XE_LwxGACQNNMU1f7dwvkbaOojd4kFGWoBaJb69X7-A/edit?usp=sharing).

##Development##

    git clone git@github.com:indradhanush/U1DB-ZeroMQ-Transport.git
    cd U1DB-ZeroMQ-Transport
    virtualenv venv
    source venv/bin/activate
    pip install -r requirements.txt

Note: Current development branch is zmq_architecture.

##Running the tests##

    git checkout zmq_architecture
    python -m unittest -v test

