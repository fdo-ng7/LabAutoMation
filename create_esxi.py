#!/usr/bin/env python
# William lam
# www.virtuallyghetto.com

"""
vSphere SDK for Python program for creating tiny VMs (1vCPU/128MB) with random
names using the Marvel Comics API
Syntax:
    Executing as script:
    create_esxi.py -h hosts -u user -p password -d datastore -n name -v vCpu
    -m memorymb -g guestId
    Execting as module:
        import create_esxi
        create_esxi_vm()
Updates:
    01/31/2018 - FNG Edited code to blank Create ESXI VMs
        - VMs Specs MEM, CPU, 2xVMXNet Nic, 8GB HDD, HVH Enabled.
        - Default 8GB and 4cpu
        - Creates NICs and Attaches to VDS
    02/01/2018 - NIC can only be attached to VDS - Static Binding PG
        - Added create_nic_backing function to handle ephemeral and
        staticbinding ports.

"""

import atexit
import hashlib
import json

import random
import time

import requests
from pyVim import connect
from pyVmomi import vim

from tools import cli
from tools import tasks


def get_args():
    """
    Use the tools.cli methods and then add a few more arguments.
    """
    parser = cli.build_arg_parser()

    parser.add_argument('-d', '--datastore',
                        required=True,
                        action='store',
                        help='Name of Datastore to create VM in')

    parser.add_argument('-n', '--name',
                        required=True,
                        action='store',
                        help='Name for VM')

    parser.add_argument('-m', '--memorymb',
                        required=False,
                        action='store',
                        help='Memory in MB')

    parser.add_argument('-v', '--vcpunum',
                        required=False,
                        action='store',
                        help='Number of CPU')

    parser.add_argument('-w', '--network',
                        required=True,
                        action='store',
                        help='VDS Portgroup')

    parser.add_argument('-g', '--guestid',
                        required=False,
                        action='store',
                        help='Guest ID for ESXI version')

    parser.add_argument('-x', '--vmxversion',
                        required=False,
                        action='store',
                        help='VMX version')

    parser.add_argument('-l', '--location',
                        required=False,
                        action='store',
                        help='VM Folder name')

    args = parser.parse_args()

    return cli.prompt_for_password(args)


def get_obj(content, vimtype, name):
    obj = None
    container = content.viewManager.CreateContainerView(
        content.rootFolder, vimtype, True)
    for c in container.view:
        if c.name == name:
            obj = c
            break
    return obj


# port_find and search_port script required to find VDS PG
def port_find(dvs, key):
    obj = None
    ports = dvs.FetchDVPorts()
    for c in ports:
        if c.key == key:
            obj = c
    return obj

# search for port key


def search_port(dvs, portgroupkey):
    search_portkey = []
    criteria = vim.dvs.PortCriteria()
    criteria.connected = False
    criteria.inside = True
    criteria.portgroupKey = portgroupkey
    ports = dvs.FetchDVPorts(criteria)
    for port in ports:
        search_portkey.append(port.key)
    # print(search_portkey)
    return search_portkey[0]


# creates port backing for ephemeral and static binding
# returns nicspec.device.baking
# reference: https://github.com/vmware/pyvmomi-community-samples/blob/master/samples/change_vm_vif.py
def create_nic_backing(portgroup):

    nic_type = portgroup.config.type
    if nic_type == "ephemeral":
        print "Create ephemeral device.backing"
        dvs = portgroup.config.distributedVirtualSwitch
        #portKey = search_port(dvs, portgroup.key)
        #port = port_find(dvs, portKey)
        device_backing = \
            vim.vm.device.VirtualEthernetCard.DistributedVirtualPortBackingInfo()
        device_backing.port = vim.dvs.PortConnection()
        device_backing.port.portgroupKey = portgroup.key
        # print portgroup.config.distributedVirtualSwitch.uuid
        device_backing.port.switchUuid = portgroup.config.distributedVirtualSwitch.uuid
        #device_backing.port.portKey = portgroup.key
        return device_backing
    elif nic_type == "earlyBinding":
        print "Create static device.backing"
        dvs = portgroup.config.distributedVirtualSwitch
        portKey = search_port(dvs, portgroup.key)
        port = port_find(dvs, portKey)
        device_backing = \
            vim.vm.device.VirtualEthernetCard.DistributedVirtualPortBackingInfo()
        device_backing.port = vim.dvs.PortConnection()
        device_backing.port.portgroupKey = port.portgroupKey
        device_backing.port.switchUuid = port.dvsUuid
        device_backing.port.portKey = port.key
        # print "portgroup info =  ", port
        return device_backing
    else:
        print "Can't Configure nic_type : ", nic_type
        print "Update Code in create_nic_backing()"
        return -1


