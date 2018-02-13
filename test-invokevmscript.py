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
from vm_nic import get_vm_macaddr
from modules.upload_file_to_vm import upload_file_to_vm, invoke_vmscript


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

# SCript to Transfer files via scp
# Requirement must be configured with ssh_keys to allow passwordless
# transfers


def transfer_via_scp(server, file_list):
    import os
    print "Transfering Files to: ", server

    # for itm in file_list:
    #     print " - uploading - ", itm
    #     #os.system("scp " + itm + " ansible@10.159.81.200:/tmp/")
    os.system("scp " + file_list[0] + " ansible@10.159.81.200:/var/lib/tftpboot/KS/")
    os.system("scp " + file_list[1] + " ansible@10.159.81.200:/var/lib/tftpboot/pxelinux.cfg/")
    os.system("scp " + file_list[2] + " ansible@10.159.81.200:/var/lib/tftpboot/pxelinux.cfg/boot")


def main():
    print "000 - Started Build-NDC Script"
    print "Check Variables"
    print "Check vCenter Creds"
    print "vcip  -", vc_ip
    print "vcuid -", vc_user
    print "vcpwd -", vc_pwd
    print "Nested VM info: "
    print " - GuestID -", guest_id
    print " - VMXVersion", vm_version

    print "001 - Connecting to vCenter ", vc_ip

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

    # print "002 - Start Build DC Process"
    #
    # # 001 Create VM folder - Using basename
    # if (get_obj(content, [vim.Folder], foldername)):
    #     print("Folder '%s' already exists" % foldername)
    # else:
    #     create_folder(content, datacenter.vmFolder, foldername)
    #     print("Successfully created the VM folder '%s'" % foldername)
    #
    # # 002 Build ESXI VMs
    # # print esxi_list
    # print "005 - Deploying ESXI:"
    # count = len(esxi_list)
    # print "Esxi to build :", count
    # esxi_vms = []
    # for esxi in esxi_list:
    #     # print esxi['ip']
    #     no = esxi_list.index(esxi) + 1
    #     vmname = basename + "esx" + '{:02}'.format(no)
    #     esxi_vms.append(vmname)
    #     print "Creating VM - ", vmname
    #     # print "VMX_Version - ", vm_version
    #     create_esxi_vm(name=vmname, service_instance=service_instance,
    #                    vm_folder=vmfolder, resource_pool=resource_pool,
    #                    datastore=dstore, memory=esxi_mem,
    #                    vcpu=esxi_cpu, network=vm_network, guestid=guest_id,
    #                    vmxversion=vm_version)
    # # create_esxi_vm(name, service_instance, vm_folder, resource_pool,
    # #                   datastore, memory, vcpu, network, guestid, vmx_version):
    #
    # print "Esxi deployment completed"
    # print esxi_vms
    # print len(esxi_vms)

    # # 003 Generate KS Script
    # print "010 - Generating KS Process"
    # from generate_ks import generate_ks
    # # def generate_ks(macaddr, esx_version, vlan, ipaddr, gateway, nameserver,
    # #    netmask, hostname, rootpw, iscitarget)
    #
    # for i in range(len(esxi_vms)):
    #     print esxi_vms[i], " -- ",  esxi_list[i]['ip']
    #
    #     vmip = esxi_list[i]['ip']
    #     vmobj = get_obj(content, [vim.VirtualMachine], esxi_vms[i])
    #     # print vmobj
    #     # Get macaddr of Network Adapter 1
    #     mac = get_vm_macaddr(content, vmobj, 1)
    #     print "MAC - ", mac
    #
    #     # Generate KS
    #     ks_files = generate_ks(macaddr=mac, esx_version=esxi_version, vlan=pg_vlan,
    #                            ipaddr=vmip, gateway=vm_gateway, nameserver=vm_dns,
    #                            netmask=vm_subnet, esxhostname=esxi_vms[i],
    #                            rootpw=esxi_rootpw, iscsitarget=iscsitarget)
    #
    #     transfer_via_scp(tftp_svr, ks_files)
    #
    #     # Power On VM
    #     task = vmobj.PowerOn()
    # return 0

    # # Testing upload file script
    # # Teested Working
    # iscsivm = "iscstore01"
    # upload_file = "testfile.txt"
    # vm_path = "c:\\testfile.txt"
    # uuid = None
    # upload_file_to_vm(content, iscsivm, uuid, upload_file, vm_path)

    # # This sectiona manually defined how to updlad a file to VM
    # # Test Uploading file to ISCSI server
    # iscsivm = "iscstore01"
    # uuid = "564d57ad-b834-1a1b-e6b7-300fce0061b6"
    # uuid = ""
    # vm = None
    # if uuid:
    #     print "Searching vm via uuid =", uuid
    #     search_index = content.searchIndex
    #     vm = search_index.FindByUuid(None, uuid, True)
    #     print vm
    # elif iscsivm:
    #     #content = si.RetrieveContent()
    #     vm = get_obj(content, [vim.VirtualMachine], iscsivm)
    #
    # print vm
    #
    # tools_status = vm.guest.toolsStatus
    # if (tools_status == 'toolsNotInstalled' or
    #         tools_status == 'toolsNotRunning'):
    #     raise SystemExit(
    #         "VMwareTools is either not running or not installed. "
    #         "Rerun the script after verifying that VMWareTools "
    #         "is running")
    #
    # upload_file = "testfile.txt"
    # vm_path = "c:\\testfile.txt"
    # creds = vim.vm.guest.NamePasswordAuthentication(
    #     username="administrator", password="Passw0rd!")
    # with open(upload_file, 'rb') as myfile:
    #     args = myfile.read()
    #
    # print upload_file
    # print vm_path
    # print "arrgs - ", args
    #
    # try:
    #     file_attribute = vim.vm.guest.FileManager.FileAttributes()
    #     url = content.guestOperationsManager.fileManager. \
    #         InitiateFileTransferToGuest(vm, creds, vm_path,
    #                                     file_attribute,
    #                                     len(args), True)
    #     # When : host argument becomes https://*:443/guestFile?
    #     # Ref: https://github.com/vmware/pyvmomi/blob/master/docs/ \
    #     #            vim/vm/guest/FileManager.rst
    #     # Script fails in that case, saying URL has an invalid label.
    #     # By having hostname in place will take take care of this.
    #     import re
    #     url = re.sub(r"^https://\*:", "https://*:", url)
    #     resp = requests.put(url, data=args, verify=False)
    #     if not resp.status_code == 200:
    #         print "Error while uploading file"
    #     else:
    #         print "Successfully uploaded file"
    # except IOError, e:
    #     print e

    print "Test invoke vm script"

    script_text = "Get-ChildItem c:\\"
    invoke_vmscript(content, "administrator", "Passw0rd!", "iscstore01",
                    script_text, True)


# Start program
if __name__ == "__main__":
    main()
