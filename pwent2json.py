#!/usr/bin/env python

# export passwd, group, shadow, gshadow to json

# allow function-like print when using Python 2
from __future__ import print_function

import pwd
import grp
import spwd
import sys
import json
from pprint import pprint

# suck all three tables into memory

passwd = pwd.getpwall()
passwd_dict = {}
for pwent in passwd:
    pwent4dict = {}
    pwent4dict['pw_name'] = pwent.pw_name
    pwent4dict['pw_passwd'] = pwent.pw_passwd
    pwent4dict['pw_uid'] = pwent.pw_uid
    pwent4dict['pw_gid'] = pwent.pw_gid
    pwent4dict['pw_gecos'] = pwent.pw_gecos
    pwent4dict['pw_dir'] = pwent.pw_dir
    pwent4dict['pw_shell'] = pwent.pw_shell
    passwd_dict[pwent.pw_name] = pwent4dict

groups = grp.getgrall()
groups_dict = {}
for grpent in groups:
    grpent4dict = {}
    grpent4dict['gr_name'] = grpent.gr_name
    grpent4dict['gr_passwd'] = grpent.gr_passwd
    grpent4dict['gr_gid'] = grpent.gr_gid
    grpent4dict['gr_mem'] = grpent.gr_mem
    groups_dict[grpent.gr_name] = grpent4dict

shadow = spwd.getspall()
shadow_dict = {}
for spent in shadow:
    spent4dict = {}
    spent4dict['sp_nam'] = spent.sp_nam
    spent4dict['sp_pwd'] = spent.sp_pwd
    spent4dict['sp_lstchg'] = spent.sp_lstchg
    spent4dict['sp_min'] = spent.sp_min
    spent4dict['sp_max'] = spent.sp_max
    spent4dict['sp_warn'] = spent.sp_warn
    spent4dict['sp_inact'] = spent.sp_inact
    spent4dict['sp_expire'] = spent.sp_expire
    spent4dict['sp_flag'] = spent.sp_flag
    shadow_dict[spent.sp_nam] = spent4dict
    
all_dict = {}
all_dict['passwd'] = passwd_dict
all_dict['group'] = groups_dict
all_dict['shadow'] = shadow_dict

# dump to json

json.dump(all_dict, sys.stdout)
#pprint(all_dict)
