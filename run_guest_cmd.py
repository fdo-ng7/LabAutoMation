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


def run_command_in_guest(content, vm, username, password, program_path, program_args, program_cwd, program_env):

    result = {'failed': False}

    tools_status = vm.guest.toolsStatus
    if (tools_status == 'toolsNotInstalled' or
            tools_status == 'toolsNotRunning'):
        result['failed'] = True
        result['msg'] = "VMwareTools is not installed or is not running in the guest"
        return result

    # https://github.com/vmware/pyvmomi/blob/master/docs/vim/vm/guest/NamePasswordAuthentication.rst
    creds = vim.vm.guest.NamePasswordAuthentication(
        username=username, password=password
    )

    try:
        # https://github.com/vmware/pyvmomi/blob/master/docs/vim/vm/guest/ProcessManager.rst
        pm = content.guestOperationsManager.processManager
        # https://www.vmware.com/support/developer/converter-sdk/conv51_apireference/vim.vm.guest.ProcessManager.ProgramSpec.html
        ps = vim.vm.guest.ProcessManager.ProgramSpec(
            # programPath=program,
            # arguments=args
            programPath=program_path,
            arguments=program_args,
            workingDirectory=program_cwd,
        )

        res = pm.StartProgramInGuest(vm, creds, ps)
        result['pid'] = res
        pdata = pm.ListProcessesInGuest(vm, creds, [res])

        # wait for pid to finish
        while not pdata[0].endTime:
            time.sleep(1)
            pdata = pm.ListProcessesInGuest(vm, creds, [res])

        result['owner'] = pdata[0].owner
        result['startTime'] = pdata[0].startTime.isoformat()
        result['endTime'] = pdata[0].endTime.isoformat()
        result['exitCode'] = pdata[0].exitCode
        if result['exitCode'] != 0:
            result['failed'] = True
            result['msg'] = "program exited non-zero"
        else:
            result['msg'] = "program completed successfully"

    except Exception as e:
        result['msg'] = str(e)
        result['failed'] = True

    return result


def open_url(url, data=None, headers=None, method=None, use_proxy=True,
             force=False, last_mod_time=None, timeout=10, validate_certs=True,
             url_username=None, url_password=None, http_agent=None,
             force_basic_auth=False, follow_redirects='urllib2'):
    '''
    Sends a request via HTTP(S) or FTP using urllib2 (Python2) or urllib (Python3)

    Does not require the module environment
    '''
    handlers = []
    ssl_handler = maybe_add_ssl_handler(url, validate_certs)
    if ssl_handler:
        handlers.append(ssl_handler)

    # FIXME: change the following to use the generic_urlparse function
    #        to remove the indexed references for 'parsed'
    parsed = urlparse(url)
    if parsed[0] != 'ftp':
        username = url_username

        if headers is None:
            headers = {}

        if username:
            password = url_password
            netloc = parsed[1]
        elif '@' in parsed[1]:
            credentials, netloc = parsed[1].split('@', 1)
            if ':' in credentials:
                username, password = credentials.split(':', 1)
            else:
                username = credentials
                password = ''

            parsed = list(parsed)
            parsed[1] = netloc

            # reconstruct url without credentials
            url = urlunparse(parsed)

        if username and not force_basic_auth:
            passman = urllib_request.HTTPPasswordMgrWithDefaultRealm()

            # this creates a password manager
            passman.add_password(None, netloc, username, password)

            # because we have put None at the start it will always
            # use this username/password combination for  urls
            # for which `theurl` is a super-url
            authhandler = urllib_request.HTTPBasicAuthHandler(passman)
            digest_authhandler = urllib_request.HTTPDigestAuthHandler(passman)

            # create the AuthHandler
            handlers.append(authhandler)
            handlers.append(digest_authhandler)

        elif username and force_basic_auth:
            headers["Authorization"] = basic_auth_header(username, password)

        else:
            try:
                rc = netrc.netrc(os.environ.get('NETRC'))
                login = rc.authenticators(parsed[1])
            except IOError:
                login = None

            if login:
                username, _, password = login
                if username and password:
                    headers["Authorization"] = basic_auth_header(username, password)

    if not use_proxy:
        proxyhandler = urllib_request.ProxyHandler({})
        handlers.append(proxyhandler)

    if HAS_SSLCONTEXT and not validate_certs:
        # In 2.7.9, the default context validates certificates
        context = SSLContext(ssl.PROTOCOL_SSLv23)
        context.options |= ssl.OP_NO_SSLv2
        context.options |= ssl.OP_NO_SSLv3
        context.verify_mode = ssl.CERT_NONE
        context.check_hostname = False
        handlers.append(urllib_request.HTTPSHandler(context=context))

    # pre-2.6 versions of python cannot use the custom https
    # handler, since the socket class is lacking create_connection.
    # Some python builds lack HTTPS support.
    if hasattr(socket, 'create_connection') and CustomHTTPSHandler:
        handlers.append(CustomHTTPSHandler)

    handlers.append(RedirectHandlerFactory(follow_redirects, validate_certs))

    opener = urllib_request.build_opener(*handlers)
    urllib_request.install_opener(opener)

    data = to_bytes(data, nonstring='passthru')
    if method:
        if method.upper() not in ('OPTIONS', 'GET', 'HEAD', 'POST', 'PUT', 'DELETE', 'TRACE', 'CONNECT', 'PATCH'):
            raise ConnectionError('invalid HTTP request method; %s' % method.upper())
        request = RequestWithMethod(url, method.upper(), data)
    else:
        request = urllib_request.Request(url, data)

    # add the custom agent header, to help prevent issues
    # with sites that block the default urllib agent string
    if http_agent:
        request.add_header('User-agent', http_agent)

    # Cache control
    # Either we directly force a cache refresh
    if force:
        request.add_header('cache-control', 'no-cache')
    # or we do it if the original is more recent than our copy
    elif last_mod_time:
        tstamp = last_mod_time.strftime('%a, %d %b %Y %H:%M:%S +0000')
        request.add_header('If-Modified-Since', tstamp)

    # user defined headers now, which may override things we've set above
    if headers:
        if not isinstance(headers, dict):
            raise ValueError("headers provided to fetch_url() must be a dict")
        for header in headers:
            request.add_header(header, headers[header])

    urlopen_args = [request, None]
    if sys.version_info >= (2, 6, 0):
        # urlopen in python prior to 2.6.0 did not
        # have a timeout parameter
        urlopen_args.append(timeout)

    r = urllib_request.urlopen(*urlopen_args)
    return r

