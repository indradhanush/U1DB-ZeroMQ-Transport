"""
Utility script to create database for running tests.
"""
# System imports
import os
import sys

# Dependencies' imports
import u1db

# Local imports
from zmq_transport.config.settings import DATABASE_ROOT


sys.stdout.write('Creating test databases...\n')
source = u1db.open(os.path.join(DATABASE_ROOT, "source-USER-1.u1db"),
                   create=True)
source.close()

target = u1db.open(os.path.join(DATABASE_ROOT, "user-USER-1.u1db"),
                   create=True)
target.close()
