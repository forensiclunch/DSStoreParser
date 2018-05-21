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
from ds_store_parser import ds_store_handler

__VERSION__ = "0.1.1"


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
                s_path.append(os.path.join(root, filename))
    else:
        s_path.append(os.path.join(options.source, s_name))
        
    for ds_file in s_path:
        file_io = open(ds_file, "rb")
        ds_handler = ds_store_handler.DsStoreHandler(
            file_io, ds_file
        )
        for record in ds_handler:
            record_handler.write_record(
                record
            )


class RecordHandler(object):
    def __init__(self):
        self.writer = csv.DictWriter(
            sys.stdout, delimiter="\t", lineterminator="\n",
            fieldnames=["filename", "type", "code", "value"]
        )
        self.writer.writeheader()

    def write_record(self, record):
        record_dict = record.as_dict()

        self.writer.writerow(
            record_dict
        )


if __name__ == '__main__':
    main()
