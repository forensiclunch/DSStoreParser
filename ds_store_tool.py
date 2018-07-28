#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
# ds_store_tool
# ------------------------------------------------------
# Copyright 2018 G-C Partners, LLC
# Nicole Ibrahim
#
# G-C Partners licenses this file to you under the Apache License, Version
# 2.0 (the "License"); you may not use this file except in compliance with the
# License.  You may obtain a copy of the License at:
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.  See the License for the specific language governing
# permissions and limitations under the License.
import fnmatch
import csv
import sys
import os
import argparse
from time import (gmtime, strftime)
import datetime
from ds_store_parser import ds_store_handler

__VERSION__ = "0.1.2"


def get_arguments():
    """Get needed options for the cli parser interface"""
    usage = """.DS_Store Parser CLI tool. v{}""".format(__VERSION__)

    argument_parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=(usage)
    )

    argument_parser.add_argument(
        '-s',
        '--source',
        dest='source',
        action="store",
        required=True,
        help='The source path to the .DS_Store file to parse.'
    )
    argument_parser.add_argument(
        '-r',
        '--recursive',
        dest='recrs',
        action="store_true",
        required=False,
        default=False,
        help='Recursive option. Recursively search for .DS_Store files in the source path provided.'
    )
    return argument_parser


def main():
    arguments = get_arguments()
    options = arguments.parse_args()
    s_path = []
    s_name = '.DS_Store'
    
    record_handler = RecordHandler()
    
    if options.recrs:
        for root, dirnames, filenames in os.walk(options.source):
            for filename in fnmatch.filter(filenames, s_name):
                parse(os.path.join(root, filename), record_handler, options.source)
    else:
        parse(os.path.join(options.source, s_name), record_handler, options.source)
        
def parse(ds_file, record_handler, source):
    
    source_acc_time = os.stat(ds_file).st_atime
    # script will update accessed ts for write access volume in macOS
    # when it reads contents of the file
    source_acc_time = str(datetime.datetime.utcfromtimestamp(source_acc_time))
    
    file_io = open(ds_file, "rb")

    try:
        ds_handler = ds_store_handler.DsStoreHandler(
            file_io, 
            ds_file
        )
        for record in ds_handler:
            record_handler.write_record(
                record, 
                ds_file, 
                source_acc_time, 
                source
            )
    # When handler cannot parse ds, print exception as row
    except Exception as exp:
        source_mod_time = os.stat(ds_file).st_mtime
        source_create_time = os.stat(ds_file).st_ctime
        source_size = os.stat(ds_file).st_size
        
        try:
            source_birth_time = os.stat(ds_file).st_birthtime
        except:
            source_birth_time = os.stat(ds_file).st_ctime
        print '{0}\t\t\t\t\t\t{1}\t{2}\t{3}\t{4}\t{5}\t{6}'.format(
            exp, 
            ds_file,
            str(datetime.datetime.utcfromtimestamp(source_mod_time)),
            str(datetime.datetime.utcfromtimestamp(source_create_time)),
            str(datetime.datetime.utcfromtimestamp(source_birth_time)),
            source_acc_time,
            source_size
            )


