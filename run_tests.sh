#!/bin/bash


function initiate_env() {
    printf "Initiating environment..."
    if [ -d "./database/" ]; then
        rm -rf ./database/*
    else
        mkdir ./database
    fi

    # Initiate databases.
    python create_test_db.py
    printf "Done\n"
}


printf "##################### STAGE 1 #####################\n"
initiate_env
# Run tests.
printf "Running tests..."
coverage run --source zmq_transport/ -m unittest -v zmq_transport.tests.app.test_zmq_app


# printf "##################### STAGE 2 #####################\n"
# initiate_env
# # Run tests.
# printf "Running tests..."
# coverage run --source zmq_transport/ -m unittest -v zmq_transport.tests.client.test_zmq_client
