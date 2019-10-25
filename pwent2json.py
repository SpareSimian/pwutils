#!/usr/bin/python3

# export passwd, group, shadow to json

import sys
from pprint import pprint
import pwent2dict
import json

# dump to json

json.dump(pwent2dict.pwent2dict(), sys.stdout)
#pprint(all_dict)