class RecordHandler(object):
    def __init__(self):
        self.writer = csv.DictWriter(
            sys.stdout, delimiter="\t", lineterminator="\n",
            fieldnames=[
            "file_exists", 
            "ds_store_path", 
            "filename", 
            "code", 
            "value", 
            "type", 
            "source_file", 
            "source_mod_time",
            "source_create_time",
            "source_birth_time",
            "source_acc_time",
            "source_size"]
        )
        self.writer.writeheader()

    def write_record(self, record, ds_file, source_acc_time, source):
        record_dict = record.as_dict()
        record_dict["source_file"] = ds_file
        
        abs_path_len = len(os.path.split(source)[0])
        
        record_dict["ds_store_path"] = os.path.split(ds_file)[0][abs_path_len:]
        record_dict["source_acc_time"] = source_acc_time
        
        record_file_path = os.path.join(
            os.path.split(ds_file)[0],
            record_dict["filename"]
            )


        if record_dict["code"] == "dilc" or record_dict["code"] == "Iloc":
            record_dict["value"] = self.icon_handler(record_dict)
        if record_dict["code"] == "vstl":
            record_dict["value"] = self.style_handler(record_dict)
            
        record_dict["file_exists"] = self.CheckIfFileExists(record_file_path)
        
        source_mod_time = os.stat(ds_file).st_mtime
        source_create_time = os.stat(ds_file).st_ctime
        source_size = os.stat(ds_file).st_size
        
        try:
            # Account for parsing within Mac
            source_birth_time = os.stat(ds_file).st_birthtime
        except:
            # when birthtime not available
            source_birth_time = os.stat(ds_file).st_ctime
        
        record_dict["source_mod_time"] = str(datetime.datetime.utcfromtimestamp(source_mod_time))
        record_dict["source_create_time"] = str(datetime.datetime.utcfromtimestamp(source_create_time))
        record_dict["source_birth_time"] = str(datetime.datetime.utcfromtimestamp(source_birth_time))
        record_dict["source_size"] = source_size
        
        record_dict["code"] = self.update_descriptor(record_dict)
        
        self.writer.writerow(record_dict)
        
    def CheckIfFileExists(self, record_file_name):
        if os.path.exists(record_file_name):
            return "True."
        else:
            return "False. File not found."
        
    def update_descriptor(self, record):
        types_dict = {
            "BKGD": "BKGD: Finder Folder Background Picture",
            "ICVO": "ICVO: Unknown. Icon View?",
            "Iloc": "Iloc: Icon Location and Index",
            "LSVO": "LSVO: Unknown. List View?",
            "bwsp": "bwsp: Finder Window Work Space Changed",
            "cmmt": "cmmt: Spotlight Comments",
            "dilc": "dilc: Desktop Icon Location",
            "dscl": "dscl: Directory Disclosed (Expanded) in List View",
            "fdsc": "fdsc: Directory Disclosed (Expanded) in Limited Finder Window",
            "extn": "extn: File Extension",
            "fwi0": "fwi0: Finder window information",
            "fwsw": "fwsw: Finder window sidebar width",
            "fwvh": "fwvh: Finder window sidebar height",
            "GRP0": "GRP0: Arrange by",
            "icgo": "icgo: Unknown",
            "icsp": "icsp: Unknown",
            "icvo": "icvo: Icon View Options",
            "icvp": "icvp: Icon View Properties",
            "icvt": "icvt: Icon View Text",
            "info": "info: Unknown",
            "logS": "logS: Logical size",
            "lg1S": "lg1S: Logical size",
            "lssp": "lssp: Unknown",
            "lsvC": "lsvC: List View Unknown",
            "lsvo": "lsvo: List View Options",
            "lsvt": "lsvt: List View Text",
            "lsvp": "lsvp: List View Properties",
            "lsvP": "lsvP: List View Properties",
            "modD": "modD: Modified date",
            "moDD": "moDD: Modified date",
            "phyS": "phyS: Physical size",
            "ph1S": "ph1S: Physical size",
            "pict": "pict: Unknown",
            "vSrn": "vSrn: Opened Folder in new Tab",
            "bRsV": "bRsV: Browse in Icon View",
            "pBBk": "pBBk: Finder Folder Background Image Bookmark",
            "vstl": "vstl: View Style",
            "ptbL": "ptbL: Trash Put Back Location",
            "ptbN": "ptbN: Trash Put Back Name"
            }
        try:
            code_desc = types_dict[record["code"]]
        except:
            code_desc = "Unknown Code: {0}".format(record["code"])
        return code_desc

    def icon_handler(self, record):

        r_value_hor = record["value"][0]
        r_value_ver = record["value"][1]
        r_value_idx = record["value"][2]
        if r_value_hor == 4294967295L:
            r_value_hor = "Null"
        if r_value_ver == 4294967295L:
            r_value_ver = "Null"
        if r_value_idx == 4294967295L:
            r_value_idx = "Null"
        if record["code"] == "Iloc":
            icon_val = "Location: ({0}, {1}), Selected Index: {2}".format(
                str(r_value_hor), 
                str(r_value_ver), 
                str(r_value_idx)
            )
        if record["code"] == "dilc":
            icon_val = record["value"]
        return icon_val
            
    def style_handler(self, record):
        styles_dict = {
            "": "Undefined",
            "icnv": "icnv: Icon View",
            "clmv": "clmv: Column View",
            "Nlsv": "Nlsv: List View",
            "Flwv": "Flwv: CoverFlow View"
            }
        try:
            code_desc = styles_dict[record["value"]]
        except:
            code_desc = "Unknown Code: {0}".format(record["value"])
        return code_desc

if __name__ == '__main__':
    main()