#
# Module-related functions
#


def fetch_url(module, url, data=None, headers=None, method=None,
              use_proxy=True, force=False, last_mod_time=None, timeout=10):
    '''Sends a request via HTTP(S) or FTP (needs the module as parameter)

    :arg module: The AnsibleModule (used to get username, password etc. (s.b.).
    :arg url:             The url to use.

    :kwarg data:          The data to be sent (in case of POST/PUT).
    :kwarg headers:       A dict with the request headers.
    :kwarg method:        "POST", "PUT", etc.
    :kwarg boolean use_proxy:     Default: True
    :kwarg boolean force: If True: Do not get a cached copy (Default: False)
    :kwarg last_mod_time: Default: None
    :kwarg int timeout:   Default: 10

    :returns: A tuple of (**response**, **info**). Use ``response.body()`` to read the data.
        The **info** contains the 'status' and other meta data. When a HttpError (status > 400)
        occurred then ``info['body']`` contains the error response data::

    Example::

        data={...}
        resp, info = fetch_url("http://example.com",
                               data=module.jsonify(data)
                               header={Content-type': 'application/json'},
                               method="POST")
        status_code = info["status"]
        body = resp.read()
        if status_code >= 400 :
            body = info['body']
'''

    if not HAS_URLPARSE:
        module.fail_json(msg='urlparse is not installed')

    # Get validate_certs from the module params
    validate_certs = module.params.get('validate_certs', True)

    username = module.params.get('url_username', '')
    password = module.params.get('url_password', '')
    http_agent = module.params.get('http_agent', None)
    force_basic_auth = module.params.get('force_basic_auth', '')

    follow_redirects = module.params.get('follow_redirects', 'urllib2')

    r = None
    info = dict(url=url)
    try:
        r = open_url(url, data=data, headers=headers, method=method,
                     use_proxy=use_proxy, force=force, last_mod_time=last_mod_time, timeout=timeout,
                     validate_certs=validate_certs, url_username=username,
                     url_password=password, http_agent=http_agent, force_basic_auth=force_basic_auth,
                     follow_redirects=follow_redirects)
        info.update(r.info())
        info.update(dict(msg="OK (%s bytes)" % r.headers.get(
            'Content-Length', 'unknown'), url=r.geturl(), status=r.code))
    except NoSSLError:
        e = get_exception()
        distribution = get_distribution()
        if distribution is not None and distribution.lower() == 'redhat':
            module.fail_json(msg='%s. You can also install python-ssl from EPEL' % str(e))
        else:
            module.fail_json(msg='%s' % str(e))
    except (ConnectionError, ValueError):
        e = get_exception()
        module.fail_json(msg=str(e))
    except urllib_error.HTTPError:
        e = get_exception()
        try:
            body = e.read()
        except AttributeError:
            body = ''
        info.update(dict(msg=str(e), body=body, **e.info()))
        info['status'] = e.code
    except urllib_error.URLError:
        e = get_exception()
        code = int(getattr(e, 'code', -1))
        info.update(dict(msg="Request failed: %s" % str(e), status=code))
    except socket.error:
        e = get_exception()
        info.update(dict(msg="Connection failure: %s" % str(e), status=-1))
    except Exception:
        e = get_exception()
        info.update(dict(msg="An unknown error occurred: %s" % str(e), status=-1))

    return r, info


