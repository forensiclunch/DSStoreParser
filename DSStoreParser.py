#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
# ds_store_tool
# ------------------------------------------------------
# Copyright 2019 G-C Partners, LLC
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
import unicodecsv as csv
import sys
import os
import argparse
from time import (gmtime, strftime)
import datetime
from ds_store_parser import ds_store_handler

__VERSION__ = "0.2.0"

folder_access_report = None
other_info_report = None
finder_window_change_report = None
all_records_ds_store_report = None

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
        type=commandline_arg,
        required=True,
        help='The source path to the .DS_Store file to parse.'
    )
    
    argument_parser.add_argument(
        '-o',
        '--out',
        dest='outdir',
        action="store",
        type=commandline_arg,
        required=True,
        help='The destination folder for parsed ds_store reports.'
    )
    return argument_parser
    
def main():
    arguments = get_arguments()
    options = arguments.parse_args()
    s_path = []
    s_name = u'.DS_Store'
    global folder_access_report, other_info_report, finder_window_change_report, all_records_ds_store_report
    opts_source = options.source
    opts_out = options.outdir
    
    try:
        folder_access_report = open(
                os.path.join(opts_out, 'DS_Store-Folder_Access_Report.tsv'),
                'wb'
            )
        finder_window_change_report = open(
                os.path.join(opts_out, 'DS_Store-Finder_Window_Changed_Report.tsv'),
                'wb'
            )
        other_info_report = open(
                os.path.join(opts_out, 'DS_Store-Miscellaneous_Info_Report.tsv'),
                'wb'
            )
        all_records_ds_store_report = open(
                os.path.join(opts_out, 'DS_Store-All_Parsed_Report.tsv'),
                'wb'
            )
    except:
        print 'Unable to proceed. Error creating reports.'
        sys.exit(0)
    
    # Accounting for paths ending with \"
    if opts_source[-1:] == '"':
        opts_source = opts_source[:-1]
    
    record_handler = RecordHandler()

    for root, dirnames, filenames in os.walk(opts_source):
        for filename in fnmatch.filter(filenames, s_name):
            parse(os.path.join(root, filename), record_handler, opts_source)
        
def parse(ds_file, record_handler, source):
    # script will update accessed ts for write access volume in macOS
    # when it reads contents of the file
    source_acc_time = os.stat(ds_file).st_atime
    source_acc_time = str(datetime.datetime.utcfromtimestamp(source_acc_time))
    source_mod_time = os.stat(ds_file).st_mtime
    source_mod_time = unicode(datetime.datetime.utcfromtimestamp(source_mod_time))
    try:
        # Account for parsing within Mac
        source_birth_time = os.stat(ds_file).st_birthtime
        source_birth_time = unicode(datetime.datetime.utcfromtimestamp(source_birth_time))
        source_chg_time = os.stat(ds_file).st_ctime
        source_chg_time = unicode(datetime.datetime.utcfromtimestamp(source_chg_time)) + '[UTC]'
    except:
        # when birthtime not available
        source_birth_time = os.stat(ds_file).st_ctime
        source_birth_time = unicode(datetime.datetime.utcfromtimestamp(source_birth_time))
        source_chg_time = ''

    source_size = os.stat(ds_file).st_size
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
                source,
                source_birth_time,
                source_mod_time,
                source_chg_time,
                source_acc_time
            )
    # When handler cannot parse ds, print exception as row
    except Exception as exp:        
        
        print 'ERROR: {} for file {}'.format(
            exp,
            source
            )
            
def commandline_arg(bytestring):
    unicode_string = bytestring.decode(sys.getfilesystemencoding())
    return unicode_string

