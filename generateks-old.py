#!/usr/bin/env python
# VMware vSphere Python SDK
# Copyright (c) 2008-2015 VMware, Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Python program for listing the vms on an ESX / vCenter host
"""

from __future__ import print_function

from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vim

import argparse
import atexit
import getpass
import ssl


def GetArgs():
    """
    Supports the command-line arguments listed below.
    """
    parser = argparse.ArgumentParser(
        description='Process args for retrieving all the Virtual Machines')
    parser.add_argument('-s', '--host', required=True, action='store',
                        help='Remote host to connect to')
    parser.add_argument('-o', '--port', type=int, default=443, action='store',
                        help='Port to connect on')
    parser.add_argument('-u', '--user', required=True, action='store',
                        help='User name to use when connecting to host')
    parser.add_argument('-p', '--password', required=False, action='store',
                        help='Password to use when connecting to host')
    parser.add_argument('-n', '--vmname', required=True, action='store',
                        help='Name of the virtual machine')
    args = parser.parse_args()
    return args


def get_obj(content, vim_type, name):
    obj = None
    container = content.viewManager.CreateContainerView(
        content.rootFolder, vim_type, True)
    for c in container.view:
        if c.name == name:
            obj = c
            break
    return obj


def get_mac(si, vm, nic_number):
    """ Deletes virtual NIC based on nic number
    :param si: Service Instance
    :param vm: Virtual Machine Object
    :param nic_number: Unit Number
    :return: True if success
    """
    nic_prefix_label = 'Network adapter '
    nic_label = nic_prefix_label + str(nic_number)
    virtual_nic_device = None
    for dev in vm.config.hardware.device:
        # print(dev)
        if isinstance(dev, vim.vm.device.VirtualEthernetCard)   \
                and dev.deviceInfo.label == nic_label:
            virtual_nic_device = dev
        elif isinstance(dev, vim.vm.device.VirtualVmxnet3)   \
                and dev.deviceInfo.label == nic_label:
            virtual_nic_device = dev

    if virtual_nic_device:
        return virtual_nic_device.macAddress
    else:
        return False


def main():
    """
    Simple command-line program for listing the virtual machines on a system.
    """

    args = GetArgs()
    if args.password:
        password = args.password
    else:
        password = getpass.getpass(prompt='Enter password for host %s and '
                                          'user %s: ' % (args.host, args.user))

    context = None
    if hasattr(ssl, '_create_unverified_context'):
        context = ssl._create_unverified_context()
    si = SmartConnect(host=args.host,
                      user=args.user,
                      pwd=password,
                      port=int(args.port),
                      sslContext=context)
    if not si:
        print("Could not connect to the specified host using specified "
              "username and password")
        return -1

    atexit.register(Disconnect, si)
    vmname = args.vmname
    print("Searching fo VM - ", vmname)
    # Retreive the list of Virtual Machines from the inventory objects
    # under the rootFolder
    content = si.RetrieveContent()
    vm = get_obj(content, [vim.VirtualMachine], vmname)

    if vm:
        print("Found VM -- ", vm)
        vm_mac = get_mac(content, vm, 1)
        print("Network Adapter 1 - Mac is:", vm_mac)
    else:
        print("VM not found")

    return 0


# Start program
if __name__ == "__main__":
    main()
