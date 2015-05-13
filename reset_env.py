# System imports
import os
import binascii
import time

# Dependencies' imports
import u1db

# Local imports
from generate_random_file import BASE_FILE_PATH

BASE_DB_PATH = os.path.join(os.path.abspath(os.path.dirname(__file__)),
                            "database")


def create_and_write(dbname, file_path):
    """
    Utility to write files to dbname from file_path.

    :param dbname: Name of the database.
    :type dbname: str

    :param file_path: Absolute path of the directory that contains the
                      files.
    :type file_path: str
    """
    # Note: When the os.urandom() data is encoded to be inserted as a
    # doc_content in u1db, its size may change depending on the encoding
    # chosen. So the code is being benchmarked against larger files than
    # what it may appear to be.
    db = u1db.open(os.path.join(BASE_DB_PATH, dbname), create=True)
    files = os.listdir(file_path)
    for f in files:
        file_ob = open(os.path.join(file_path, f), "rb")
        data = ""
        while True:
            byte = file_ob.read(45)
            if not byte:
                break
            data += binascii.b2a_uu(byte)

        file_ob.close()

        db.create_doc({
            "name": f,
            "data": data
        })

    docs = db.get_all_docs()
    db.close()


if __name__ == "__main__":
    source_path = os.path.join(BASE_FILE_PATH, "source")
    target_path = os.path.join(BASE_FILE_PATH, "target")

    # TODO: Use timeit for more accurate times.
    start = time.time()
    create_and_write("source-USER-1.u1db", source_path)
    print time.time() - start
    start = time.time()
    create_and_write("user-USER-1.u1db",  target_path)
    print time.time() - start
