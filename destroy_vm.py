#!/usr/bin/env python
# Copyright 2015 Michael Rice <michael@michaelrice.org>
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

from __future__ import print_function

import atexit

from pyVim import connect

from pyVmomi import vim

from tools import cli
from tools import tasks


def setup_args():
    """Adds additional ARGS to allow the vm name or uuid to
    be set.
    """
    parser = cli.build_arg_parser()
    # using j here because -u is used for user
    parser.add_argument('-j', '--uuid',
                        help='BIOS UUID of the VirtualMachine you want '
                             'to destroy.')
    parser.add_argument('-n', '--name',
                        help='DNS Name of the VirtualMachine you want to '
                             'destroy.')
    parser.add_argument('-i', '--ip',
                        help='IP Address of the VirtualMachine you want to '
                             'destroy')
    parser.add_argument('-v', '--vm',
                        help='VM name of the VirtualMachine you want '
                             'to destroy.')

    my_args = parser.parse_args()

    return cli.prompt_for_password(my_args)


def get_obj(content, vimtype, name):
    """Create contrainer view and search for object in it"""
    obj = None
    container = content.viewManager.CreateContainerView(
        content.rootFolder, vimtype, True)
    for c in container.view:
        if name:
            if c.name == name:
                obj = c
                break
        else:
            obj = c
            break

    container.Destroy()
    return obj


def main():

    args = setup_args()

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

    vm = get_obj(content, [vim.VirtualMachine], args.vm)

    if vm is None:
        raise SystemExit(
            "Unable to locate VirtualMachine. Arguments given: "
            "vm - {0} , uuid - {1} , name - {2} , ip - {3}"
            .format(args.vm, args.uuid, args.name, args.ip)
        )

    print("Found: {0}".format(vm.name))
    print("The current powerState is: {0}".format(vm.runtime.powerState))
    if format(vm.runtime.powerState) == "poweredOn":
        print("Attempting to power off {0}".format(vm.name))
        TASK = vm.PowerOffVM_Task()
        tasks.wait_for_tasks(service_instance, [TASK])
        print("{0}".format(TASK.info.state))

    print("Destroying VM from vSphere.")
    TASK = vm.Destroy_Task()
    tasks.wait_for_tasks(service_instance, [TASK])
    print("Done.")

    return 0


# Start program
if __name__ == "__main__":
    main()
