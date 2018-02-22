<#

    SCript to Configure Nested LAb Environment ISCSI Storage
    Reference:https://wiki.engr.opsource.net/display/PES/NestedLabEnvironment+-+iSCSI+Node+Build+Procedure
    Author: FN
    Date: 10/28/2016

#>


Import-Module -Name ServerManager
# Installing ISCSI Target Components
if (!(Get-WindowsFeature -Name FS-iSCSITarget-Server).Installed){
    Write-Host "FS-iSCSITarget-Server - Installing"
    Add-WindowsFeature -Name FS-iSCSITarget-Server -Confirm:$false
}else{
    Write-Host "FS-iSCSITarget-Server - Already Installed"
}

if (!(Get-WindowsFeature -Name iSCSITarget-VSS-VDS).Installed){
    Write-Host "iSCSITarget-VSS-VDS - Installing"
    Add-WindowsFeature -Name iSCSITarget-VSS-VDS -Confirm:$false
}else{
    Write-Host "iSCSITarget-VSS-VDS - Already Installed"
}

#Configure ISCSI Target Server
Import-Module -Name iSCSITarget

$targetname = $env:COMPUTERNAME
If (!(Get-IscsiServerTarget -TargetName $targetname -ErrorAction SilentlyContinue)){
    Write-Host "ISCSI TargetName [$targetname] not found"
    Write-Host "Creating [$targetname] target"
    New-IscsiServerTarget -TargetName $targetname 
    ## Assign target to all initiator attempting to connect to it
    Set-IscsiServerTarget -TargetName $targetname -InitiatorIds "IQN:*"

}



# Create DataStore Folder
if (!(Test-Path "c:\DataStores")){

    mkdir "c:\DataStores"
}


# Get Disk
Write-Host "Rescan for New Disk"
"rescan" | diskpart


## Format and mount all required volumes
# Get New disk only
Write-Host "Get List of Disk"
$disks = Get-Disk | where {$_.PartitionStyle -ne "MBR"}


foreach ($disk in $disks){
    
    $dnum = $disk.Number
    $dname = $env:COMPUTERNAME + "_Disk"+$dnum
    $dsize = $disk.Size - ($disk.Size * 0.05)

      
        
        Write-Host "[$dname] DiskNumber [$dnum] "
        #checking if disk already mapped
        if (! (Test-Path "C:\DataStores\$dname\$dname.vhd" -ErrorAction SilentlyContinue)){
            Write-Host "[$dname] - Creating ISCSI Disk Mapping"

            Initialize-Disk $dnum -ErrorAction SilentlyContinue           

            Write-Host "Creating $dname"
            Write-Host "New-Partition -DiskNumber $dnum -UseMaximumSize | Format-Volume -FileSystem NTFS -NewFileSystemLabel $dname -Confirm:$false"
            New-Partition -DiskNumber $dnum -UseMaximumSize | Format-Volume -FileSystem NTFS -NewFileSystemLabel $dname -Confirm:$false   
    
            Write-Host "Creating folder c:\DataStores\$dname"
            Write-Host "mkdir C:\DataStores\$dname"
            mkdir C:\DataStores\$dname -ErrorAction SilentlyContinue
    
            Write-Host "Add-PartitionAccessPath -DiskNumber $dnum -PartitionNumber 2 -AccessPath `"C:\DataStores\$dname\`""
            Add-PartitionAccessPath -DiskNumber $dnum -PartitionNumber 2 -AccessPath "C:\DataStores\$dname"


            ## Create ISCSI Virtual Disk
            Write-Host "New-IscsiVirtualDisk -Path C:\DataStores\$dname\$dname.vhd -Size $dsize"
            New-IscsiVirtualDisk -Path "C:\DataStores\$dname\$dname.vhd" -Size $dsize 

            ## Assign VHD to a Target
            Write-Host "Add-IscsiVirtualDiskTargetMapping $targetname `"C:\DataStores\$dname\$dname.vhd`""
            Add-IscsiVirtualDiskTargetMapping $targetname "C:\DataStores\$dname\$dname.vhd"
        
        }else{
            Write-Host "[$dname] - Disk already Mapped. Skip"
        
        }
    


}


#Configure JUMBO FRAMES
$Netadapter = Get-NetAdapter * | Where-Object { $_.TransmitLinkSpeed –EQ “10000000000” }
if ($Netadapter){
    Set-NetAdapterAdvancedProperty $Netadapter.name -DisplayName “Jumbo Packet” -DisplayValue “Jumbo 9000”
}






#adding storage to the target

