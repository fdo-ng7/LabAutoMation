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
import os
jsonfile = "qalabasr-config.json"
script_path = os.path.dirname(os.path.abspath(__file__))
# print script_path
jsonpath = script_path + "/" + jsonfile
with open(jsonpath) as json_file:
    jdata = json.load(json_file)


# Physical Infrastructure Information
vc_ip = jdata['physical']['vcenter']['ip']
vc_user = jdata['physical']['vcenter']['username']
vc_pwd = jdata['physical']['vcenter']['password']
tftp_svr = jdata['physical']['tftp_svr']

esxi_list = jdata['nested']['esxi']
basename = jdata['config']['basename']
foldername = jdata['config']['foldername']

# Nested VM Config
esxi_cpu = jdata['nested']['config']['cpu']
esxi_mem = jdata['nested']['config']['mem']
guest_id = jdata['nested']['config']['guestid']
esxi_version = jdata['nested']['config']['esxversion']
esxi_rootpw = jdata['nested']['config']['rootpw']
vm_version = jdata['nested']['config']['vmx_version']

# Network
vm_network = jdata['network']['portgroup']
pg_vlan = jdata['network']['pg_vlan']
vm_gateway = jdata['network']['gateway']
vm_subnet = jdata['network']['subnet']
vm_dns = jdata['network']['dns']

iscsitarget = jdata['iscsiserver']['ip']
dest_datastore = jdata['datastore']
