#!/usr/bin/env python
"""
    Name: Variable Loader File
    Description: File will load all variables from Json file specified
    Usage: To all variables in this file use
        from variable_load import *
    This file could also be encrypted if desired
    Last Update:
        01/31/2018 - Created This file
"""
import json
with open('./ndc-config.json') as json_file:
    jdata = json.load(json_file)

# Physical Infrastructure Information
vc_ip = jdata['physical']['vcenter']['ip']
vc_user = jdata['physical']['vcenter']['username']
vc_pwd = jdata['physical']['vcenter']['password']
tftp_svr = jdata['physical']['tftp_svr']
