#!/usr/bin/env python
"""
Script to Generate the KS Script
Required parameters:
    path = "./KS/"
    esx_version = "ESXi6.0u2"
    esx_version = "ESXi5.5u2"
    macaddr = "00:50:56:90:eb:e1"
    vlan = ""
    ipaddr = "10.10.10.12"
    gateway = "10.10.10.1"
    nameserver = "8.8.8.8"
    netmask = "255.255.255.0"
    esxhostname = "testesx01.ashlab.ops"
    rootpw = "VMWware01!"
    iscsitarget = "10.10.10.200"
Updates:
    02/09/2018 Convert into Module
        - added function generate_ks()
        - function returns list with 3 file to be used for upload

"""
import fileinput
# Main Body

# Generate KS Files and return file_list containing 3 files


def generate_ks(macaddr, esx_version, vlan, ipaddr, gateway, nameserver,
                netmask, esxhostname, rootpw, iscsitarget):

    # Path were all KS files located
    path = "./KS/"
    # files to be uploaded
    file_list = []

    macaddr = macaddr.replace(":", "-")

    # defining output file path and name
    outks = path + "outfile/01-" + macaddr + ".cfg"
    outmnu = path + "outfile/01-" + macaddr
    outboot = path + "outfile/01-" + macaddr + "boot.cfg"

    if esx_version == "ESXi5.5u2":
        mnupath = path + "tmplmnu_uni"
        kspath = path + "ks_cfg_v1"
        bootpath = path + "boot_cfg_ESXi5.5u2"
        ESXTITLE = "ESXi-5.5.2-2068190-full"
    elif esx_version == "ESXi6.0u2":
        mnupath = path + "tmplmnu_uni"
        kspath = path + "ks_cfg_v1"
        bootpath = path + "boot_cfg_ESXi6.0u2"
        ESXTITLE = "ESXi-6.0.2-3620759-full"

    print " ESXi Version Selected - ", esx_version
    print " - kspath set to -- ", kspath
    print " - mnupath set to -- ", mnupath
    print " - bootpath set to -- ", bootpath

    # Adding VLAN
    if (vlan is None or vlan == ""):
        newstring1 = "--bootproto=static --device=vmnic0 --ip=" + ipaddr + \
            " --gateway=" + gateway + " --nameserver=" + \
            nameserver + " --netmask=" + netmask + \
            " --hostname=" + esxhostname + " --addvmportgroup=1 \n"
        newstring2 = "VLANID=\"0\"\n"
    else:
        newstring1 = "--bootproto=static --device=vmnic0 --ip=" + ipaddr + \
            " --gateway=" + gateway + " --nameserver=" + \
            nameserver + " --netmask=" + netmask + \
            " --hostname=" + esxhostname + " --addvmportgroup=1 --vlanid=" + \
            vlan + "\n"
        newstring2 = "VLANID=\"" + vlan + "\"\n"

    # Part 1 - Generate KickStart Configuration File
    fr = open(kspath, "r")
    outfile = open(outks, 'w')

    for line in fr:
        # if line.strip() == 'replacethislinewithcorrectvalues':
        if line.strip().find('replacethislinewithcorrectvalues') != -1:
            # print line.strip().replace('replacethislinewithcorrectvalues', newstring)
            outfile.write(line.strip().replace(
                'replacethislinewithcorrectvalues', newstring1))
        elif line.strip().find('VLANID=\"\"') != -1:
            outfile.write(line.strip().replace(
                'VLANID=\"\"', newstring2))
        elif line.strip().find('ISCSITG=\"\"') != -1:
            outfile.write(line.strip().replace(
                'ISCSITG=\"\"', "ISCSITG=\"" + iscsitarget + "\"\n"))
        elif line.strip().find('mypassword') != -1:
            outfile.write(line.strip().replace(
                'mypassword', rootpw))
        else:
            outfile.write(line)
    fr.close()
    outfile.close()

    # Use fileinput to do inplace text replacement for ESXi5.5u2
    # add vibs to install process, vmtools and patch
    if esx_version == "ESXi5.5u2":
        newstr = "esxcli software vib install --viburl=http://10.158.81.38/KS/repo/ESXi550-201505002.zip\n" + \
            "esxcli software vib install --viburl=http://10.158.81.38/KS/repo/esx-tools-for-esxi-9.7.2-0.0.5911061.i386.vib\n"
        # print "Replacing VIBINSTALL STRING--\n" + newstr
        # print '##VIBINSTALLSTRING'
        for line in fileinput.input(outks, inplace=True):
            print line.strip().replace('##VIBINSTALLSTRING', newstr)

    print "KS.CFG file -- ", outks
    file_list.append(outks)

    # Part 2 - Generate MNU file
    # Ouput file - outmnu
    fr = open(mnupath, "r")
    outfile = open(outmnu, 'w')

    for line in fr:
        # if line.strip() == 'replacethislinewithcorrectvalues':
        if line.strip().find('REPLACETHISLINE') != -1:
            newstr = "-c /pxelinux.cfg/boot/01-" + macaddr + \
                "boot.cfg ks=http://10.10.10.5/KS/01-" + macaddr + ".cfg +++"
            outfile.write(line.replace(
                'REPLACETHISLINE', newstr))
        elif line.strip().find('ESXVERSION') != -1:
            outfile.write(line.replace(
                'ESXVERSION', esx_version))
        elif line.strip().find('REPLACEWTITLE') != -1:
            outfile.write(line.replace(
                'REPLACEWTITLE', ESXTITLE))
        else:
            outfile.write(line)
    fr.close()
    outfile.close()

    print "MNU file created -- ", outmnu
    file_list.append(outmnu)

    # Part 3 - create Boot.CFG files
    fr = open(bootpath, "r")
    outfile = open(outboot, 'w')

    for line in fr:
        # if line.strip() == 'replacethislinewithcorrectvalues':
        if line.strip().find('runweasel') != -1:
            newstr = "http://10.10.10.5/KS/01-" + macaddr + ".cfg"
            outfile.write(line.replace(
                'runweasel', newstr))
        elif line.strip().find('ESXVERSION') != -1:
            outfile.write(line.replace(
                'ESXVERSION', esx_version))
        else:
            outfile.write(line)
    fr.close()
    outfile.close()
    print "BootCFG file created -- ", outboot
    file_list.append(outboot)

    print file_list
    # print "Transfering Files to: "
    # import os
    # os.system("scp " + outks + " root@10.159.81.200:/tmp/")
    return file_list


