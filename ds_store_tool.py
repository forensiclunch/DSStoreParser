#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
import difflib
import sys, os
import filecmp
import hashlib
import atexit
from time import strftime, gmtime

try:
    import ds_store
except:
    print("Unable to import ds_store module\
    \nRun 'pip install ds_store' to install dependancy")
    sys.exit(1)
path = os.path.join(os.path.split(sys.argv[0])[0],'tmp')
file_1 = os.path.join(path,str(os.getpid())+'comp_file_1.txt')
file_2 = os.path.join(path,str(os.getpid())+'comp_file_2.txt')

def Main():
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

    store = ds_store.DSStore.open(ds_file, 'rb')

    if action.lower() == 'parse':
        print("DSStoreEntry_Filename\tDSStoreEntry_Type\tDSStoreEntry_Code\tDSStoreEntry_Value\n")
        for i in store:
            print(str(i.filename)+"\t"+str(i.type)+"\t"+str(i.code)+"\t"+str(i.value)+"\n")
        sys.exit(1)
        
    print "\nWatching .DS_Store for changes\n\nPress Ctrl+C to stop script"
    if os.path.isdir(os.path.join(os.path.split(sys.argv[0])[0],'tmp')):
        pass
    else:
        os.mkdir(os.path.join(os.path.split(sys.argv[0])[0],'tmp'))
        
    with open(file_1, 'wb') as f1:
        f1.write("DSStoreEntry_Filename\tDSStoreEntry_Type\tDSStoreEntry_Code\tDSStoreEntry_Value\n")
        for i in store:
           f1.write(str(i.filename)+"\t"+str(i.type)+"\t"+str(i.code)+"\t"+str(i.value)+"\n")

    hasher_f_1 = hashlib.md5()
         
    with open(ds_file, 'rb') as afile:
        buf = afile.read()
        hasher_f_1.update(buf)

    while True:
        hasher_f_2 = hashlib.md5()

        with open(ds_file, 'rb') as afile:
            buf = afile.read()
            hasher_f_2.update(buf)
        
        if hasher_f_1.hexdigest()!=hasher_f_2.hexdigest():
            store = ds_store.DSStore.open(ds_file, 'rb')
            # Recreate file 2
            with open(file_2, 'wb') as f2:
                f2.write("DSStoreEntry_Filename\tDSStoreEntry_Type\tDSStoreEntry_Code\tDSStoreEntry_Value\n")
                for i in store:
                   f2.write(str(i.filename)+"\t"+str(i.type)+"\t"+str(i.code)+"\t"+str(i.value)+"\n")

            hasher_f_1 = hashlib.md5()
            with open(file_1, 'rb') as f1:
                lines1 = f1.readlines()

            with open(file_2, 'rb') as f2:
                lines2 = f2.readlines()
                
            print strftime("%m/%d/%Y %H:%M:%S", gmtime()),"---------------------------------"
            
            # Get differences
            diff = difflib.ndiff(lines1,lines2)
            changes = [l for l in diff if l.startswith('+ ') or l.startswith('- ') or l.startswith('! ')]
            
            for i in changes:
                print i
                
            print ''
            
            store = ds_store.DSStore.open(ds_file, 'rb')
            # Recreate file 1
            with open(file_1, 'wb') as f1:
                f1.write("DSStoreEntry_Filename\tDSStoreEntry_Type\tDSStoreEntry_Code\tDSStoreEntry_Value\n")
                for i in store:
                   f1.write(str(i.filename)+"\t"+str(i.type)+"\t"+str(i.code)+"\t"+str(i.value)+"\n")
                   
            with open(ds_file, 'rb') as afile:
                buf = afile.read()
                hasher_f_1.update(buf)
            continue
        else:
            pass
    
if __name__ == '__main__':
    try:
        Main()
    except KeyboardInterrupt:
        print "Exiting and cleaning up...."
        os.remove(file_1)
        if os.path.exists(file_2):
            os.remove(file_2)
        os.rmdir(path)

