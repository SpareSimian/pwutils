#!/usr/bin/python3

# merge databases in json argument to existing databases in /etc and
# dump as new databases specified by arguments

# allow function-like print when using Python 2
from __future__ import print_function

import argparse
import io
import pwent2dict
import json
from pprint import pprint

desc = """
Load another server's password/group database in JSON format and merge
it the local server's database. Output the result to the named database
files. The input file is expected to have been written by pwent2json.py.
"""

parser = argparse.ArgumentParser(description= desc)
parser.add_argument('otherdb', type=str, help='JSON file with users and groups to merge')
parser.add_argument('newdbdir', type=str, help='directory into which the new database is written')
args = parser.parse_args()

otherdb = json.load(io.open(args.otherdb))
pprint(otherdb)

mydb = pwent2dict.pwent2dict()
pprint(mydb)
