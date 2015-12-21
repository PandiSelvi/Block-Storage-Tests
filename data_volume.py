"""

Resuable functions for data operations on volume

author: pandiselvi.rajangam@ril.com

"""

import time
import httplib
import httplib2
import json
import datetime
import paramiko
import StringIO
import shlex


def create_filesystem(instance_ip, device, mount_dir):
    """
       Creates filesystem on a volume attached to an instance
       Return value: "Filesystem Created"
    """
    ssh = paramiko.SSHClient()
    key_file = open('/home/ubuntu/devstack/oskey1.priv', 'r')
    string = key_file.read()
    keyfile = StringIO.StringIO(string)
    mykey = paramiko.RSAKey.from_private_key(keyfile)
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(instance_ip, username='cirros', pkey=mykey)
    stdin, stdout, stderr = ssh.exec_command(
        "sudo /usr/sbin/mkfs.ext3 -b 1024 %s" % device, get_pty=True)
    output = stdout.readlines()
    stdin, stdout, stderr = ssh.exec_command("sudo /sbin/blkid /dev/vd*")
    output = stdout.readlines()
    ssh.close()
    for line in output:
        if device in line:
            return "Filesystem Created"


def mount_volume(instance_ip, device, mount_dir):
    """
      Mounts volume with the given directory
      Return value : "Successfully mounted"
    """
    ssh = paramiko.SSHClient()
    key_file = open('/home/ubuntu/devstack/oskey1.priv', 'r')
    string = key_file.read()
    keyfile = StringIO.StringIO(string)
    mykey = paramiko.RSAKey.from_private_key(keyfile)
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(instance_ip, username='cirros', pkey=mykey)
    stdin, stdout, stderr = ssh.exec_command("sudo mkdir %s" % mount_dir)
    stdin, stdout, stderr = ssh.exec_command(
        "sudo mount %s %s" % (device, mount_dir))
    time.sleep(60)
    stdin, stdout, stderr = ssh.exec_command("sudo /sbin/blkid /dev/vd*")
    output = stdout.readlines()
    stdin, stdout, stderr = ssh.exec_command("sudo df -h")
    output = stdout.readlines()
    ssh.close()
    for i in output:
        if device and mount_dir in i:
            return "Successfully mounted"


def unmount_volume(instance_ip, mount_dir):
    """
      Unmounts a volume
      Return value: "Successfully unmounted"
    """
    ssh = paramiko.SSHClient()
    key_file = open('/home/ubuntu/devstack/oskey1.priv', 'r')
    string = key_file.read()
    keyfile = StringIO.StringIO(string)
    mykey = paramiko.RSAKey.from_private_key(keyfile)
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(instance_ip, username='cirros', pkey=mykey)
    stdin, stdout, stderr = ssh.exec_command("sudo umount %s " % (mount_dir))
    stdin, stdout, stderr = ssh.exec_command("sudo df -h")
    output = stdout.readlines()
    ssh.close()
    for i in output:
        if mount_dir not in i:
            return "Successfully unmounted"


def write_data_on_volume(instance_ip, block_size, count, mount_dir):
    """
      Writes data on volume with given size
      Return value : None
    """
    ssh = paramiko.SSHClient()
    key_file = open('/home/ubuntu/devstack/oskey1.priv', 'r')
    string = key_file.read()
    keyfile = StringIO.StringIO(string)
    mykey = paramiko.RSAKey.from_private_key(keyfile)
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(instance_ip, username='cirros', pkey=mykey)
    if mount_dir == "/":
        stdin, stdout, stderr = ssh.exec_command(
            "sudo dd if=/dev/zero of=%stest.img bs=%d count=%d"
            % (mount_dir, block_size, count))
    else:
        stdin, stdout, stderr = ssh.exec_command(
            "sudo dd if=/dev/zero of=%s/test.img bs=%d count=%d"
            % (mount_dir, block_size, count))
        stdout.readlines()
        ssh.close()


def is_file_exists(instance_ip, mount_dir, file_size, file_name="test.img"):
    """
      Checks if a file with a given size exists in a directory
      Return value: True
    """
    ssh = paramiko.SSHClient()
    key_file = open('/home/ubuntu/devstack/oskey1.priv', 'r')
    string = key_file.read()
    keyfile = StringIO.StringIO(string)
    mykey = paramiko.RSAKey.from_private_key(keyfile)
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(instance_ip, username='cirros', pkey=mykey)
    stdin, stdout, stderr = ssh.exec_command("sync")
    stdin, stdout, stderr = ssh.exec_command("cd %s;""ls -l;" % mount_dir)
    time.sleep(30)
    output = stdout.readlines()
    ssh.close()
    for line in output:
        if file_name in line:
            details = shlex.split(line)
            if int(details[4]) == file_size:
                return True
    raise Exception(
                 "File %s not found" % file_name)
