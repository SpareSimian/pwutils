# pwutils
Import/export/merge passwd/group/shadow database for user/group migration

The pwent2json.py script dumps the passwd, group, and shadow databases
to stdout in JSON format. This is moved to a target machine to merge
entries into its database.
