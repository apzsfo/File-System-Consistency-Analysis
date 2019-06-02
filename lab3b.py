#!/usr/bin/python
import sys
import csv







def main():
    if len(sys.argv) != 2:
        sys.stderr.write("Requires exactly 1 argument\n")
        exit(1)
    try:
        infile = open(sys.argv[1])
    except IOError:
        sys.stderr.write("Error opening file system image\n")
        exit(1)


    infile.close()
    exit(0)




if __name__ == '__main__':
	main()
