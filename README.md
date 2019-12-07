# Linux user/group Migration
Import/export/merge passwd/group/shadow database for user/group migration

These scripts are intended to be used to migrate users and groups  from an existing
Linux system to a new one. They should be used in combination with tools
like pwck, grpck, pwconv, and grpconv. 

The pwent2json.py script dumps the passwd, group, and shadow databases
to stdout in JSON format. This is moved to a target machine to merge
entries into its database. Note that Python lacks a gshadow module so we
don't migrate that. Use grpconv to migrate after the group database is
migrated.
