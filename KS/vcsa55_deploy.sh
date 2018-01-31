#!/bin/bash

for i in "$@"
do
case $i in
    -h=*|--esxi-host=*)
    ESXI_HOST="${i#*=}"
    shift # past argument=value
    ;;
    -u=*|--esxi-username=*)
    ESXI_USERNAME="${i#*=}"
    shift # past argument=value
    ;;
    -p=*|--esxi-password=*)
    ESXI_PASSWORD="${i#*=}"
    shift # past argument=value
    ;;
    -v=*|--vcsa-vmname=*)
    VCSA_VMNAME="${i#*=}"
    shift # past argument=value
    ;;
    -n=*|--vcsa-hostname=*)
    VCSA_HOSTNAME="${i#*=}"
    shift # past argument=value
    ;;
    -i=*|--vcsa-ip=*)
    VCSA_IP="${i#*=}"
    shift # past argument=value
    ;;
    -m=*|--vcsa-netmask=*)
    VCSA_NETMASK="${i#*=}"
    shift # past argument=value
    ;;
    -g=*|--vcsa-gateway=*)
    VCSA_GATEWAY="${i#*=}"
    shift # past argument=value
    ;;
    -d=*|--vcsa-dns=*)
    VCSA_DNS="${i#*=}"
    shift # past argument=value
    ;;
    -w=*|--vm-network=*)
    VM_NETWORK="${i#*=}"
    shift # past argument=value
    ;;
    -s=*|--vm-datastore=*)
    VM_DATASTORE="${i#*=}"
    shift # past argument=value
    ;;
    --default)
    DEFAULT=YES
    shift # past argument with no value
    ;;
    *)
            # unknown option
    ;;
esac
done


NEW_OVTOOL="/usr/lib/vmware-ovftool/ovftool"
VCSA_OVA=/mnt/nfs/VMware-vCenter-Server-Appliance-5.5.0.20200-2183109_OVF10.ova

#ESXI_HOST=192.168.1.100
#ESXI_USERNAME=root
#ESXI_PASSWORD=vmware123

#VCSA_VMNAME=VCSA-5.5
#VCSA_HOSTNAME=vcsa.virtuallyghetto.com
#VCSA_IP=192.168.1.200
#VCSA_NETMASK=255.255.255.0
#VCSA_GATEWAY=192.168.1.1
#VCSA_DNS=192.168.1.1
VM_NETWORK="VM Network"
#VM_DATASTORE=mini-local-datastore-1

echo "ESXI_HOST     = ${ESXI_HOST}"
echo "ESXI_USERNAME = ${ESXI_USERNAME}"
echo "ESXI_PASSWORD = ${ESXI_PASSWORD}"
echo "VCSA_VMNAME   = ${VCSA_VMNAME}"
echo "VCSA_HOSTNAME = ${VCSA_HOSTNAME}"
echo "VCSA_IP       = ${VCSA_IP}"
echo "VCSA_NETMASK  = ${VCSA_NETMASK}"
echo "VCSA_GATEWAY  = ${VCSA_GATEWAY}"
echo "VCSA_DNS      = ${VCSA_DNS}"
echo "VM_NETWORK    = ${VM_NETWORK}"
echo "VM_DATASTORE  = ${VM_DATASTORE}"
echo  

### DO NOT EDIT BEYOND HERE ###

echo "${NEW_OVTOOL}" --acceptAllEulas --noSSLVerify --skipManifestCheck --X:injectOvfEnv --powerOn "--net:Network 1=${VM_NETWORK}" --datastore=${VM_DATASTORE} --diskMode=thin --name=${VCSA_VMNAME} --prop:vami.hostname=${VCSA_HOSTNAME} --prop:vami.DNS.VMware_vCenter_Server_Appliance=${VCSA_DNS} --prop:vami.gateway.VMware_vCenter_Server_Appliance=${VCSA_GATEWAY} --prop:vami.ip0.VMware_vCenter_Server_Appliance=${VCSA_IP} --prop:vami.netmask0.VMware_vCenter_Server_Appliance=${VCSA_NETMASK} ${VCSA_OVA} \"vi://${ESXI_USERNAME}:${ESXI_PASSWORD}@${ESXI_HOST}/\"

echo "Executing Script..."

#"${NEW_OVTOOL}"

"${NEW_OVTOOL}" --acceptAllEulas --skipManifestCheck --noSSLVerify --X:injectOvfEnv --powerOn "--net:Network 1=${VM_NETWORK}" --datastore=${VM_DATASTORE} --diskMode=thin --name=${VCSA_VMNAME} --prop:vami.hostname=${VCSA_HOSTNAME} --prop:vami.DNS.VMware_vCenter_Server_Appliance=${VCSA_DNS} --prop:vami.gateway.VMware_vCenter_Server_Appliance=${VCSA_GATEWAY} --prop:vami.ip0.VMware_vCenter_Server_Appliance=${VCSA_IP} --prop:vami.netmask0.VMware_vCenter_Server_Appliance=${VCSA_NETMASK} ${VCSA_OVA} "vi://${ESXI_USERNAME}:${ESXI_PASSWORD}@${ESXI_HOST}/"


#"${NEW_OVTOOL}" --acceptAllEulas --skipManifestCheck --X:injectOvfEnv --powerOn "--net:Network 1=${VM_NETWORK}" --datastore=${VM_DATASTORE} --name=${VCSA_VMNAME} --prop:vami.hostname=${VCSA_HOSTNAME} --prop:vami.DNS.VMware_vCenter_Server_Appliance=${VCSA_DNS} --prop:vami.gateway.VMware_vCenter_Server_Appliance=${VCSA_GATEWAY} --prop:vami.ip0.VMware_vCenter_Server_Appliance=${VCSA_IP} --prop:vami.netmask0.VMware_vCenter_Server_Appliance=${VCSA_NETMASK} ${VCSA_OVA} \"vi://root:"Passw0rd!"@${ESXI_HOST}\/\""

#"${NEW_OVTOOL}" --acceptAllEulas --skipManifestCheck --X:injectOvfEnv --powerOn "--net:Network 1=${VM_NETWORK}" --datastore=${VM_DATASTORE} --diskMode=thin --name=${VCSA_VMNAME} --prop:vami.hostname=${VCSA_HOSTNAME} --prop:vami.DNS.VMware_vCenter_Server_Appliance=${VCSA_DNS} --prop:vami.gateway.VMware_vCenter_Server_Appliance=${VCSA_GATEWAY} --prop:vami.ip0.VMware_vCenter_Server_Appliance=${VCSA_IP} --prop:vami.netmask0.VMware_vCenter_Server_Appliance=${VCSA_NETMASK} ${VCSA_OVA} "vi://${ESXI_USERNAME}:${ESXI_PASSWORD}@${ESXI_HOST}/"

#"${NEW_OVTOOL}" --acceptAllEulas --skipManifestCheck --X:injectOvfEnv --powerOn "--net:Network 1=VM Network" --datastore=Store01 --diskMode=thin --name=vcsa341 --prop:vami.hostname=vcsa341.ashlab.ops --prop:vami.DNS.VMware_vCenter_Server_Appliance=10.159.81.20 --prop:vami.gateway.VMware_vCenter_Server_Appliance=10.158.81.1 --prop:vami.ip0.VMware_vCenter_Server_Appliance=10.158.81.60 --prop:vami.netmask0.VMware_vCenter_Server_Appliance=255.255.255.0 "/mnt/nfs/VMware-vCenter-Server-Appliance-5.5.0.20200-2183109_OVF10.ova" "vi://root:Passw0rd!@10.158.81.58/"



echo "End of Script"
