#!/bin/bash

printf "Initiating environment..."
if [ -d "./database/" ]; then
    rm -rf ./database/*
else
    mkdir ./database
fi

# Initiate databases.
python create_test_db.py
printf "Done\n"

# Run tests.
printf "Running tests..."

coverage run --source zmq_transport/ -m unittest -v zmq_transport.tests.app.test_zmq_app
