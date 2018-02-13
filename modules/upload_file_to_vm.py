
import requests
from pyVmomi import vim


def get_obj(content, vimtype, name):
    obj = None
    container = content.viewManager.CreateContainerView(
        content.rootFolder, vimtype, True)
    for c in container.view:
        if c.name == name:
            obj = c
            break
    return obj


# Script to upload file to vm
# Parameters required: si_content, vm_name or uuid, source file path,
# destination file path


def upload_file_to_vm(content, vm_name, uuid, src_file, dest_path):
    # Test Uploading file to ISCSI server
    # iscsivm = "iscstore01"
    # uuid = "564d57ad-b834-1a1b-e6b7-300fce0061b6"
    # uuid = ""
    vm = None
    if uuid:
        print "Searching vm via uuid =", uuid
        search_index = content.searchIndex
        vm = search_index.FindByUuid(None, uuid, True)
        print vm
    elif vm_name:
        # content = si.RetrieveContent()
        vm = get_obj(content, [vim.VirtualMachine], vm_name)

    print vm

    tools_status = vm.guest.toolsStatus
    if (tools_status == 'toolsNotInstalled' or
            tools_status == 'toolsNotRunning'):
        raise SystemExit(
            "VMwareTools is either not running or not installed. "
            "Rerun the script after verifying that VMWareTools "
            "is running")

    # upload_file = "testfile.txt"
    upload_file = src_file
    # guestpath = "c:\\testfile.txt"
    guestpath = dest_path
    creds = vim.vm.guest.NamePasswordAuthentication(
        username="administrator", password="Passw0rd!")
    with open(upload_file, 'rb') as myfile:
        args = myfile.read()

    print upload_file
    print guestpath
    print "arrgs - ", args

    try:
        file_attribute = vim.vm.guest.FileManager.FileAttributes()
        url = content.guestOperationsManager.fileManager. \
            InitiateFileTransferToGuest(vm, creds, guestpath,
                                        file_attribute,
                                        len(args), True)
        # When : host argument becomes https://*:443/guestFile?
        # Ref: https://github.com/vmware/pyvmomi/blob/master/docs/ \
        #            vim/vm/guest/FileManager.rst
        # Script fails in that case, saying URL has an invalid label.
        # By having hostname in place will take take care of this.
        import re
        url = re.sub(r"^https://\*:", "https://*:", url)

        # str = "https://" + vc_ip
        # url = re.sub(r"^http[s]?:\/\/(?:[0-9]|[.])+", str, url)
        #url = re.sub(r"^http[s]?:\/\/(?:[0-9]|[.])+", "https://*", url)
        print "url -- ", url
        resp = requests.put(url, data=args, verify=False)
        if not resp.status_code == 200:
            print "Error while uploading file"
        else:
            print "Successfully uploaded file"
    except IOError, e:
        print e


def invoke_vmscript(content, vm_username, vm_password, vm_name, script_content, wait_for_output=False):

    script_content_crlf = script_content.replace('\n', '\r\n')
    import logging
    # create logger
    logger = logging.getLogger('simple_example')
    logger.setLevel(logging.DEBUG)

    #content = self.si.content
    creds = vim.vm.guest.NamePasswordAuthentication(username=vm_username, password=vm_password)
    vm = get_obj(content, [vim.VirtualMachine], vm_name)
    logger.debug("Invoke-VMScript Started for %s", vm_name)
    logger.debug("CREATING TEMP OUTPUT DIR")
    file_manager = content.guestOperationsManager.fileManager

    temp_dir = file_manager.CreateTemporaryDirectoryInGuest(vm, creds, "nodebldr_",
                                                            "_scripts")
    print "Tempdir - ", temp_dir
    try:
        file_manager.MakeDirectoryInGuest(vm, creds, temp_dir, False)
    except vim.fault.FileAlreadyExists:
        pass
    temp_script_file = file_manager.CreateTemporaryFileInGuest(vm, creds, "nodebldr_",
                                                               "_script.ps1",
                                                               temp_dir)
    temp_output_file = file_manager.CreateTemporaryFileInGuest(vm, creds, "nodebldr_",
                                                               "_output.txt",
                                                               temp_dir)
    logger.debug("SCRIPT FILE: " + temp_script_file)
    logger.debug("OUTPUT FILE: " + temp_output_file)
    file_attribute = vim.vm.guest.FileManager.FileAttributes()
    url = file_manager.InitiateFileTransferToGuest(vm, creds, temp_script_file,
                                                   file_attribute,
                                                   len(script_content_crlf), True)
    logger.debug("UPLOAD SCRIPT TO: " + url)
    r = requests.put(url, data=script_content_crlf, verify=False)
    if not r.status_code == 200:
        #logger.debug("Error while uploading file")
        print "Error while uploading file"
    else:
        #logger.debug("Successfully uploaded file")
        print "Successfully uploaded file"
    self.remote_cmd(vm_name, vm_username, vm_password, 'C:\\WINDOWS\\system32\\WindowsPowerShell\\v1.0\\powershell.exe',
                    "-Noninteractive {0} > {1}".format(temp_script_file,
                                                       temp_output_file), temp_dir,
                    wait_for_end=wait_for_output)

    output = None
    if wait_for_output:
        dl_url = file_manager.InitiateFileTransferFromGuest(vm, creds,
                                                            temp_output_file)
        logger.debug("DOWNLOAD OUTPUT FROM: " + dl_url.url)
        r = requests.get(dl_url.url, verify=False)
        output = r.text
        logger.debug("Script Output was: %s", output)

    logger.debug("DELETING temp files & directory")
    file_manager.DeleteFileInGuest(vm, creds, temp_script_file)
    file_manager.DeleteFileInGuest(vm, creds, temp_output_file)
    file_manager.DeleteDirectoryInGuest(vm, creds, temp_dir, True)
    logger.debug("Invoke-VMScript COMPLETE")

    return output
