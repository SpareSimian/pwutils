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
import os

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

# change group id number in passwd table to its name to avoid needing
# to remap it on collision later

def gid_to_group_name(groups, gid):
    for group in groups.values():
        if gid == group["gr_gid"]:
            return group["gr_name"]
    raise KeyError(gid + " in password file not in group file")

def passwd_gid_to_group_name(passwd, groups):
    for user in passwd.values():
        user["pw_gid"] = gid_to_group_name(groups, user["pw_gid"])

passwd_gid_to_group_name(otherpasswd, othergroup)
passwd_gid_to_group_name(mypasswd, mygroup)

def is_system_id(id):
    return (id < 1000) or (id > 60000)

def id_in_use(id_key, id_key_value, dict):
    """
    Return true if an ID is already in use.
    """
    for value in dict.values():
        if value[id_key] == id_key_value:
            return True
    return False

# check for system users in imported db not in local db and warn about
# them

missing_system_users = []
for otheruser in otherpasswd.values():
    if is_system_id(otheruser['pw_uid']) and not id_in_use('pw_name', otheruser['pw_name'], mypasswd):
        missing_system_users.append(otheruser['pw_name'])
        
if missing_system_users:
    print(
        "System users on other system not on local system:\n ",
        ' '.join(missing_system_users),
        #"\n",
        file=sys.stderr)

# check for system groups in imported db not in local db and warn about
# them

missing_system_groups = []
for othergroupvalue in othergroup.values():
    if is_system_id(othergroupvalue['gr_gid']) and not id_in_use('gr_name', othergroupvalue['gr_name'], mygroup):
        missing_system_groups.append(othergroupvalue['gr_name'])

if missing_system_groups:
    print(
        "System groups on other system not on local system:\n ",
        ' '.join(missing_system_groups),
        #"\n",
        file=sys.stderr)

def get_entry_by_id(id_key, id_key_value, dict):
    """return the dict entry with matching key value"""
    for value in dict.values():
        if value[id_key] == id_key_value:
            return value
    #pprint(dict)
    raise KeyError(id_key + " of " + id_key_value + " not found")

def has_entry_by_id(id_key, id_key_value, dict):
    """return true if the dict entry has matching key value"""
    for value in dict.values():
        if value[id_key] == id_key_value:
            return True
    return False

def merge_other_into_my(id_key, name_key, other, my, id_collisions):
    for value in other.values():
        otherid = value[id_key]
        othername = value[name_key]
        # add only if it's a new name, else preserve the local
        # user/group
        if not has_entry_by_id(name_key, othername, my):
            if id_in_use(id_key, otherid, my):
                id_collisions.append(otherid)
                print(" ID collision", otherid, "between",
                    othername, "there and",
                    get_entry_by_id(id_key, otherid, my)[name_key],
                    "here")
            else:
                my[otherid] = value
            #elif my[othername] != value:
            #   print("", othername, "differs\n")

# here we do groups first in case we need to fix up the pw_gid on a gid
# collision

# merge new groups from otherdb into mydb

print("Merging new groups...")
gid_collisions = []
merge_other_into_my('gr_gid', 'gr_name', othergroup, mygroup, gid_collisions)

# merge new users from otherdb into mydb

print("Merging new users...")
uid_collisions = []
merge_other_into_my('pw_uid', 'pw_name', otherpasswd, mypasswd, uid_collisions)

# uid_new and uid_collisions has the list of users on the other
# system that need to be added to shadow.

# now insert new users and groups that had collisions, choosing "holes"
# above 1000 for non-system users and 500 for system users

def find_free_id(oldid, destination_dict):
    '''
    find id not used as key in destination_dict
    oldid is used to determine where to start searching
    '''
    if is_system_id(oldid):
        candidate_id = 500
    else:
        candidate_id = 1000
    while True:
        if not candidate_id in destination_dict:
            return candidate_id
        candidate_id = candidate_id + 1
    
def insert_new_entries_allocating_ids(ids, id_key, dict_key, source_dict, destination_dict):
    for id in ids:
        source_entry = get_entry_by_id(id_key, id, source_dict)
        new_entry = copy.deepcopy(source_entry)
        new_id = find_free_id(id, destination_dict)
        new_entry[id_key] = new_id
        destination_dict[new_id] = new_entry
        print(" inserted ", new_entry[dict_key])

print("Merging colliding users...")
pprint(uid_collisions)
insert_new_entries_allocating_ids(ids=uid_collisions, id_key='pw_uid', dict_key='pw_name',
    source_dict=otherpasswd, destination_dict=mypasswd)

print("Merging colliding groups...")
pprint(gid_collisions)
insert_new_entries_allocating_ids(ids=gid_collisions, id_key='gr_gid', dict_key='gr_name',
    source_dict=othergroup, destination_dict=mygroup)

# merge shadows from otherdb into mydb (no ID processing!)
# must be done last after UID collisions are handled.

def user_name_to_uid(passwd, name):
    for user in passwd.values():
        if name == user["pw_name"]:
            return user["pw_uid"]
    raise KeyError("user " + name + " not in passwd file")

for othershadowvalue in othershadow.values():
    othershadowname = othershadowvalue['sp_nam']
    othershadowuid = user_name_to_uid(otherpasswd, othershadowname)
    if not has_entry_by_id('sp_nam', othershadowname, myshadow):
        # here we don't have to worry about uid collision
        myshadow[othershadowname] = othershadowvalue
    elif myshadow[othershadowname] != othershadowvalue:
        print("Shadow", othershadowname, "differs")

# convert the primary group names back to gids in mypasswd

def group_name_to_gid(groups, name):
    entry = get_entry_by_id("gr_name", name, groups)
    return entry["gr_gid"]

for user in mypasswd.values():
    user["pw_gid"] = group_name_to_gid(mygroup, user["pw_gid"])
    
# dump it all out into caller's directory

if not os.path.isdir(args.newdbdir):
    os.mkdir(args.newdbdir)

def write_pw_entry(file, entry, keys):
    first = True
    for key in keys:
        if not first:
            file.write(":")
        field = entry[key]
        if isinstance(field, list):
            file.write(",".join(field))
        else:
            file.write(str(field))
        first = False
    file.write("\n")

def write_pw_file(basename, dict, keys):
    f = open(os.path.join(args.newdbdir, basename), "w+")
    for entry in dict.values():
        write_pw_entry(f, entry, keys)
    f.close()
    
write_pw_file("passwd.new", mypasswd, [
    'pw_name',
    'pw_passwd',
    'pw_uid',
    'pw_gid',
    'pw_gecos',
    'pw_dir',
    'pw_shell'])
write_pw_file("group.new", mygroup, [
    'gr_name',
    'gr_passwd',
    'gr_gid',
    'gr_mem'])
write_pw_file("shadow.new", myshadow, [
    'sp_nam',
    'sp_pwd',
    'sp_lstchg',
    'sp_min',
    'sp_max',
    'sp_warn',
    'sp_inact',
    'sp_expire',
    'sp_flag'])
