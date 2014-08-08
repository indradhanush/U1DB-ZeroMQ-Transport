import os
import binascii

import u1db

from generate_random_file import BASE_FILE_PATH

BASE_DB_PATH = os.path.join(os.path.abspath(os.path.dirname(__file__)),
                            "database")


def create_and_write(dbname, file_path):
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

    import time
    start = time.time()
    create_and_write("source-USER-1.u1db", source_path)
    print time.time() - start
    start = time.time()
    create_and_write("user-USER-1.u1db",  target_path)
    print time.time() - start
