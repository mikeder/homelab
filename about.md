# Homelab Repo

My personal home lab compose templates.

Runs on a single docker VM on a single Proxmox host machine. The VM templates are as below:

```bash
root@pve:/# cd /etc/pve/qemu-server
root@pve:/etc/pve/qemu-server# ls
100.conf  103.conf
```

`100.conf`
```ini
balloon: 0
boot: order=scsi0;ide2;net0
cores: 2
cpu: host
ide2: none,media=cdrom
memory: 4096
name: freenas
net0: virtio=3E:94:1D:50:03:30,bridge=vmbr0,firewall=1
numa: 1
onboot: 1
ostype: l26
scsi0: black1:100/vm-100-disk-1.raw,size=32G
scsi1: /dev/disk/by-id/ata-WDC_WD20EFRX-68EUZN0_WD-WMC4M1155464,size=2000G
scsi2: /dev/disk/by-id/ata-WDC_WD20EFRX-68EUZN0_WD-WCC4M2XPP587,size=2000G
scsi3: /dev/disk/by-id/ata-WDC_WD20EFRX-68EUZN0_WD-WCC4M0173865,size=2000G
scsi4: /dev/disk/by-id/ata-WDC_WD20EFRX-68EUZN0_WD-WCC4M7KDVTJ7,size=2000G
scsi5: /dev/disk/by-id/ata-WDC_WD20EFRX-68EUZN0_WD-WCC4M6NXP2AJ,size=2000G
scsihw: virtio-scsi-pci
smbios1: uuid=0469a370-945e-4225-a53e-9f2cc8b7b1ff
sockets: 1
startup: order=1
vmgenid: b74c87a6-b8f7-42ae-a47c-14c426cfb856
```

`103.conf`
```ini
balloon: 0
boot: order=scsi0;net0
cores: 2
cpu: host
memory: 2048
name: docker-04
net0: virtio=2E:4D:B8:80:EE:A3,bridge=vmbr0,firewall=1
numa: 1
onboot: 1
ostype: l26
scsi0: black1:103/vm-103-disk-0.qcow2,size=200G
scsihw: virtio-scsi-pci
smbios1: uuid=5a2f866b-1956-46d0-b5d6-652357a48c16
sockets: 1
startup: order=2
vmgenid: 09454f8c-c825-49fa-970f-543ef9bc93cc
```