def main():
    # Parameters required
    path = "./KS/"
    esx_version = "ESXi6.0u2"
    esx_version = "ESXi5.5u2"
    macaddr = "00:50:56:90:eb:e1"
    vlan = ""
    ipaddr = "10.10.10.12"
    gateway = "10.10.10.1"
    nameserver = "8.8.8.8"
    netmask = "255.255.255.0"
    esxhostname = "testesx01.ashlab.ops"
    rootpw = "VMWware01!"
    iscsitarget = "10.10.10.200"

    macaddr = macaddr.replace(":", "-")
    outks = path + "outfile/01-" + macaddr + ".cfg"
    outmnu = path + "outfile/01-" + macaddr
    outboot = path + "outfile/01-" + macaddr + "boot.cfg"
    # Part one KickStart Script
    # file = open("./KS/ks_cfg_v1", "r")
    # print(file.read())
    # file.close()

    if esx_version == "ESXi5.5u2":
        mnupath = path + "tmplmnu_uni"
        kspath = path + "ks_cfg_v1"
        bootpath = path + "boot_cfg_ESXi5.5u2"
        ESXTITLE = "ESXi-5.5.2-2068190-full"
    elif esx_version == "ESXi6.0u2":
        mnupath = path + "tmplmnu_uni"
        kspath = path + "ks_cfg_v1"
        bootpath = path + "boot_cfg_ESXi6.0u2"
        ESXTITLE = "ESXi-6.0.2-3620759-full"

    print " ESXi Version Selected - ", esx_version
    print " - kspath set to -- ", kspath
    print " - mnupath set to -- ", mnupath
    print " - bootpath set to -- ", bootpath

    print "Generating Config files for MAC ", macaddr

    # vlan
    if (vlan is None or vlan == ""):
        newstring1 = "--bootproto=static --device=vmnic0 --ip=" + ipaddr + \
            " --gateway=" + gateway + " --nameserver=" + \
            nameserver + " --netmask=" + netmask + \
            " --hostname=" + esxhostname + " --addvmportgroup=1 \n"
        newstring2 = "VLANID=\"0\"\n"
    else:
        newstring1 = "--bootproto=static --device=vmnic0 --ip=" + ipaddr + \
            " --gateway=" + gateway + " --nameserver=" + \
            nameserver + " --netmask=" + netmask + \
            " --hostname=" + esxhostname + " --addvmportgroup=1 --vlanid=" + \
            vlan + "\n"
        newstring2 = "VLANID=\"" + vlan + "\"\n"
    # print newstring

    # This method works but have to open and close file everytime
    # with open(kspath, 'r') as input_file, open(outks, 'w') as output_file:
    #     for line in input_file:
    #         # if line.strip() == 'replacethislinewithcorrectvalues':
    #         if line.strip().find('replacethislinewithcorrectvalues') != -1:
    #             # print line.strip().replace('replacethislinewithcorrectvalues', newstring)
    #             output_file.write(line.strip().replace(
    #                 'replacethislinewithcorrectvalues', newstring))
    #         else:
    #             output_file.write(line)

    # Part 1 - Generate KickStart Configuration File
    fr = open(kspath, "r")
    outfile = open(outks, 'w')

    for line in fr:
        # if line.strip() == 'replacethislinewithcorrectvalues':
        if line.strip().find('replacethislinewithcorrectvalues') != -1:
            # print line.strip().replace('replacethislinewithcorrectvalues', newstring)
            outfile.write(line.strip().replace(
                'replacethislinewithcorrectvalues', newstring1))
        elif line.strip().find('VLANID=\"\"') != -1:
            outfile.write(line.strip().replace(
                'VLANID=\"\"', newstring2))
        elif line.strip().find('ISCSITG=\"\"') != -1:
            outfile.write(line.strip().replace(
                'ISCSITG=\"\"', "ISCSITG=\"" + iscsitarget + "\"\n"))
        elif line.strip().find('mypassword') != -1:
            outfile.write(line.strip().replace(
                'mypassword', rootpw))
        else:
            outfile.write(line)
    fr.close()
    outfile.close()

    # Use fileinput to do inplace text replacement for ESXi5.5u2
    # add vibs to install process, vmtools and patch
    if esx_version == "ESXi5.5u2":
        newstr = "esxcli software vib install --viburl=http://10.158.81.38/KS/repo/ESXi550-201505002.zip\n" + \
            "esxcli software vib install --viburl=http://10.158.81.38/KS/repo/esx-tools-for-esxi-9.7.2-0.0.5911061.i386.vib\n"
        # print "Replacing VIBINSTALL STRING--\n" + newstr
        # print '##VIBINSTALLSTRING'
        for line in fileinput.input(outks, inplace=True):
            print line.strip().replace('##VIBINSTALLSTRING', newstr)

    print "KS.CFG file -- ", outks

    # Part 2 - Generate MNU file
    # Ouput file - outmnu
    fr = open(mnupath, "r")
    outfile = open(outmnu, 'w')

    for line in fr:
        # if line.strip() == 'replacethislinewithcorrectvalues':
        if line.strip().find('REPLACETHISLINE') != -1:
            newstr = "-c /pxelinux.cfg/boot/01-" + macaddr + \
                "boot.cfg ks=http://10.10.10.5/KS/01-" + macaddr + ".cfg +++"
            outfile.write(line.replace(
                'REPLACETHISLINE', newstr))
        elif line.strip().find('ESXVERSION') != -1:
            outfile.write(line.replace(
                'ESXVERSION', esx_version))
        elif line.strip().find('REPLACEWTITLE') != -1:
            outfile.write(line.replace(
                'REPLACEWTITLE', ESXTITLE))
        else:
            outfile.write(line)
    fr.close()
    outfile.close()

    print "MNU file created -- ", outmnu

    # Part 3 - create Boot.CFG files
    fr = open(bootpath, "r")
    outfile = open(outboot, 'w')

    for line in fr:
        # if line.strip() == 'replacethislinewithcorrectvalues':
        if line.strip().find('runweasel') != -1:
            newstr = "http://10.10.10.5/KS/01-" + macaddr + ".cfg"
            outfile.write(line.replace(
                'runweasel', newstr))
        elif line.strip().find('ESXVERSION') != -1:
            outfile.write(line.replace(
                'ESXVERSION', esx_version))
        else:
            outfile.write(line)
    fr.close()
    outfile.close()
    print "BootCFG file created -- ", outboot

    print "Transfering Files to: "
    import os
    os.system("scp " + outks + " root@10.159.81.200:/tmp/")


# Start program
if __name__ == "__main__":
    main()
