#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
import difflib
import sys
import filecmp
import hashlib
from time import strftime, gmtime
try:
    import ds_store
except:
    print("Unable to import ds_store module\
    \nRun 'pip install ds_store' to install dependancy")
    sys.exit(1)

try:
    ds_file = sys.argv[2]
    action = sys.argv[4]
except:
    print("\nSyntax Error or a specified path does not exist.\
    \n\nusage: ds_store_tool.py --source SOURCE_DS_STORE_FILE --action [parse|watch]\
    \n\n  --source: The source .DS_Store file to run action against.\
    \n\n  --action: The action to perform on the source. Available options are:\
    \n      parse: Parse the .DS_Store file. Parsed data is outputted to stdout\
    \n      watch: Watch the .DS_Store file for changes and print changes to stdout. useful for research.")
    sys.exit(1)

if action.lower() != 'parse' and action.lower() != 'watch':
    print("\nInvalid action specified\
    \n\nusage: ds_store_tool.py --source SOURCE_DS_STORE_FILE --action [parse|watch]\
    \n\n  --source: The source .DS_Store file to run action against.\
    \n\n  --action: The action to perform on the source. Available options are:\
    \n      parse: Parse the .DS_Store file. Parsed data is outputted to stdout\
    \n      watch: Watch the .DS_Store file for changes and print changes to stdout. useful for research.")
    sys.exit(1)

store = ds_store.DSStore.open(ds_file, 'r')

if action.lower() == 'parse':
    print("DSStoreEntry_Filename\tDSStoreEntry_Type\tDSStoreEntry_Code\tDSStoreEntry_Value\n")
    for i in store:
        print(str(i.filename)+"\t"+str(i.type)+"\t"+str(i.code)+"\t"+str(i.value)+"\n")
        sys.exit(1)


o_file = open("original.txt",'wb')
file_1_comp = open("comp_file_1.txt",'wb')

o_file.write("DSStoreEntry_Filename\tDSStoreEntry_Type\tDSStoreEntry_Code\tDSStoreEntry_Value\n")
file_1_comp.write("DSStoreEntry_Filename\tDSStoreEntry_Type\tDSStoreEntry_Code\tDSStoreEntry_Value\n")
hasher_f_1 = hashlib.md5()

for i in store:
     o_file.write(str(i.filename)+"\t"+str(i.type)+"\t"+str(i.code)+"\t"+str(i.value)+"\n")
     file_1_comp.write(str(i.filename)+"\t"+str(i.type)+"\t"+str(i.code)+"\t"+str(i.value)+"\n")
file_1_comp.close()
o_file.close()
     
with open(ds_file, 'rb') as afile:
    buf = afile.read()
    hasher_f_1.update(buf)

answer = "y"
while answer=="y":
    hasher_f_2 = hashlib.md5()
            
    with open(ds_file, 'rb') as afile:
        buf = afile.read()
        hasher_f_2.update(buf)
    
    if hasher_f_1.hexdigest()!=hasher_f_2.hexdigest():
        file_2_comp = open("comp_file_2.txt",'wb')
        c_file = open("current.txt",'wb')
        file_2_comp.write("DSStoreEntry_Filename\tDSStoreEntry_Type\tDSStoreEntry_Code\tDSStoreEntry_Value\n")
        c_file.write("DSStoreEntry_Filename\tDSStoreEntry_Type\tDSStoreEntry_Code\tDSStoreEntry_Value\n")
        for i in store:
            file_2_comp.write(str(i.filename)+"\t"+str(i.type)+"\t"+str(i.code)+"\t"+str(i.value)+"\n")
            c_file.write(str(i.filename)+"\t"+str(i.type)+"\t"+str(i.code)+"\t"+str(i.value)+"\n")
        file_2_comp.close()
        c_file.close()
        hasher_f_1 = hashlib.md5()
        file_1_comp = open("comp_file_1.txt",'r')
        file_2_comp = open("comp_file_2.txt",'r')
        lines1 = file_1_comp.readlines()
        lines2 = file_2_comp.readlines()

        print strftime("%m/%d/%Y %H:%M:%S", gmtime()),"---------------------------------"

        '''for line in difflib.unified_diff(lines1, lines2, fromfile=file_1_comp, tofile=file_2_comp, lineterm='', n=0):
            print line'''
        diff = difflib.ndiff(lines1,lines2)
        changes = [l for l in diff if l.startswith('+ ') or l.startswith('- ') or l.startswith('! ')]
        for i in changes:
            print i
        print ''
        file_1_comp = open("comp_file_1.txt",'wb')
        file_1_comp.write("DSStoreEntry_Filename\tDSStoreEntry_Type\tDSStoreEntry_Code\tDSStoreEntry_Value\n")
        for i in store:
            file_1_comp.write(str(i.filename)+"\t"+str(i.type)+"\t"+str(i.code)+"\t"+str(i.value)+"\n")
        file_1_comp.close()
        with open(ds_file, 'rb') as afile:
            buf = afile.read()
            hasher_f_1.update(buf)
        continue
    else:
        pass
        
    #answer = input("continue?")
