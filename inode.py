#!/usr/bin/env python3

import sys
import csv

def inodeAllocationAudit(file, numInodes, startInode):
    file.seek(0)
    allocatedInodes = [False]*numInodes
    freelistInodes = [False]*numInodes
    for line in file:
        line = line.rstrip().split(',')
        if line[0] == "INODE":
            if int(line[1]) >= 1 and int(line[1]) <= numInodes:
                allocatedInodes[int(line[1])-1] = True
        elif line[0] == "IFREE":
            if int(line[1]) >= 1 and int(line[1]) <= numInodes:
                freelistInodes[int(line[1])-1] = True
    for i in range(numInodes):
        if allocatedInodes[i] and freelistInodes[i]:
            print("ALLOCATED INODE {} ON FREELIST".format(i+1))
        if (i >= startInode) and (not allocatedInodes[i]) and (not freelistInodes[i]):
            print("UNALLOCATED INODE {} NOT ON FREELIST".format(i+1))

def directoryConsistencyAudit(file, numInodes):
    file.seek(0)
    inodeLinkNum = [None]*numInodes
    inodeCountedLinks = [0]*numInodes
    dirInfos = []
    selfPtrRefs = []
    parentPtrRefs = []
    parentsMap = [None]*numInodes
    for line in file:
        line = line.rstrip().split(',')
        if line[0] == "INODE":
            if int(line[1]) >= 1 and int(line[1]) <= numInodes:
                inodeLinkNum[int(line[1])-1] = int(line[6])
        elif line[0] == "DIRENT":
            if int(line[3]) >= 1 and int(line[3]) <= numInodes:
                inodeCountedLinks[int(line[3])-1] += 1
                dirInfos.append((line[1], line[3], line[6]))
                if parentsMap[int(line[3])-1] is None:
                    parentsMap[int(line[3])-1] = line[1]
                if line[6] == "'.'":
                    selfPtrRefs.append((line[1], line[3]))
                elif line[6] == "'..'":
                    parentPtrRefs.append((line[1], line[3]))
            else:
                print("DIRECTORY INODE {0} NAME {1} INVALID INODE {2}".format(line[1], line[6], line[3]))
    for dirInfo in dirInfos:
        if inodeLinkNum[int(dirInfo[1])-1] is None:
            print("DIRECTORY INODE {0} NAME {1} UNALLOCATED INODE {2}".format(dirInfo[0], dirInfo[2], dirInfo[1]))
    for i in range(numInodes):
        if (inodeLinkNum[i] is not None) and (not inodeLinkNum[i] == inodeCountedLinks[i]):
            print("INODE {0} HAS {1} LINKS BUT LINKCOUNT IS {2}".format(i+1, inodeCountedLinks[i], inodeLinkNum[i]))
    for dirInodes in selfPtrRefs:
        if not dirInodes[1] == dirInodes[0]:
            print("DIRECTORY INODE {0} NAME '.' LINK TO INODE {1} SHOULD BE {0}".format(dirInodes[0], dirInodes[1]))
    for dirInodes in parentPtrRefs:
        if not dirInodes[1] == parentsMap[int(dirInodes[0])-1]:
            print("DIRECTORY INODE {0} NAME '..' LINK TO INODE {1} SHOULD BE {2}".format(dirInodes[0], dirInodes[1], parentsMap[int(dirInodes[0])-1]))

def main():
    if len(sys.argv) != 2:
        sys.stderr.write("Requires exactly 1 argument\n")
        exit(1)
    try:
        infile = open(sys.argv[1])
    except IOError:
        sys.stderr.write("Error opening file system image\n")
        exit(1)

    numBlocks = 0
    numInodes = 0
    for line in infile:
        line = line.rstrip().split(',')
        if line[0] == "SUPERBLOCK":
            numBlocks = int(line[1])
            numInodes = int(line[2])
            startInode = int(line[7])-1

    #Block Consistency Audits

    #I-node Allocation Audits
    inodeAllocationAudit(infile, numInodes, startInode)
    directoryConsistencyAudit(infile, numInodes)

    #Directory Consistency Audits

    infile.close()

if __name__ == '__main__':
	main()
