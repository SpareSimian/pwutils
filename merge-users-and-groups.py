#!/usr/bin/python3

# merge databases in json argument to existing databases in /etc and
# dump as new databases specified by arguments

import argparse
import io
import pwent2dict
import json
from pprint import pprint
import sys
import copy

desc = """
Load another server's password/group database in JSON format and merge
it the local server's database. Output the result to the named database
files. The input file is expected to have been written by pwent2json.py.
"""

parser = argparse.ArgumentParser(description= desc)
parser.add_argument('otherdb', type=str, help='JSON file with users and groups to merge')
parser.add_argument('newdbdir', type=str, help='directory into which the new database is written')
args = parser.parse_args()

# load the databases
otherdb = json.load(io.open(args.otherdb))
mydb = pwent2dict.pwent2dict()

# handy references to sub-objects
otherpasswd = otherdb['passwd']
othergroup = otherdb['group']
othershadow = otherdb['shadow']
mypasswd = mydb['passwd']
mygroup = mydb['group']
myshadow = mydb['shadow']

def is_system_id(id):
    return (id < 1000) or (id > 60000)

# check for system users in imported db not in local db and warn about
# them

missing_system_users = []
for otheruser in otherpasswd.values():
    if is_system_id(otheruser['pw_uid'] and (not otheruser['pw_name'] in mypasswd):
        missing_system_users.append(otheruser['pw_name'])

if missing_system_users:
    print(
        "\nSystem users on other system not on local system:\n ",
        ' '.join(missing_system_users),
        "\n",
        file=sys.stderr)

# check for system groups in imported db not in local db and warn about
# them

missing_system_groups = []
for othergroupvalue in othergroup.values():
    if is_system_id(othergroupvalue['gr_gid']) and (not othergroupvalue['gr_name'] in mygroup):
        missing_system_groups.append(othergroupvalue['gr_name'])

if missing_system_groups:
    print(
        "\nSystem groups on other system not on local system:\n ",
        ' '.join(missing_system_groups),
        "\n",
        file=sys.stderr)


def id_in_use(id_key, id_key_value, dict):
    """
    For all tables the primary key is the name and the numeric ID is a unique secondary key.
    Return true if an ID is already in use.
    """
    for value in dict.values():
        if value[id_key] == id_key_value:
            return True
    return False

def get_entry_by_id(id_key, id_key_value, dict):
    """return the dict entry with matching key value"""
    for value in dict.values():
        if value[id_key] == id_key_value:
            return value
    pprint(dict)
    raise KeyError(id_key + "[" + id_key_value + "] not found")

def merge_other_into_my(id_key, name_key, other, my, id_collisions):
    id_collisions = []
    for value in other.values():
        otherid = value[id_key]
        if not is_system_id(otherid):
            othername = value[name_key]
            if not othername in my:
                if id_in_use(id_key, otherid, my):
                    id_collisions.append(otherid)
                    print(" ID collision", otherid, "between",
                        othername, "there and",
                        get_entry_by_id(id_key, otherid, my)[name_key],
                        "here\n")
                    else:
                        my[othername] = value
            #elif my[othername] != value:
                #print("", othername, "differs\n")

# here we do groups first in case we need to fix up the pw_gid on a gid
# collision

# merge new groups from otherdb into mydb
gid_collisions = []
merge_other_into_my('gr_uid', 'gr_name', othergroup, mygroup, gid_collections)

# merge new users from otherdb into mydb
uid_collisions = []
merge_other_into_my('pw_uid', 'pw_name', otherpasswd, mypasswd, uid_collections)

# now insert new users and groups that had collisions, choosing "holes"
# above 1000

def insert_new_entries_allocating_ids(ids, id_key, dict_key, source_dict, destination_dict):
    for id in ids:
        source_entry = get_entry_by_id(id_key, id, source_dict)
        new_entry = copy.deep_copy(source_entry)
        new_id = find_free_id(id_key, destination_dict)
        new_entry[id_key] = new_id
        destination_dict[new_entry[dict_key]] = new_entry

insert_new_entries_allocating_ids(ids=uid_collisions, id_key='pw_uid', dict_key='pw_name',
    source_dict=otherpasswd, destination_dict=mypasswd)

insert_new_entries_allocating_ids(ids=gid_collisions, id_key='gr_gid', dict_key='gr_name',
    source_dict=othergroup, destination_dict=mygroup)

# merge shadows from otherdb into mydb (no ID processing!)
# must be done last after UID collisions are handled.

for othershadowvalue in othershadow.values():
    othershadowname = othershadowvalue['sp_nam']
    othershadowuid = otherpasswd[othershadowname]['pw_uid']
    if not is_system_id(othershadowuid):
        if not othershadowname in myshadow:
            # here we don't have to worry about uid collision
            myshadow[othershadowname] = othershadowvalue
        elif myshadow[othershadowname] != othershadowvalue:
            print("Shadow", othershadowname, "differs\n")

