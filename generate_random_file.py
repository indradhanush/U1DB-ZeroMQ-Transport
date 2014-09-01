"""
Generates Random data and writes to a file.
Takes the number of files and size of each file in MB as arguments.
Used for testing.
Author: Indradhanush Gupta
Github: https://github.com/indradhanush
Twitter: https://twitter.com/Indradhanush92
Facebook: https://www.facebook.com/Indradhanush
"""


import os
import sys


BASE_FILE_PATH = os.path.join(os.path.abspath(os.path.dirname(__file__)),
                              "dumps")

def generate_files(file_suffix, n, size):

    directory = os.path.join(BASE_FILE_PATH, file_suffix)
    if not os.path.exists(directory):
        os.makedirs(directory)

    base_file_name = "{0}_".format(file_suffix)
    file_count = 1

    for i in xrange(n):
        name = os.path.abspath("{0}/{1}{2}".format(directory,
                                                   base_file_name,
                                                   str(file_count)))
        file = open(name, "wb")
        file.write(os.urandom((1024**2)*size))
        file.close()
        file_count += 1


if __name__ == '__main__':
    if len(sys.argv) != 4:
        print "Insufficient or Too Many Arguments!"
        print "Usage : file_suffix no_of_files size_of_each_file_in_MB"
        sys.exit()

    try:
        file_suffix = sys.argv[1]
        n = int(sys.argv[2])
        size = int(sys.argv[3])
    except(ValueError, TypeError):
        print "Arguments must be of type int"
        sys.exit()

    print "Creating %d files of size %d MB each..." % (n, size)
    generate_files(file_suffix, n, size)