def fetch_file_from_guest(content, vm, username, password, src, dest):
    """ Use VMWare's filemanager api to fetch a file over http """
    print "Inside fetch_file_from_guest"
    result = {'failed': False}

    tools_status = vm.guest.toolsStatus
    if tools_status == 'toolsNotInstalled' or tools_status == 'toolsNotRunning':
        result['failed'] = True
        result['msg'] = "VMwareTools is not installed or is not running in the guest"
        return result

    # https://github.com/vmware/pyvmomi/blob/master/docs/vim/vm/guest/NamePasswordAuthentication.rst
    creds = vim.vm.guest.NamePasswordAuthentication(
        username=username, password=password
    )

    # https://github.com/vmware/pyvmomi/blob/master/docs/vim/vm/guest/FileManager/FileTransferInformation.rst
    fti = content.guestOperationsManager.fileManager. \
        InitiateFileTransferFromGuest(vm, creds, src)

    result['size'] = fti.size
    result['url'] = fti.url

    # Use module_utils to fetch the remote url returned from the api
    rsp, info = fetch_url(self.module, fti.url, use_proxy=False,
                          force=True, last_mod_time=None,
                          timeout=10, headers=None)

    # save all of the transfer data
    for k, v in iteritems(info):
        result[k] = v

    # exit early if xfer failed
    if info['status'] != 200:
        result['failed'] = True
        return result

    # attempt to read the content and write it
    try:
        with open(dest, 'wb') as f:
            f.write(rsp.read())
    except Exception as e:
        result['failed'] = True
        result['msg'] = str(e)

    return result


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
    # foldername = basename
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

    # Testing upload file script
    # Teested Working
    iscsivm = "iscstore01"
    downloadfile_file = "c:\\testfile.txt"
    dest_path = "testfile234.txt"
    uuid = None
    # upload_file_to_vm(content, iscsivm, uuid, upload_file, vm_path)

    # def fetch_file_from_guest(self, vm, username, password, src, dest):
    # fetch_file_from_guest()

    # This sectiona manually defined how to updlad a file to VM
    # Test Uploading file to ISCSI server
    print "030 - Excute Command from Guest"
    iscsivm = "iscstore01"
    uuid = "564d57ad-b834-1a1b-e6b7-300fce0061b6"
    uuid = ""
    vm = None
    if uuid:
        print "Searching vm via uuid =", uuid
        search_index = content.searchIndex
        vm = search_index.FindByUuid(None, uuid, True)
        print vm
    elif iscsivm:
        # content = si.RetrieveContent()
        vm = get_obj(content, [vim.VirtualMachine], iscsivm)

    print vm
    username = "administrator"
    password = "Passw0rd!"
    program_path = 'c:\Windows\System32\WindowsPowerShell\\v1.0\powershell.exe'
    #"remove-item c:\\testfile.txt -force"
    program_args = "New-Item -ItemType Directory c:\\Temp1  -force; " + \
        "New-Item -ItemType Directory c:\Temp2\ -force; " + \
        "Remove-Item C:\Temp2 -force"

    program_cwd = None
    program_env = None
    run_command_in_guest(content, vm, username, password, program_path,
                         program_args, program_cwd, program_env)


    # Start program
if __name__ == "__main__":
    main()
