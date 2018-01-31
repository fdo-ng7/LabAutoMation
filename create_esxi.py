#!/usr/bin/env python
# William lam
# www.virtuallyghetto.com

"""
vSphere SDK for Python program for creating tiny VMs (1vCPU/128MB) with random
names using the Marvel Comics API
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

    parser.add_argument('-c', '--count',
                        type=int,
                        required=True,
                        action='store',
                        help='Number of VMs to create')

    parser.add_argument('-d', '--datastore',
                        required=True,
                        action='store',
                        help='Name of Datastore to create VM in')

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


def get_marvel_characters(number_of_characters, marvel_public_key,
                          marvel_private_key):
    """Makes an API call to the Marvel Comics developer API
        to get a list of character names.

    :param number_of_characters: int Number of characters to fetch.
    :param marvel_public_key: String Public API key from Marvel
    :param marvel_private_key: String Private API key from Marvel
    :rtype list: Containing names of characters
    """
    timestamp = str(int(time.time()))
    # hash is required as part of request which is
    # md5(timestamp + private + public key)
    hash_value = hashlib.md5(timestamp + marvel_private_key +
                             marvel_public_key).hexdigest()

    characters = []
    for _num in xrange(number_of_characters):
        # randomly select one of the 1478 Marvel characters
        offset = random.randrange(1, 1478)
        limit = '1'

        # GET /v1/public/characters
        url = ('http://gateway.marvel.com:80/v1/public/characters?limit=' +
               limit + '&offset=' + str(offset) + '&apikey=' +
               marvel_public_key + '&ts=' + timestamp + '&hash=' + hash_value)

        headers = {'content-type': 'application/json'}
        request = requests.get(url, headers=headers)
        data = json.loads(request.content)
        if data.get('code') == 'InvalidCredentials':
            raise RuntimeError('Your Marvel API keys do not work!')

        # retrieve character name & replace spaces with underscore so we don't
        # have spaces in our VM names
        character = data['data']['results'][0]['name'].strip().replace(' ',
                                                                       '_')
        characters.append(character)
    return characters


def create_dummy_vm(name, service_instance, vm_folder, resource_pool,
                    datastore):
    """Creates a dummy VirtualMachine with 1 vCpu, 128MB of RAM.

    :param name: String Name for the VirtualMachine
    :param service_instance: ServiceInstance connection
    :param vm_folder: Folder to place the VirtualMachine in
    :param resource_pool: ResourcePool to place the VirtualMachine in
    :param datastore: DataStrore to place the VirtualMachine on
    """
    vm_name = 'MARVEL-' + name
    datastore_path = '[' + datastore + '] ' + vm_name

    # bare minimum VM shell, no disks. Feel free to edit
    vmx_file = vim.vm.FileInfo(logDirectory=None,
                               snapshotDirectory=None,
                               suspendDirectory=None,
                               vmPathName=datastore_path)

    config = vim.vm.ConfigSpec(name=vm_name, memoryMB=128, numCPUs=1,
                               files=vmx_file, guestId='vmkernel6Guest',
                               version='vmx-11')

    print "Creating VM {}...".format(vm_name)
    task = vm_folder.CreateVM_Task(config=config, pool=resource_pool)
    tasks.wait_for_tasks(service_instance, [task])

# port_find and search_port script required to find VDS PG


def port_find(dvs, key):
    obj = None
    ports = dvs.FetchDVPorts()
    for c in ports:
        if c.key == key:
            obj = c
    return obj


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


def create_esxi_vm(name, service_instance, vm_folder, resource_pool,
                   datastore):
    """Creates a dummy VirtualMachine with 1 vCpu, 128MB of RAM.

    :param name: String Name for the VirtualMachine
    :param service_instance: ServiceInstance connection
    :param vm_folder: Folder to place the VirtualMachine in
    :param resource_pool: ResourcePool to place the VirtualMachine in
    :param datastore: DataStrore to place the VirtualMachine on
    """
    network_pxe = "pxe"
    network_vm = "MGMT"
    nic_type = "VMXNET3"
    vm_name = 'MARVEL-' + name
    disk_size = 8
    disk_type = "thin"
    datastore_path = '[' + datastore + '] ' + vm_name

    content = service_instance.RetrieveContent()
    # bare minimum VM shell, no disks. Feel free to edit
    vmx_file = vim.vm.FileInfo(logDirectory=None,
                               snapshotDirectory=None,
                               suspendDirectory=None,
                               vmPathName=datastore_path)

    device_changes = []
    # Addig Network Device 1 - VDS SWitch
    # Gather PG and VDS info
    portgroup = None
    portgroup = get_obj(content,
                        [vim.dvs.DistributedVirtualPortgroup], network_pxe)
    if portgroup is None:
        print("Portgroup not Found in DVS ...")
        exit(0)
    dvs = portgroup.config.distributedVirtualSwitch
    portKey = search_port(dvs, portgroup.key)
    port = port_find(dvs, portKey)
    nic_spec = vim.vm.device.VirtualDeviceSpec()
    nic_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.add
    nic_spec.device = vim.vm.device.VirtualVmxnet3()
    nic_spec.device.deviceInfo = vim.Description()
    nic_spec.device.backing = \
        vim.vm.device.VirtualEthernetCard.DistributedVirtualPortBackingInfo()
    nic_spec.device.backing.port = vim.dvs.PortConnection()
    nic_spec.device.backing.port.portgroupKey = port.portgroupKey
    nic_spec.device.backing.port.switchUuid = port.dvsUuid
    nic_spec.device.backing.port.portKey = port.key
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
    portgroup = None
    portgroup = get_obj(content,
                        [vim.dvs.DistributedVirtualPortgroup], network_vm)
    if portgroup is None:
        print("Portgroup not Found in DVS ...")
        exit(0)
    dvs = portgroup.config.distributedVirtualSwitch
    portKey = search_port(dvs, portgroup.key)
    port = port_find(dvs, portKey)
    nic_spec = vim.vm.device.VirtualDeviceSpec()
    nic_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.add
    nic_spec.device = vim.vm.device.VirtualVmxnet3()
    nic_spec.device.deviceInfo = vim.Description()
    nic_spec.device.backing = \
        vim.vm.device.VirtualEthernetCard.DistributedVirtualPortBackingInfo()
    nic_spec.device.backing.port = vim.dvs.PortConnection()
    nic_spec.device.backing.port.portgroupKey = port.portgroupKey
    nic_spec.device.backing.port.switchUuid = port.dvsUuid
    nic_spec.device.backing.port.portKey = port.key
    nic_spec.device.connectable = vim.vm.device.VirtualDevice.ConnectInfo()
    nic_spec.device.connectable.startConnected = True
    nic_spec.device.connectable.allowGuestControl = True
    nic_spec.device.connectable.connected = False
    nic_spec.device.connectable.status = 'untried'
    nic_spec.device.wakeOnLanEnabled = True
    nic_spec.device.addressType = 'assigned'
    device_changes.append(nic_spec)

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

    config = vim.vm.ConfigSpec(name=vm_name, memoryMB=128, numCPUs=1,
                               files=vmx_file, guestId='vmkernel6Guest',
                               version='vmx-11', deviceChange=device_changes,
                               nestedHVEnabled=True)

    print "Creating VM {}...".format(vm_name)
    task = vm_folder.CreateVM_Task(config=config, pool=resource_pool)
    tasks.wait_for_tasks(service_instance, [task])


def add_controller(vm):
    vm.ReconfigVM_Task(
        spec=vim.vm.ConfigSpec(
            deviceChange=[
                vim.vm.device.VirtualDeviceSpec(
                    operation=vim.vm.device.VirtualDeviceSpec.Operation.add,
                    device=vim.vm.device.VirtualLsiLogicSASController(
                        sharedBus=vim.vm.device.VirtualSCSIController.Sharing.noSharing
                    ),
                )
            ]
        )
    )


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
    vmfolder = datacenter.vmFolder
    hosts = datacenter.hostFolder.childEntity
    resource_pool = hosts[0].resourcePool

    characters = "esx01", "esx02"

    for name in characters:
        # create_dummy_vm(name, service_instance, vmfolder, resource_pool,
        #                 args.datastore)
        create_esxi_vm(name, service_instance, vmfolder, resource_pool,
                       args.datastore)
        print "Creating -- ", name
    return 0


# Start program
if __name__ == "__main__":
    main()
