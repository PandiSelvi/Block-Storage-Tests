"""

Config file for the scripts
Should be edited with respective parameters
before executing the script

author: pandiselvi.rajangam@ril.com

"""


# Endpoints
volume_url = "http://10.0.2.15:8776/v2/"
glance_url = "http://10.0.2.15:9292/v1/"
nova_url = "http://10.0.2.15:8774/v2/"
network_url = "http://10.0.2.15:9696/v2.0/"

# Log path
log_file_name = "/home/ubuntu/test.log"

# Tenant and user
tenant_name = "demo"
user_name = "demo"
password = "password"

# Volume
non_bootable_volume_name = "non_boot_vol"
non_bootable_volume_size = 1
bootable_volume_name = "boot_vol"
bootable_volume_size = 3
bootable_volume_size_for_data = 5
volume_block_size = 2000
count = 1000
volume_limit = 10
image_name = "cirros-0.3.4-x86_64-uec"
multiple_boot_volumes_limit = 3

# Instance
flavor = 2
key_name = "oskey1"
network = "private"
security_group = "default"
instance_name = "boot_inst"

# Backup
backup_name = "back_up"
backup_limit = 10