class RecordHandler(object):
    def __init__(self):
        global folder_access_report, other_info_report, finder_window_change_report, all_records_ds_store_report
        fields = [
            u"path", 
            u"value", 
            u"type", 
            u"code", 
            u"source_size",
            u"source_mod_time",
            u"source_chg_time",
            u"source_create_time",
            u"source_acc_time",
            u"source_file"]
            
        # Codes that do not always mean that a folder was opened
        # Some codes are for informational purposes
        self.other_info_codes = [
            u"Iloc",
            u"dilc",
            u"cmmt",
            u"extn",
            u"logS",
            u"lg1S",
            u"modD",
            u"moDD",
            u"phyS",
            u"ph1S",
            u"ptbL",
            u"ptbN"
        ]
        
        # Codes that explicitly indicate a folder was opened
        self.opened_folder_codes = [
            u"dscl",
            u"fdsc",
            u"vSrn"
        ]
        
        # Codes that indicate the finder window changed for an open folder
        self.opened_folder_finder_window_changes = [
            u"BKGD",
            u"ICVO",
            u"LSVO",
            u"bwsp",
            u"fwi0",
            u"fwsw",
            u"fwvh",
            u"glvp",
            u"GRP0",
            u"icgo",
            u"icsp",
            u"icvo",
            u"icvp",
            u"icvt",
            u"info",
            u"lssp",
            u"lsvC",
            u"lsvo",
            u"lsvt",
            u"lsvp",
            u"lsvP",
            u"pict",
            u"bRsV",
            u"pBBk",
            u"vstl"
        ]
            
            
        self.fa_writer = csv.DictWriter(
            folder_access_report, delimiter="\t", lineterminator="\n",
            fieldnames=fields
        )
        self.fa_writer.writeheader()
        
        self.fc_writer = csv.DictWriter(
            finder_window_change_report, delimiter="\t", lineterminator="\n",
            fieldnames=fields
        )
        self.fc_writer.writeheader()
        
        self.oi_writer = csv.DictWriter(
            other_info_report, delimiter="\t", lineterminator="\n",
            fieldnames=fields
        )
        self.oi_writer.writeheader()
        
        self.ar_writer = csv.DictWriter(
            all_records_ds_store_report, delimiter="\t", lineterminator="\n",
            fieldnames=fields
        )
        self.ar_writer.writeheader()

    def write_record(self, record, ds_file, source, source_birth_time, source_mod_time, source_chg_time, source_acc_time):
        record_dict = record.as_dict()
        
        record_dict["source_file"] = ds_file
        code = record_dict["code"]
        abs_path_len = len(os.path.split(source)[0])
        
        record_dict["filename"] = record_dict["filename"].replace('\x0d','').replace('\x0a','')
        record_dict["path"] = os.path.split(ds_file)[0][abs_path_len:].replace('\\','/') + '/' + record_dict["filename"]
        del record_dict["filename"]
        
        if record_dict["path"][:1] != '/':
            record_dict["path"] = '/' + record_dict["path"]

        if record_dict["code"] == "dilc" or record_dict["code"] == "Iloc":
            record_dict["value"] = unicode(self.icon_handler(record_dict))
        if record_dict["code"] == "vstl":
            record_dict["value"] = unicode(self.style_handler(record_dict))

        record_dict["source_chg_time"] = source_chg_time
        record_dict["source_acc_time"] = source_acc_time + '[UTC]'
        record_dict["source_mod_time"] = source_mod_time + '[UTC]'
        record_dict["source_create_time"] = source_birth_time + '[UTC]'
        record_dict["source_size"] = os.stat(ds_file).st_size
        record_dict["value"] = unicode(self.update_descriptor(record_dict)) + str(record_dict["value"])
        
        self.ar_writer.writerow(record_dict)
        
        if code in self.other_info_codes:
            self.oi_writer.writerow(record_dict)
        elif code in self.opened_folder_codes:
            self.fa_writer.writerow(record_dict)
        elif code in self.opened_folder_finder_window_changes:
            self.fc_writer.writerow(record_dict)
        else:
            print 'Code not accounted for.', code
        
    def update_descriptor(self, record):
        types_dict = {
            "BKGD": u"Finder Folder Background Picture Changed: ",
            "ICVO": u"ICVO. Unknown. Icon View Options?: ",
            "Iloc": u"Icon Location or Index Changed: ",
            "LSVO": u"Unknown. List View Options? Changed: ",
            "bwsp": u"Finder Window Work Space Changed",
            "cmmt": u"Spotlight Comments Changed: ",
            "dilc": u"Desktop Icon Location Changed: ",
            "dscl": u"Is Directory Expanded in List View: ",
            "fdsc": u"Is Directory Expanded in Limited Finder Window: ",
            "extn": u"eFile Extension: ",
            "fwi0": u"Finder Window Information Changed",
            "fwsw": u"Finder window sidebar widt changed: ",
            "fwvh": u"Finder window sidebar height changed: ",
            "glvp": u"Gallery View Properties Changed: ",
            "GRP0": u"Group by Changed. Group Items by: ",
            "icgo": u"icgo. Unknown. Icon View?: ",
            "icsp": u"icsp. Unknown. Icom View?: ",
            "icvo": u"Icon View Options Changed: ",
            "icvp": u"Icon View Properties Changed: ",
            "icvt": u"Icon View Text Changed: ",
            "info": u"info: Unknown. Finder Info?:",
            "logS": u"Logical size updated: ",
            "lg1S": u"Logical size updated: ",
            "lssp": u"lssp. Unknown. List view scroll position changed?: ",
            "lsvC": u"List View Columns Changed: ",
            "lsvo": u"List View Options Changed: ",
            "lsvt": u"List View Text Size Changed: ",
            "lsvp": u"List View Properties Changed: ",
            "lsvP": u"List View Properties Changed: ",
            "modD": u"Modified date updated: ",
            "moDD": u"Modified date updated: ",
            "phyS": u"Physical size updated: ",
            "ph1S": u"Physical size updated: ",
            "pict": u"pict. Unknown. Background image changed?: ",
            "vSrn": u"Opened Folder in new tab: ",
            "bRsV": u"Browse in Selected View: ",
            "pBBk": u"Finder Folder Background Image Bookmark Changed: ",
            "vstl": u"View Style Changed: ",
            "ptbL": u"Originally sent to Trash. Trash Put Back Location: ",
            "ptbN": u"Originally sent to Trash. Trash Put Back Name: "
            }
        try:
            code_desc = unicode(types_dict[record["code"]])
        except:
            code_desc = u"Unknown Code: {0}".format(record["code"])
        return code_desc

    def icon_handler(self, record):

        r_value_hor = record["value"][0]
        r_value_ver = record["value"][1]
        r_value_idx = record["value"][2]
        if r_value_hor == 4294967295L:
            r_value_hor = u"Null"
        if r_value_ver == 4294967295L:
            r_value_ver = u"Null"
        if r_value_idx == 4294967295L:
            r_value_idx = u"Null"
        if record["code"] == u"Iloc":
            icon_val = "Location: ({0}, {1}), Selected Index: {2}".format(
                unicode(r_value_hor), 
                unicode(r_value_ver), 
                unicode(r_value_idx)
            )
        if record["code"] == u"dilc":
            icon_val = record["value"]
        return icon_val
            
    def style_handler(self, record):
        styles_dict = {
            '\x00\x00\x00\x00': u"view type null",
            "none": u"View type unselected",
            "icnv": u"icnv: Icon View",
            "clmv": u"clmv: Column View",
            "Nlsv": u"Nlsv: List View",
            "glyv": u"glyv: Gallery View",
            "Flwv": u"Flwv: CoverFlow View"
            }

        try: 
            code_desc = styles_dict[record["value"]]
        except:
            code_desc = "Unknown Code: {0}".format(record["value"])
        return code_desc

if __name__ == '__main__':
    main()
