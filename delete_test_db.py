"""
Utility script to cleanup database after running tests.
"""
# System imports
import os
import sys

# Third party imports
import u1db

# Local imports
from zmq_transport.config.settings import DATABASE_ROOT


sys.stdout.write('Destroying test databases...\n')
os.remove(os.path.join(DATABASE_ROOT, 'source-USER-1.u1db'))
os.remove(os.path.join(DATABASE_ROOT, 'user-USER-1.u1db'))
