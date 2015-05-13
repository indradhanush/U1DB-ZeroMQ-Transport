#!/bin/bash

rm ./database/*.u1db
python reset_env.py
echo | ls -l ./database/
