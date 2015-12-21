"""

Functional test cases for block storage

author: pandiselvi.rajangam@ril.com

"""

import data_volume
import volume_utils
import instance_utils
import backup_utils
import network_utils
import image_utils
import common_utils
import time
import sys
import os
import unittest
import traceback
import logging
import config
LOG = logging


def main():
    try:
        errors, failures = main_section()
        test_summary(errors, failures)
    except SystemExit:
        pass
        # do nothing, just exit
    except:
        LOG.error("Unexpected error:")
        LOG.error(traceback.format_exc())


def test_summary(errors, failures):
    error_count = len(errors)
    failure_count = len(failures)
    if (error_count > 0 or failure_count > 0):
        LOG.info("Number of failures = %s, " +
                 "Number of errors = %s" % (failure_count, error_count))
        LOG.info("**************************************************")
        LOG.info("       TEST COMPLETED WITH FAILURES")
        LOG.info("**************************************************")
    else:
        LOG.info("test completed and exiting normally")
        LOG.info("**************************************************")
        LOG.info("      TEST COMPLETED - ALL TESTS PASSED")
        LOG.info("**************************************************")


def main_section():
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s %(levelname)s %(message)s',
                        filename=config.log_file_name +
                        time.strftime("%d-%m-%Y") +
                        "-" + time.strftime("%I%M%S"),
                        filemode='w')

    class Functional_tests(unittest.TestCase):
        @classmethod
        def setUpClass(cls):
            cls.tenant_id, cls.auth_token = common_utils.keystone_login(
                                                   config.tenant_name,
                                                   config.user_name,
                                                   config.password)
            instances = instance_utils.instance_list(
                                  cls.tenant_id, cls.auth_token)
            floating_ips = network_utils.floating_ip_list(
                                  cls.tenant_id, cls.auth_token)
            volumes = volume_utils.volume_list(
                                  cls.tenant_id, cls.auth_token)
            backups = backup_utils.backup_list(cls.tenant_id, cls.auth_token)
            if len(instances["servers"]) > 0 or \
               len(floating_ips["floatingips"]) > 0 or \
               len(volumes["volumes"]) > 0 \
               or len(backups["backups"]) > 0:
                LOG.error("Could not run " +
                          "tests found some resources exists")
                print "Could not run"\
                      "tests found some resources exists"
                sys.exit()

        def setUp(self):
            self.tenant_id, self.auth_token = common_utils.keystone_login(
                                                    config.tenant_name,
                                                    config.user_name,
                                                    config.password)

        def test_01(self):
            """ Delete non bootable volume """
            volume_id = volume_utils.create_non_bootable_volume(
                               self.tenant_id, self.auth_token,
                               config.non_bootable_volume_name,
                               config.non_bootable_volume_size)
            value = volume_utils.volume_delete(
                           self.tenant_id, self.auth_token,
                           volume_id)
            try:
                self.assertNotEqual(
                        True, value,
                        "Volume is not deleted")
            except Exception as e:
                LOG.error(self.id() + " Volume is not deleted")
                raise e

        def test_02(self):
            """ Delete non bootable when attached to an instance """
            instance_id = instance_utils.create_instance(
                                  self.tenant_id, self.auth_token,
                                  config.image_name, config.flavor,
                                  config.key_name,
                                  config.network,
                                  config.security_group,
                                  config.instance_name)
            volume_id = volume_utils.create_non_bootable_volume(
                                  self.tenant_id, self.auth_token,
                                  config.non_bootable_volume_name,
                                  config.non_bootable_volume_size)
            device = volume_utils.attach_volume(
                                  self.tenant_id,
                                  self.auth_token,
                                  instance_id,
                                  volume_id)
            try:
                value = volume_utils.volume_delete(
                                 self.tenant_id,
                                 self.auth_token,
                                 volume_id)
            except Exception as e:
                    exception = "Volume cannot be deleted " + \
                              "while in attached state"
                    try:
                        self.assertIn(
                              exception, str(e),
                              "Exception not found")
                    except Exception as e:
                        LOG.error(self.id() + " Exception not found")
                        raise e

        def test_03(self):
            """ Delete bootable volume """
            volume_id = volume_utils.create_bootable_volume(
                                self.tenant_id, self.auth_token,
                                config.bootable_volume_name,
                                config.bootable_volume_size,
                                config.image_name)
            value = volume_utils.volume_delete(
                                self.tenant_id,
                                self.auth_token,
                                volume_id)
            try:
                self.assertNotEqual(
                       True, value,
                       "Volume is not deleted")
            except Exception as e:
                LOG.error(self.id() + " Volume is not deleted")
                raise e

        def test_04(self):
            """ Delete instance with non- bootable volume attached """
            instance_id = instance_utils.create_instance(
                                     self.tenant_id, self.auth_token,
                                     config.image_name,
                                     config.flavor,
                                     config.key_name,
                                     config.network,
                                     config.security_group,
                                     config.instance_name)
            volume_id = volume_utils.create_non_bootable_volume(
                               self.tenant_id, self.auth_token,
                               config.non_bootable_volume_name,
                               config.non_bootable_volume_size)
            device = volume_utils.attach_volume(
                            self.tenant_id, self.auth_token,
                            instance_id, volume_id)
            value = instance_utils.instance_delete(
                             self.tenant_id, self.auth_token,
                             instance_id)
            if value is True:
                LOG.error(self.id() + "Volume is not deleted")
                raise Exception("Volume is not deleted")
            content = volume_utils.volume_details(
                             self.tenant_id, self.auth_token,
                             volume_id)
            try:
                self.assertEqual("available", content["volume"]["status"],
                                 "Volume is not in available state")
            except Exception as e:
                LOG.error(self.id() + " Volume is " +
                                      "not in available state")
                raise e

        def test_05(self):
            """ Delete instance when boot volume
                attached to instance with delete=false
            """
            image_id = image_utils.image_id(
                             self.tenant_id, self.auth_token,
                             config.image_name)
            content = volume_utils.volume_create(
                             self.tenant_id, self.auth_token,
                             config.bootable_volume_name,
                             config.bootable_volume_size,
                             image_id)
            volume_id = content["volume"]["id"]
            is_available = volume_utils.is_volume_available(
                                  self.tenant_id,
                                  self.auth_token,
                                  volume_id)
            if is_available is not True:
                LOG.error(self.id() + " Volume is " +
                                      "not in available state")
                raise Exception("Volume is not in available state")
            content = volume_utils.volume_boot_attach_while_creating_instance(
                              self.tenant_id, self.auth_token,
                              volume_id, config.key_name,
                              config.instance_name,
                              config.flavor,
                              config.network,
                              config.security_group)
            instance_id = instance_utils.instance_id(
                              self.tenant_id, self.auth_token,
                              config.instance_name)
            is_active = instance_utils.is_instance_active(
                                self.tenant_id, self.auth_token,
                                instance_id)
            if is_active is not True:
                LOG.error(self.id() + " Instance is " +
                                      "not in active state")
                raise Exception("Instance is not in active state")
            volume_details = volume_utils.volume_details(
                                  self.tenant_id, self.auth_token,
                                  volume_id)
            if volume_details["volume"]["attachments"][0]["server_id"] != \
               instance_id:
                    LOG.error(self.id() + " Instance id " +
                                          "not found in volume attachment")
                    raise Exception("Instance id " +
                                    "not found in volume attachment")
            value = instance_utils.instance_delete(
                             self.tenant_id, self.auth_token,
                             instance_id)
            if value is True:
                LOG.error(self.id() + "Instance is \
                          not deleted")
                raise Exception("Instance is not deleted")
            content = volume_utils.volume_details(
                              self.tenant_id, self.auth_token,
                              volume_id)
            try:
                self.assertEqual("available", content["volume"]["status"],
                                 "Volume is not in available state")
            except Exception as e:
                LOG.error(
                     self.id() +
                     " Volume is not in available state")
                raise e

        def test_06(self):
            """ Delete instance when boot volume
                attached to instance with delete=true
            """
            image_id = image_utils.image_id(
                             self.tenant_id, self.auth_token,
                             config.image_name)
            content = volume_utils.volume_create(
                             self.tenant_id, self.auth_token,
                             config.bootable_volume_name,
                             config.bootable_volume_size,
                             image_id)
            volume_id = content["volume"]["id"]
            is_available = volume_utils.is_volume_available(
                                  self.tenant_id, self.auth_token,
                                  volume_id)
            if is_available is not True:
                LOG.error(self.id() + " Volume is " +
                                      "not in available state")
                raise Exception("Volume is not in available state")
            content = volume_utils.volume_boot_attach_while_creating_instance(
                            self.tenant_id, self.auth_token,
                            volume_id, config.key_name,
                            config.instance_name,
                            config.flavor,
                            config.network,
                            config.security_group,
                            delete="true")
            instance_id = instance_utils.instance_id(
                                 self.tenant_id, self.auth_token,
                                 config.instance_name)
            is_active = instance_utils.is_instance_active(
                                 self.tenant_id, self.auth_token,
                                 instance_id)
            if is_active is not True:
                LOG.error(self.id() + " Instance is " +
                                      "not in active state")
                raise Exception("Instance is not in active state")
            volume_details = volume_utils.volume_details(
                                    self.tenant_id, self.auth_token,
                                    volume_id)
            if volume_details["volume"]["attachments"][0]["server_id"] != \
               instance_id:
                    LOG.error(self.id() + " Instance id " +
                                          "not found in volume attachment")
                    raise Exception("Instance id not " +
                                    "found in volume attachment")
            value = instance_utils.instance_delete(
                            self.tenant_id, self.auth_token,
                            instance_id)
            if value is True:
                LOG.error(self.id() + "Instance is not deleted")
                raise Exception("Instance is not deleted")
            try:
                details = volume_utils.volume_details(
                                 self.tenant_id, self.auth_token,
                                 volume_id)
                if details["volume"]["status"] == "in-use" or \
                   "available":
                        time.sleep(15)
                while details["volume"]["status"] == "deleting":
                        time.sleep(5)
                        details = volume_utils.volume_details(
                                          self.tenant_id, self.auth_token,
                                          volume_id)
            except Exception as e:
                if "Volume could not be found" not in str(e):
                    LOG.error(self.id() + "Exception not found")
                    raise Exception("Exception not found")
            content = volume_utils.volume_list(
                            self.tenant_id, self.auth_token)
            for volume in range(len(content["volumes"])):
                try:
                    self.assertNotEqual(
                          volume_id,
                          content["volumes"][volume]["id"],
                          "Volume is not deleted")
                except Exception as e:
                    LOG.error(self.id() + " Volume is not deleted")
                    raise e

        def test_07(self):
            """ Negative - Delete bootable volume in use """
            image_id = image_utils.image_id(
                             self.tenant_id, self.auth_token,
                             config.image_name)
            content = volume_utils.volume_create(
                             self.tenant_id, self.auth_token,
                             config.bootable_volume_name,
                             config.bootable_volume_size,
                             image_id)
            volume_id = content["volume"]["id"]
            is_available = volume_utils.is_volume_available(
                                  self.tenant_id, self.auth_token,
                                  volume_id)
            if is_available is not True:
                LOG.error(self.id() + " Volume is " +
                                      "not in available state")
                raise Exception("Volume is not in available state")
            content = volume_utils.volume_boot_attach_while_creating_instance(
                             self.tenant_id, self.auth_token,
                             volume_id, config.key_name,
                             config.instance_name, config.flavor,
                             config.network, config.security_group)
            instance_id = instance_utils.instance_id(
                                  self.tenant_id, self.auth_token,
                                  config.instance_name)
            is_active = instance_utils.is_instance_active(
                                 self.tenant_id, self.auth_token,
                                 instance_id)
            if is_active is not True:
                LOG.error(self.id() + " Instance is " +
                                      "not in active state")
                raise Exception("Instance is not in active state")
            volume_details = volume_utils.volume_details(
                                     self.tenant_id, self.auth_token,
                                     volume_id)
            if volume_details["volume"]["attachments"][0]["server_id"] != \
               instance_id:
                    LOG.error(self.id() + " Instance id " +
                                          "not found in volume attachment")
                    raise Exception("Instance id " +
                                    "not found in volume attachment")
            try:
                value = volume_utils.volume_delete(
                               self.tenant_id, self.auth_token,
                               volume_id)
            except Exception as e:
                exception = "Volume cannot be deleted " + \
                            "while in attached state"
                try:
                    self.assertIn(
                          exception, str(e),
                          "Exception not found")
                except Exception as e:
                    LOG.error(self.id() + " Exception not found")
                    raise e

        def test_08(self):
            """ Data on volume persists even after the instance is deleted """
            instance_id = instance_utils.create_instance(
                                    self.tenant_id, self.auth_token,
                                    config.image_name, config.flavor,
                                    config.key_name,
                                    config.network,
                                    config.security_group,
                                    config.instance_name)
            volume_id = volume_utils.create_non_bootable_volume(
                               self.tenant_id, self.auth_token,
                               config.non_bootable_volume_name,
                               config.non_bootable_volume_size)
            device = volume_utils.attach_volume(
                             self.tenant_id, self.auth_token,
                             instance_id, volume_id)
            instance_ip = network_utils.floating_ip_associate(
                                 self.tenant_id, self.auth_token,
                                 "public", instance_id)
            time.sleep(30)
            value = data_volume.create_filesystem(
                                instance_ip, device, "/mnt/temp")
            if value != "Filesystem Created":
                LOG.error(self.id() + "File \
                          system not created")
                raise Exception("File system not created")
            value = data_volume.mount_volume(
                         instance_ip, device, "/mnt/temp")
            if value != "Successfully mounted":
                LOG.error(self.id() + " Volume is " +
                          "not mounted successfully")
                raise Exception("Volume is not mounted successfully")
            size = config.volume_block_size
            count = config.count
            file_size = size*count
            data_volume.write_data_on_volume(
                         instance_ip, size,
                         count, "/mnt/temp")
            time.sleep(30)
            value = data_volume.is_file_exists(
                         instance_ip, "/mnt/temp", file_size)
            if value is not True:
                LOG.error(self.id() + "File doesnot exists")
                raise Exception("File doesnot exists")
            value = instance_utils.instance_delete(
                          self.tenant_id, self.auth_token,
                          instance_id)
            if value is True:
                LOG.error(self.id() + " Instance is " +
                                      "not deleted successfully")
                raise Exception("Instance is not deleted successfully")
            instance_id = instance_utils.create_instance(
                                 self.tenant_id, self.auth_token,
                                 config.image_name, config.flavor,
                                 config.key_name, config.network,
                                 config.security_group,
                                 config.instance_name)
            instance_ip = network_utils.floating_ip_associate(
                                self.tenant_id, self.auth_token,
                                "public", instance_id)
            time.sleep(30)
            device = volume_utils.attach_volume(
                           self.tenant_id, self.auth_token,
                           instance_id, volume_id)
            value = data_volume.mount_volume(
                           instance_ip, device, "/mnt/temp")
            if value != "Successfully mounted":
                LOG.error(self.id() + " Volume is " +
                                      "not mounted successfully")
                raise Exception("Volume is not mounted successfully")
            value = data_volume.is_file_exists(
                            instance_ip, "/mnt/temp", file_size)
            try:
                self.assertEqual(
                       True, value,
                       "File doesnot exists")
            except Exception as e:
                LOG.error(self.id() + "File doesnot exists")
                raise e

        def test_09(self):
            """ Volume with maximum size and  minimum size """
            vol_name = config.non_bootable_volume_name
            for size in [1, 1000]:
                    volume_id = volume_utils.create_non_bootable_volume(
                                    self.tenant_id, self.auth_token,
                                    vol_name + str(size),
                                    size)
                    is_available = volume_utils.is_volume_available(
                                           self.tenant_id, self.auth_token,
                                           volume_id)
                    if is_available is not True:
                        LOG.error(self.id() + " Volume is " +
                                              "not in available state")
                    self.assertEqual(
                            True, is_available,
                            "Volume is not in available state")

        def test_10(self):
            """ Negative - Volume size greater than
                maximum size and less than minimum size
            """
            vol_name = config.non_bootable_volume_name
            for size in [-1, 1001]:
                try:
                    volume_id = volume_utils.create_non_bootable_volume(
                                    self.tenant_id, self.auth_token,
                                    vol_name + str(size),
                                    size)
                except Exception as e:
                    if size == -1:
                        if "Invalid volume size provided" not in str(e):
                            LOG.error(self.id() + "Exception not found")
                        self.assertIn(
                            "Invalid volume size provided", str(e),
                            "Exception not found")
                    elif size == 1001:
                        exception = "Requested volume or" + \
                                   " snapshot exceeds allowed" + \
                                   " gigabytes quota"
                        try:
                            self.assertIn(
                                 exception, str(e),
                                 "Exception not found")
                        except Exception as e:
                            LOG.error(self.id() + " Exception not found")
                            raise e

        def test_11(self):
            """  Create backup """
            volume_id = volume_utils.create_non_bootable_volume(
                            self.tenant_id, self.auth_token,
                            config.non_bootable_volume_name,
                            config.non_bootable_volume_size)
            backup_id = backup_utils.create_backup(
                            self.tenant_id, self.auth_token,
                            volume_id, config.backup_name)
            try:
                self.assertNotEqual(
                       0, backup_id, "Backup creation failed")
            except Exception as e:
                LOG.error(self.id() + " Backup creation failed")
                raise e

        def test_12(self):
            """ Negative - Backup when volume is in use """
            instance_id = instance_utils.create_instance(
                           self.tenant_id, self.auth_token,
                           config.image_name, config.flavor,
                           config.key_name, config.network,
                           config.security_group,
                           config.instance_name)
            volume_id = volume_utils.create_non_bootable_volume(
                           self.tenant_id, self.auth_token,
                           config.non_bootable_volume_name,
                           config.non_bootable_volume_size)
            device = volume_utils.attach_volume(
                           self.tenant_id, self.auth_token,
                           instance_id, volume_id)
            if device:
                pass
            else:
                LOG.error(self.id() + " Volume not attached successfully")
                raise Exception("Volume not attached successfully")
            try:
                backup_id = backup_utils.create_backup(
                               self.tenant_id, self.auth_token,
                               volume_id, config.backup_name)
            except Exception as e:
                exception_1 = "Invalid volume:" + \
                              " Volume to be backed up" + \
                              " must be available"
                exception_2 = "Invalid volume:" + \
                              " Volume status is in-use"
                try:
                    self.assertIn(
                         exception_1 or exception_2, str(e),
                         "Exception not found")
                except Exception as e:
                    LOG.error(self.id() + " Exception not found")
                    raise e

        def test_13(self):
            """ Create maximum number of backups """
            volume_id = volume_utils.create_non_bootable_volume(
                              self.tenant_id, self.auth_token,
                              config.non_bootable_volume_name,
                              config.non_bootable_volume_size)
            for i in range(0, config.backup_limit):
                backup_name = config.backup_name + str(i)
                backup_id = backup_utils.create_backup(
                                 self.tenant_id, self.auth_token,
                                 volume_id, backup_name)
                backup_list = backup_utils.backup_list(
                                 self.tenant_id, self.auth_token)
            try:
                self.assertEqual(
                      config.backup_limit,
                      len(backup_list["backups"]),
                      "Number of " +
                      "backups is not equal to the maximum limit")
            except Exception as e:
                LOG.error(
                      self.id() +
                      " Number of backups " +
                      "is not equal to the maximum limit")
                raise e

        def test_14(self):
            """  Negative - create backup more than maximum limit """
            volume_id = volume_utils.create_non_bootable_volume(
                               self.tenant_id, self.auth_token,
                               config.non_bootable_volume_name,
                               config.non_bootable_volume_size)
            negative_limit = config.backup_limit + 1
            for i in range(negative_limit):
                backup_name = config.backup_name + str(i)
                try:
                    backup_id = backup_utils.create_backup(
                                      self.tenant_id, self.auth_token,
                                      volume_id, backup_name)
                except Exception as e:
                    try:
                        self.assertIn("Maximum number of backups" and
                                      "exceeded", str(e),
                                      "Exception not found")
                    except Exception as e:
                        LOG.error(self.id() + " Exception not found")
                        raise e

        def test_15(self):
            """ Restore Backup """
            volume_id = volume_utils.create_non_bootable_volume(
                                self.tenant_id, self.auth_token,
                                config.non_bootable_volume_name,
                                config.non_bootable_volume_size)
            backup_id = backup_utils.create_backup(
                                self.tenant_id, self.auth_token,
                                volume_id,
                                config.backup_name)
            volume_id = backup_utils.restore_backup(
                                self.tenant_id, self.auth_token,
                                backup_id)
            try:
                self.assertNotEqual(
                       0, volume_id, "Backup restore failed")
            except Exception as e:
                LOG.error(self.id() + " Backup restore failed")
                raise e

        def test_16(self):
            """ Backup a volume with data when
                restored and attached to another instance data exists
            """
            instance_id = instance_utils.create_instance(
                                   self.tenant_id, self.auth_token,
                                   config.image_name, config.flavor,
                                   config.key_name,
                                   config.network,
                                   config.security_group,
                                   config.instance_name)
            volume_id = volume_utils.create_non_bootable_volume(
                                   self.tenant_id, self.auth_token,
                                   config.non_bootable_volume_name,
                                   config.non_bootable_volume_size)
            device = volume_utils.attach_volume(
                                   self.tenant_id, self.auth_token,
                                   instance_id, volume_id)
            instance_ip = network_utils.floating_ip_associate(
                                   self.tenant_id, self.auth_token,
                                   "public", instance_id)
            time.sleep(30)
            value = data_volume.create_filesystem(
                                instance_ip, device, "/mnt/temp")
            if value != "Filesystem Created":
                LOG.error(self.id() + "File system not created")
                raise Exception("File system not created")
            value = data_volume.mount_volume(
                          instance_ip, device, "/mnt/temp")
            if value != "Successfully mounted":
                LOG.error(self.id() + " Volume is " +
                                      " not mounted successfully")
                raise Exception("Volume is not mounted successfully")
            size = config.volume_block_size
            count = config.count
            file_size = size*count
            data_volume.write_data_on_volume(
                       instance_ip, size, count, "/mnt/temp")
            time.sleep(30)
            value = data_volume.is_file_exists(
                       instance_ip, "/mnt/temp", file_size)
            if value is not True:
                LOG.error(self.id() + "File doesnot exists")
                raise Exception("File doesnot exists")
            value = data_volume.unmount_volume(
                         instance_ip, "/mnt/temp")
            if value != "Successfully unmounted":
                LOG.error(self.id() + " Volume is " +
                                      "unmounted successfully")
                raise Exception("Volume is unmounted successfully")
            value = instance_utils.instance_delete(
                          self.tenant_id, self.auth_token,
                          instance_id)
            if value is True:
                LOG.error(self.id() + "Instance is " +
                                      "not deleted successfully")
                raise Exception("Instance is not deleted successfully")
            backup_id = backup_utils.create_backup(
                          self.tenant_id, self.auth_token,
                          volume_id, config.backup_name)
            volume_id = backup_utils.restore_backup(
                            self.tenant_id, self.auth_token,
                            backup_id)
            instance_id = instance_utils.create_instance(
                            self.tenant_id, self.auth_token,
                            config.image_name, config.flavor,
                            config.key_name, config.network,
                            config.security_group,
                            config.instance_name)
            instance_ip = network_utils.floating_ip_associate(
                             self.tenant_id, self.auth_token,
                             "public", instance_id)
            time.sleep(30)
            device = volume_utils.attach_volume(
                            self.tenant_id, self.auth_token,
                            instance_id, volume_id)
            value = data_volume.mount_volume(
                            instance_ip, device, "/mnt/temp")
            if value != "Successfully mounted":
                LOG.error(self.id() + " Volume is " +
                                      "not mounted successfully")
                raise Exception("Volume is not mounted successfully")
            value = data_volume.is_file_exists(
                        instance_ip, "/mnt/temp", file_size)
            try:
                self.assertEqual(
                      True, value, "File doesnot exists")
            except Exception as e:
                LOG.error(self.id() + " File doesnot exists")
                raise e

        def test_17(self):
            """ Negative - Restore fails as exceeds the volume limit """
            for i in range(config.volume_limit):
                volume_name = config.non_bootable_volume_name + str(i)
                volume_id = volume_utils.create_non_bootable_volume(
                                   self.tenant_id, self.auth_token,
                                   config.non_bootable_volume_name,
                                   config.non_bootable_volume_size)
                backup_id = backup_utils.create_backup(
                                   self.tenant_id, self.auth_token,
                                   volume_id, config.backup_name)
            try:
                volume_id = backup_utils.restore_backup(
                                  self.tenant_id, self.auth_token,
                                  backup_id)
            except Exception as e:
                try:
                    self.assertIn(
                         "Maximum number of volumes" and " exceeded",
                         str(e), "Exception not found")
                except Exception as e:
                    LOG.error(self.id() + " Exception not found")
                    raise e

        def test_18(self):
            """ Check backup ids are unique """
            volume_id = volume_utils.create_non_bootable_volume(
                           self.tenant_id, self.auth_token,
                           config.non_bootable_volume_name,
                           config.non_bootable_volume_size)
            for i in range(0, 2):
                backup_id = backup_utils.create_backup(
                                self.tenant_id, self.auth_token,
                                volume_id, config.backup_name + str(i))
                if i == 0:
                    backup_1 = backup_id
                else:
                    backup_2 = backup_id
            try:
                self.assertNotEqual(
                          backup_1, backup_2,
                          "Backup id's are unique")
            except Exception as e:
                LOG.error(self.id() + " Backup id's are unique")
                raise e

        def test_19(self):
            """ Delete Backup """
            volume_id = volume_utils.create_non_bootable_volume(
                         self.tenant_id, self.auth_token,
                         config.non_bootable_volume_name,
                         config.non_bootable_volume_size)
            backup_id = backup_utils.create_backup(
                           self.tenant_id, self.auth_token,
                           volume_id, config.backup_name)
            value = backup_utils.backup_delete(
                            self.tenant_id, self.auth_token, backup_id)
            try:
                self.assertNotEqual(
                        True, value,
                        "Backup not deleted successfully")
            except Exception as e:
                LOG.error(self.id() + " Backup not " +
                                      "deleted successfully")
                raise e

        def tearDown(self):
            instances = instance_utils.instance_list(
                               self.tenant_id, self.auth_token)
            if len(instances["servers"]) > 0:
                for instance in range(len(instances["servers"])):
                    instance_id = instances["servers"][instance]["id"]
                    value = instance_utils.instance_delete(
                                  self.tenant_id, self.auth_token,
                                  instance_id)
                    if value is True:
                            LOG.error(self.id() + " Instance not deleted")
                            raise Exception("Instance not deleted")
            floating_ips = network_utils.floating_ip_list(
                                   self.tenant_id, self.auth_token)
            if len(floating_ips["floatingips"]) > 0:
                    for ip in range(len(floating_ips["floatingips"])):
                        ip_id = floating_ips["floatingips"][ip]["id"]
                        value = network_utils.floating_ip_delete(
                                       self.tenant_id, self.auth_token,
                                       ip_id)
                        if value is True:
                            LOG.error(self.id() + " IP not deleted")
                            raise Exception("IP not deleted")
            volumes = volume_utils.volume_list(
                             self.tenant_id, self.auth_token)
            if len(volumes["volumes"]) > 0:
                for volume in range(len(volumes["volumes"])):
                    volume_id = volumes["volumes"][volume]["id"]
                    value = volume_utils.volume_delete(
                                   self.tenant_id, self.auth_token,
                                   volume_id)
                    if value is True:
                            LOG.error(self.id() + " Volume not deleted")
                            raise Exception("Volume not deleted")
            backups = backup_utils.backup_list(
                            self.tenant_id, self.auth_token)
            if len(backups["backups"]) > 0:
                for backup in range(len(backups["backups"])):
                    backup_id = backups["backups"][backup]["id"]
                    value = backup_utils.backup_delete(
                                  self.tenant_id, self.auth_token,
                                  backup_id)
                    if value is True:
                            LOG.error(self.id() + " Backup not deleted")
                            raise Exception("Backup not deleted")

    suite = unittest.TestLoader().loadTestsFromTestCase(Functional_tests)
    testResult = unittest.TextTestRunner(verbosity=2).run(suite)
    errors = testResult.errors
    failures = testResult.failures
    return errors, failures

if __name__ == "__main__":
    main()