def create_esxi_vm(name, service_instance, vm_folder, resource_pool,
                   datastore, memory, vcpu, network, guestid, vmxversion):
    """Creates a dummy VirtualMachine with 1 vCpu, 128MB of RAM.

    :param name: String Name for the VirtualMachine
    :param service_instance: ServiceInstance connection
    :param vm_folder: Folder to place the VirtualMachine in
    :param resource_pool: ResourcePool to place the VirtualMachine in
    :param datastore: DataStrore to place the VirtualMachine on
    """
    content = service_instance.RetrieveContent()

    if get_obj(content, [vim.VirtualMachine], name):
        print "VM with name: ", name, " already exists..."
        return 0

    network_pxe = "vmnetwork-vds"
    network_vm = "vmnetwork-vds"
    nic_type = "VMXNET3"
    vm_name = name
    disk_size = 8
    disk_type = "thin"
    datastore_path = '[' + datastore + '] ' + vm_name
    if memory is None:
        memory = 8192
    if vcpu is None:
        vcpu = 4
    if guestid is None:
        guestid = 'vmkernel5Guest'
        # guestid = 'vmkernel6Guest'
    if vmxversion is None:
        vmxversion = 'vmx-11'
        # vmx_version is 'vmx-11'

    vmx_file = vim.vm.FileInfo(logDirectory=None,
                               snapshotDirectory=None,
                               suspendDirectory=None,
                               vmPathName=datastore_path)

    device_changes = []

    # Addig Network Device 1 - VDS SWitch - ephemeral and static
    # Gather PG and VDS info
    portgroup = None
    portgroup = get_obj(content,
                        [vim.dvs.DistributedVirtualPortgroup], network_pxe)
    print "Creating NIC 1 on portgroup - ", network_pxe
    if portgroup is None:
        print("Portgroup" + portgroup + " not Found in DVS ...")
        exit(0)

    nic_spec = vim.vm.device.VirtualDeviceSpec()
    nic_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.add
    nic_spec.device = vim.vm.device.VirtualVmxnet3()
    nic_spec.device.deviceInfo = vim.Description()
    nic_spec.device.backing = create_nic_backing(portgroup)
    nic_spec.device.connectable = vim.vm.device.VirtualDevice.ConnectInfo()
    nic_spec.device.connectable.startConnected = True
    nic_spec.device.connectable.allowGuestControl = True
    nic_spec.device.connectable.connected = False
    nic_spec.device.connectable.status = 'untried'
    nic_spec.device.wakeOnLanEnabled = True
    nic_spec.device.addressType = 'assigned'
    device_changes.append(nic_spec)

    # Addig Network Device 2 - VDS SWitch
    # Gather PG and VDS info
    print "Creating NIC 2 on portgroup - ", network_vm
    portgroup = None
    portgroup = get_obj(content,
                        [vim.dvs.DistributedVirtualPortgroup], network_pxe)
    if portgroup is None:
        print("Portgroup" + portgroup + " not Found in DVS ...")
        exit(0)

    nic_spec = vim.vm.device.VirtualDeviceSpec()
    nic_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.add
    nic_spec.device = vim.vm.device.VirtualVmxnet3()
    nic_spec.device.deviceInfo = vim.Description()
    nic_spec.device.backing = create_nic_backing(portgroup)
    nic_spec.device.connectable = vim.vm.device.VirtualDevice.ConnectInfo()
    nic_spec.device.connectable.startConnected = True
    nic_spec.device.connectable.allowGuestControl = True
    nic_spec.device.connectable.connected = False
    nic_spec.device.connectable.status = 'untried'
    nic_spec.device.wakeOnLanEnabled = True
    nic_spec.device.addressType = 'assigned'
    device_changes.append(nic_spec)

    # # Addig Network Device 1 - VDS SWitch
    # # Gather PG and VDS info
    # portgroup = None
    # portgroup = get_obj(content,
    #                     [vim.dvs.DistributedVirtualPortgroup], network_pxe)
    # print "Creating NIC 1 on portgroup - ", network_pxe
    # if portgroup is None:
    #     print("Portgroup" + portgroup + " not Found in DVS ...")
    #     exit(0)
    #
    # dvs = portgroup.config.distributedVirtualSwitch
    # portKey = search_port(dvs, portgroup.key)
    # port = port_find(dvs, portKey)
    # nic_spec = vim.vm.device.VirtualDeviceSpec()
    # nic_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.add
    # nic_spec.device = vim.vm.device.VirtualVmxnet3()
    # nic_spec.device.deviceInfo = vim.Description()
    # nic_spec.device.backing = \
    #     vim.vm.device.VirtualEthernetCard.DistributedVirtualPortBackingInfo()
    # nic_spec.device.backing.port = vim.dvs.PortConnection()
    # nic_spec.device.backing.port.portgroupKey = port.portgroupKey
    # nic_spec.device.backing.port.switchUuid = port.dvsUuid
    # nic_spec.device.backing.port.portKey = port.key
    # nic_spec.device.connectable = vim.vm.device.VirtualDevice.ConnectInfo()
    # nic_spec.device.connectable.startConnected = True
    # nic_spec.device.connectable.allowGuestControl = True
    # nic_spec.device.connectable.connected = False
    # nic_spec.device.connectable.status = 'untried'
    # nic_spec.device.wakeOnLanEnabled = True
    # nic_spec.device.addressType = 'assigned'
    # device_changes.append(nic_spec)
    #
    # # Addig Network Device 2 - VDS SWitch
    # # Gather PG and VDS info
    # print "Creating NIC 2 on portgroup - ", network_vm
    # portgroup = None
    # portgroup = get_obj(content,
    #                     [vim.dvs.DistributedVirtualPortgroup], network_vm)
    # if portgroup is None:
    #     print("Portgroup not Found in DVS ...")
    #     exit(0)
    #
    # print portgroup.config.type
    # dvs = portgroup.config.distributedVirtualSwitch
    # portKey = search_port(dvs, portgroup.key)
    # port = port_find(dvs, portKey)
    # nic_spec = vim.vm.device.VirtualDeviceSpec()
    # nic_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.add
    # nic_spec.device = vim.vm.device.VirtualVmxnet3()
    # nic_spec.device.deviceInfo = vim.Description()
    # nic_spec.device.backing = \
    #     vim.vm.device.VirtualEthernetCard.DistributedVirtualPortBackingInfo()
    # nic_spec.device.backing.port = vim.dvs.PortConnection()
    # nic_spec.device.backing.port.portgroupKey = port.portgroupKey
    # nic_spec.device.backing.port.switchUuid = port.dvsUuid
    # nic_spec.device.backing.port.portKey = port.key
    # nic_spec.device.connectable = vim.vm.device.VirtualDevice.ConnectInfo()
    # nic_spec.device.connectable.startConnected = True
    # nic_spec.device.connectable.allowGuestControl = True
    # nic_spec.device.connectable.connected = False
    # nic_spec.device.connectable.status = 'untried'
    # nic_spec.device.wakeOnLanEnabled = True
    # nic_spec.device.addressType = 'assigned'
    # device_changes.append(nic_spec)

    # Addig Network Device 1 - Standard Switch
    # nic_spec = vim.vm.device.VirtualDeviceSpec()
    # nic_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.add
    # nic_spec.device = vim.vm.device.VirtualVmxnet3()
    # nic_spec.device.deviceInfo = vim.Description()
    # #nic_spec.device.deviceInfo.summary = 'vCenter API test'
    # nic_spec.device.backing = \
    #     vim.vm.device.VirtualEthernetCard.NetworkBackingInfo()
    # nic_spec.device.backing.useAutoDetect = False
    # content = service_instance.RetrieveContent()
    # nic_spec.device.backing.network = get_obj(content, [vim.Network], network_pxe)
    # nic_spec.device.backing.deviceName = network_pxe
    # nic_spec.device.connectable = vim.vm.device.VirtualDevice.ConnectInfo()
    # nic_spec.device.connectable.startConnected = True
    # nic_spec.device.connectable.startConnected = True
    # nic_spec.device.connectable.allowGuestControl = True
    # nic_spec.device.connectable.connected = False
    # nic_spec.device.connectable.status = 'untried'
    # nic_spec.device.wakeOnLanEnabled = True
    # nic_spec.device.addressType = 'assigned'
    # device_changes.append(nic_spec)

    # # Addig Network Device 2 - Standard PG
    # nic_spec = vim.vm.device.VirtualDeviceSpec()
    # nic_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.add
    # nic_spec.device = vim.vm.device.VirtualVmxnet3()
    # nic_spec.device.deviceInfo = vim.Description()
    # #nic_spec.device.deviceInfo.summary = 'vCenter API test'
    # nic_spec.device.backing = \
    #     vim.vm.device.VirtualEthernetCard.NetworkBackingInfo()
    # nic_spec.device.backing.useAutoDetect = False
    # nic_spec.device.backing.network = get_obj(content, [vim.Network], network_pxe)
    # nic_spec.device.backing.deviceName = network_vm
    # nic_spec.device.connectable = vim.vm.device.VirtualDevice.ConnectInfo()
    # nic_spec.device.connectable.startConnected = True
    # nic_spec.device.connectable.startConnected = True
    # nic_spec.device.connectable.allowGuestControl = True
    # nic_spec.device.connectable.connected = False
    # nic_spec.device.connectable.status = 'untried'
    # nic_spec.device.wakeOnLanEnabled = True
    # nic_spec.device.addressType = 'assigned'
    # device_changes.append(nic_spec)

    # Add Disk controller
    iscsictrl = vim.vm.device.VirtualDeviceSpec()
    iscsictrl.operation = vim.vm.device.VirtualDeviceSpec.Operation.add
    iscsictrl.device = vim.vm.device.VirtualLsiLogicSASController()
    iscsictrl.device.sharedBus = vim.vm.device.VirtualSCSIController.Sharing.noSharing
    device_changes.append(iscsictrl)

    # Add Disk
    unit_number = 0
    # for dev in vm.config.hardware.device:
    #     if hasattr(dev.backing, 'fileName'):
    #         unit_number = int(dev.unitNumber) + 1
    #         # unit_number 7 reserved for scsi controller
    #         if unit_number == 7:
    #             unit_number += 1
    #         if unit_number >= 16:
    #             print "we don't support this many disks"
    #             return
    #     if isinstance(dev, vim.vm.device.VirtualSCSIController):
    #         controller = dev
    new_disk_kb = int(disk_size) * 1024 * 1024
    disk_spec = vim.vm.device.VirtualDeviceSpec()
    disk_spec.fileOperation = "create"
    disk_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.add
    disk_spec.device = vim.vm.device.VirtualDisk()
    disk_spec.device.backing = \
        vim.vm.device.VirtualDisk.FlatVer2BackingInfo()
    if disk_type == 'thin':
        disk_spec.device.backing.thinProvisioned = True
    disk_spec.device.backing.diskMode = 'persistent'
    disk_spec.device.unitNumber = unit_number
    disk_spec.device.capacityInKB = new_disk_kb
    disk_spec.device.controllerKey = 0
    device_changes.append(disk_spec)

    config = vim.vm.ConfigSpec(name=vm_name, memoryMB=memory, numCPUs=vcpu,
                               files=vmx_file, guestId=guestid,
                               version=vmxversion, deviceChange=device_changes,
                               nestedHVEnabled=True)

    print "Creating VM {}...".format(vm_name)
    task = vm_folder.CreateVM_Task(config=config, pool=resource_pool)
    tasks.wait_for_tasks(service_instance, [task])


def main():
    """
    Simple command-line program for creating Dummy VM based on Marvel character
    names
    """

    args = get_args()

    if args.disable_ssl_verification:
        service_instance = connect.SmartConnectNoSSL(host=args.host,
                                                     user=args.user,
                                                     pwd=args.password,
                                                     port=int(args.port))
    else:
        service_instance = connect.SmartConnect(host=args.host,
                                                user=args.user,
                                                pwd=args.password,
                                                port=int(args.port))

    if not service_instance:
        print("Could not connect to the specified host using specified "
              "username and password")
        return -1

    atexit.register(connect.Disconnect, service_instance)

    content = service_instance.RetrieveContent()
    datacenter = content.rootFolder.childEntity[0]
    vmfolder = get_obj(content, [vim.Folder], location)
    if vmfolder is None:
        vmfolder = datacenter.vmFolder

    hosts = datacenter.hostFolder.childEntity
    resource_pool = hosts[0].resourcePool
    name = args.name
    print "Creating -- ", name
    create_esxi_vm(name, service_instance, vmfolder, resource_pool,
                   args.datastore, args.memorymb, args.vcpunum,
                   args.network, args.guestid, args.vmxversion)
    return 0


# Start program
if __name__ == "__main__":
    main()
