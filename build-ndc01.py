#!/usr/bin/env python
# fng

"""
    Build Script to deploy nested environment

"""
import os
import requests
from pyVim import connect
from pyVmomi import vim
# Import Variables
from config.variable_load import *
from create_esxi import create_esxi_vm


def main():
    print "Started Build-NDC Script"
    print "Check Variables"
    print "Check vCenter Creds"
    print "vcip  -", vc_ip
    print "vcuid -", vc_user
    print "vcpwd -", vc_pwd

    print "Connecting to vCenter ", vc_ip

    service_instance = connect.SmartConnectNoSSL(host=vc_ip,
                                                 user=vc_user,
                                                 pwd=vc_pwd)

    if not service_instance:
        print("Could not connect to the specified host using specified "
              " username and password")
        return -1

    # Initializing Variables
    content = service_instance.RetrieveContent()
    datacenter = content.rootFolder.childEntity[0]
    vmfolder = datacenter.vmFolder
    hosts = datacenter.hostFolder.childEntity
    resource_pool = hosts[0].resourcePool
    dstore = "srlab03STD_L1"
    print "Start Build DC Process"
    # print esxi_list
    count = len(esxi_list)
    print "Esxi to build :", count

    for esxi in esxi_list:
        # print esxi['ip']
        no = esxi_list.index(esxi) + 1
        vmname = basename + '{:02}'.format(no)

        print "Creatig VM - ", vmname
        create_esxi_vm(name=vmname, service_instance=service_instance,
                       vm_folder=vmfolder, resource_pool=resource_pool,
                       datastore=dstore, memory=esxi_mem,
                       vcpu=esxi_cpu, network="VM Network", guestid=esxi_version)
    # create_esxi_vm(name, service_instance, vm_folder, resource_pool,
    #                   datastore, memory, vcpu, network, guestid):

    return 0


# Start program
if __name__ == "__main__":
    main()
