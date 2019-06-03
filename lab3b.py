#!/usr/bin/env python3

#NAME: Ryan Nemiroff, Andrew Zeff
#EMAIL: ryguyn@gmail.com, apzsfo@g.ucla.edu#
#ID: 304903942, 804994987

import sys

def inodeAllocationAudit(file, numInodes, startInode): #allocating inodes
    file.seek(0) #start at beginning
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

    #Block Consistency Audits
    num_blocks = 0
    num_inodes = 0
    block_size = 0
    inode_size = 0

    direct_key = {0: "BLOCK", 1: "INDIRECT BLOCK", 2: "DOUBLE INDIRECT BLOCK", 3: "TRIPLE INDIRECT BLOCK"}
    single_block = {"bfree": 0, "referenced": 0, "direction" : [0], "offset" : [-1], "inode_nums" : []} #each block has info
    block_info = {}
    #inode_dict = {}

    for csv in infile:
        parsed = csv.split(',')
        if parsed[0] == 'SUPERBLOCK': #get sizes
            num_blocks = int(parsed[1])
            num_inodes = int(parsed[2])
            block_size = int(parsed[3])
            inode_size = int(parsed[4])
            start_inode = int(parsed[7])-1
        if parsed[0] == 'INODE': #capture blocks corresponding to particular inodes
            #inode_dict[int(parsed[1])] = []
            for num in range(12, 27):
                if int(parsed[num]) not in block_info:
                    block_info[int(parsed[num])] = {"bfree": 0, "referenced": 1, "direction" : [0], "offset" : [num - 12], "inode_num" : [int(parsed[1])]}
                    #inode_dict[int(parsed[1])].append(int(parsed[num]))
                else:
                    #inode_dict[int(parsed[1])].append(int(parsed[num]))
                    block_info[int(parsed[num])]["referenced"] += 1
                    block_info[int(parsed[num])]["inode_num"].append(int(parsed[1]))
                    block_info[int(parsed[num])]["offset"].append(num - 12)
                    block_info[int(parsed[num])]["direction"].append(0)
                length = len(block_info[int(parsed[num])]["direction"])
                if num == 24:
                    block_info[int(parsed[num])]["direction"][length-1] = 1 #handling the indirect cases
                
                if num == 25:
                    block_info[int(parsed[num])]["direction"][length-1] = 2
                    block_info[int(parsed[num])]["offset"][length-1] = 12 + 256
                if num == 26:
                    block_info[int(parsed[num])]["direction"][length -1] = 3
                    block_info[int(parsed[num])]["offset"][length -1] = 12 + 256 + 256*256


    infile.seek(0) #start at beginning of file
    for csv in infile:
        parsed = csv.split(',')
        if parsed[0] == 'GROUP': #find information for the first valid block
            first_valid = int(parsed[8]) + inode_size * num_inodes / block_size
        if parsed[0] == 'BFREE': #check free list
            if int(parsed[1]) in block_info:
                block_info[int(parsed[1])]["bfree"] = 1
            else:
                block_info[int(parsed[1])] = {"bfree": 1, "referenced": 0, "direction" : [0], "offset" : [-1], "inode_nums" : []}

    for num in block_info: #loop through all blocks
        length = len(block_info[num]["direction"])
        for i in range (0, length): #duplicate check
            allocated_conditional = 0
            reserved = 0
            invalid = 0
            if (num < 0 or num > num_blocks - 1) and block_info[num]["offset"][i] != -1:
                sys.stdout.write("INVALID " + direct_key[block_info[num]["direction"][i]] + " " + num + " IN INODE " + block_info[num]["inode_num"][i] + " AT OFFSET " + block_info[num]["offset"][i] + "\n")
                invalid = 1
            elif num > 0 and num < first_valid and block_info[num]["offset"][i] != -1:
                sys.stdout.write("RESERVED " + direct_key[block_info[num]["direction"][i]] + " " + num + " IN INODE " + block_info[num]["inode_num"][i] + " AT OFFSET " + block_info[num]["offset"][i] + "\n")
                reserved = 1
            if block_info[num]["referenced"] == 0 and block_info[num]["bfree"] == 0 and reserved == 0 and invalid == 0:
                sys.stdout.write("UNREFERENCED BLOCK " + num)
            if block_info[num]["bfree"] == 1 and block_info[num]["referenced"] > 0 and reserved == 0 and invalid == 0 and allocated_conditional == 0:
                sys.stdout.write("ALLOCATED BLOCK " + num + " ON FREELIST" + "\n")
                allocated_conditional = 1
            if block_info[num]["referenced"] > 1 and reserved == 0 and invalid == 0:
                sys.stdout.write("DUPLICATE " + direct_key[block_info[num]["direction"][i]] + " " + str(num) + "\n")

    #I-node Allocation Audits
    inodeAllocationAudit(infile, num_inodes, start_inode)
    directoryConsistencyAudit(infile, num_inodes)

    infile.close()

if __name__ == '__main__':
	main()
