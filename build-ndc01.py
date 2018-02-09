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


def create_folder(content, host_folder, folder_name):
    host_folder.CreateFolder(folder_name)


def get_obj(content, vimtype, name):
    obj = None
    container = content.viewManager.CreateContainerView(
        content.rootFolder, vimtype, True)
    for c in container.view:
        if c.name == name:
            obj = c
            break
    return obj


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
    vmfolder = get_obj(content, [vim.Folder], foldername)
    if vmfolder is None:
        vmfolder = datacenter.vmFolder
    hosts = datacenter.hostFolder.childEntity
    resource_pool = hosts[0].resourcePool

    # Initializing Variable Load
    #foldername = basename
    dstore = dest_datastore

    print "Start Build DC Process"

    # Create VM folder - Using basename
    if (get_obj(content, [vim.Folder], foldername)):
        print("Folder '%s' already exists" % foldername)
    else:
        create_folder(content, datacenter.vmFolder, foldername)
        print("Successfully created the VM folder '%s'" % foldername)

    # print esxi_list
    print "Deploying ESXI:"
    count = len(esxi_list)
    print "Esxi to build :", count

    for esxi in esxi_list:
        # print esxi['ip']
        no = esxi_list.index(esxi) + 1
        vmname = basename + "esx" + '{:02}'.format(no)

        print "Creating VM - ", vmname
        # print "VMX_Version - ", vm_version
        create_esxi_vm(name=vmname, service_instance=service_instance,
                       vm_folder=vmfolder, resource_pool=resource_pool,
                       datastore=dstore, memory=esxi_mem,
                       vcpu=esxi_cpu, network=vm_network, guestid=guest_id,
                       vmxversion=vm_version)
    # create_esxi_vm(name, service_instance, vm_folder, resource_pool,
    #                   datastore, memory, vcpu, network, guestid, vmx_version):

    return 0


# Start program
if __name__ == "__main__":
    main()
