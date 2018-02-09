#!/usr/bin/env python
"""
    vm_nic.py - module for NIC Device info

"""


def get_obj(content, vim_type, name):
    obj = None
    container = content.viewManager.CreateContainerView(
        content.rootFolder, vim_type, True)
    for c in container.view:
        if c.name == name:
            obj = c
            break
    return obj

# returns the mac address of vm


def get_vm_macaddr(content, vm_obj, nic_number):
    """
    :param si: Service Instance
    :param vm_obj: Virtual Machine Object
    :param nic_number: Network Interface Controller Number
        "Network adapter 1 or Network adapter 2"
    :return: MAC if success
    """

    nic_prefix_label = 'Network adapter '
    nic_label = nic_prefix_label + str(nic_number)
    virtual_nic_device = None

    for dev in vm_obj.config.hardware.device:
        if dev.deviceInfo.label == nic_label:
            virtual_nic_device = dev
            # print nic_label
            return virtual_nic_device.macAddress

    if virtual_nic_device is None:
        return 0
