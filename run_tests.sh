#!/bin/bash

# Script to run the tests.


function setup() {
    if [ -d "./database/" ]; then
        rm -rf ./database/*;
    else
        mkdir ./database;
    fi

    # Create databases.
    python create_test_db.py;
}

function teardown() {
    # Delete databases.
    python delete_test_db.py;
}

setup;
printf "Running tests...\n";
coverage run --source zmq_transport/ -m unittest discover;
teardown;

# printf "##################### STAGE 2 #####################\n"
# initiate_env
# # Run tests.
# printf "Running tests..."
# coverage run --source zmq_transport/ -m unittest -v zmq_transport.tests.client.test_zmq_client
