import os
import pathlib
import codecs
import sys
from sys import argv


def create_doclist(outfile, directories):
    with open(outfile, "w") as f:
        for dir_path in directories:
            abs_dir_path = str(pathlib.Path(dir_path).absolute().resolve())
            print("\t"+abs_dir_path)
            add_files_in_directory(f, abs_dir_path)

def add_files_in_directory(f, directory_path):
    """
    recursively searches a directory and any subdirectory it has for files and adds them to the output file
    :param f: file handler of file to write to
    :param directory_path: an absolute path of the directory to search or files, as a string
    :return: None
    """

    abs_files = os.listdir(directory_path)
    for abs_file in abs_files:
        # if it is a directory explore it to check for files, otherwise add it
        if os.path.isdir(os.path.join(directory_path, abs_file)):
            print("\t"+os.path.join(directory_path, abs_file))
            add_files_in_directory(f, os.path.join(directory_path, abs_file))
        else:
            f.write(os.path.join(directory_path, abs_file)+"\n")


if __name__ == "__main__":
    if sys.stdout.encoding != 'utf8':
        sys.stdout = codecs.getwriter('utf8')(sys.stdout.buffer, 'strict')
    if sys.stderr.encoding != 'utf8':
        sys.stderr = codecs.getwriter('utf8')(sys.stderr.buffer, 'strict')

    if len(argv) < 3 or argv[1] == "help":
        print("Use: python dir2doclist.py <outfile> [directories]")
        print("        where outfile is a .txt, and directories is a list of existing directories"
              "a list of paths to directories containing the raw files. "
              "if the outfile already exists it will be overwritten")
        print("        example: python3 ../path/to/doclist.txt ../path/to/raw-data/html1/ ../path/to/raw-data/html2/")
        sys.exit()
    print("outfile: " + argv[1])

    for dir in argv[2:]:
        abs_path = str(pathlib.Path(dir).absolute().resolve())
        if not os.path.exists(abs_path):
            print("directory "+abs_path+" does not exist. please run python3 dir2doclist.py help for instructions ")
            exit(1)

    create_doclist(argv[1], argv[2:])



