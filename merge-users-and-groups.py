#!/usr/bin/python3

# merge databases in json argument to existing databases in /etc and
# dump as new databases specified by arguments

import argparse
import io
import pwent2dict
import json
from pprint import pprint
import sys

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
#pprint(otherdb)

mydb = pwent2dict.pwent2dict()
#pprint(mydb)

# check for system users in imported db not in local db and warn about
# them

missing_system_users = []
for otheruser in otherdb['passwd'].values():
    #pprint(type(otheruser))
    #pprint(type(mydb['passwd']))
    if (otheruser['pw_uid'] < 1000) and (not otheruser['pw_name'] in mydb['passwd']):
        missing_system_users.append(otheruser['pw_name'])

if missing_system_users:
    print(
        "system users on other system not on local system:\n ",
        ' '.join(missing_system_users),
        "\nInstall missing packages and try again.",
        file=sys.stderr)
    sys.exit(1)

