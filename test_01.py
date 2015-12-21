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
        LOG.info("Number of failures=%s,\
                 Number of errors=%s" % (failure_count, error_count))
        LOG.info("*************************************************")
        LOG.info("      TEST COMPLETED WITH FAILURES")
        LOG.info("*************************************************")
    else:
        LOG.info("test completed and exiting normally")
        LOG.info("*************************************************")
        LOG.info("      TEST COMPLETED - ALL TESTS PASSED")
        LOG.info("*************************************************")


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
                                            config.user_name, config.password)
            instances = instance_utils.instance_list(
                                            cls.tenant_id, cls.auth_token)
            floating_ips = network_utils.floating_ip_list(
                                           cls.tenant_id, cls.auth_token)
            volumes = volume_utils.volume_list(cls.tenant_id, cls.auth_token)
            if len(instances["servers"]) > 0 or \
               len(floating_ips["floatingips"]) > 0 or \
               len(volumes["volumes"]) > 0:
                        LOG.error("Could not " +
                                  "run tests found some " +
                                  "resources exists ")
                        print "Could not " + \
                              "run tests found some resources exists"
                        sys.exit()

        def setUp(self):
            self.tenant_id, self.auth_token = common_utils.keystone_login(
                                              config.tenant_name,
                                              config.user_name,
                                              config.password)

        def test_01(self):
            """ Create non-bootable volume """
            volume_id = volume_utils.create_non_bootable_volume(
                              self.tenant_id, self.auth_token,
                              config.non_bootable_volume_name,
                              config.non_bootable_volume_size)
            is_available = volume_utils.is_volume_available(
                               self.tenant_id, self.auth_token, volume_id)
            if is_available is not True:
                LOG.error(self.id() + " Volume is not in available state")
                raise Exception("Volume is not in available state")
            volume_details = volume_utils.volume_details(
                                 self.tenant_id, self.auth_token,
                                 volume_id)
            try:
                self.assertEqual(
                     config.non_bootable_volume_size,
                     volume_details["volume"]["size"],
                     "Volume size is different than the requested size")
            except Exception as e:
                LOG.error(self.id() + " Volume size is \
                          different than the requested size")
                raise e

        def test_02(self):
            """ Create maximum number of non bootable volumes """
            for volume in range(config.volume_limit):
                volume_name = "non_boot" + str(volume)
                volume_id = volume_utils.create_non_bootable_volume(
                                   self.tenant_id, self.auth_token,
                                   config.non_bootable_volume_name,
                                   config.non_bootable_volume_size)
                is_available = volume_utils.is_volume_available(
                                     self.tenant_id, self.auth_token,
                                     volume_id)
                if is_available is not True:
                    LOG.error(self.id() + " Volume is not in available state")
                    raise Exception("Volume is not in available state")
                volume_details = volume_utils.volume_details(
                                        self.tenant_id, self.auth_token,
                                        volume_id)
                if volume_details["volume"]["size"] != \
                   config.non_bootable_volume_size:
                    LOG.error(self.id() + " Volume size is \
                              different than the requested size")
                    raise Exception("Volume size \
                                    is different than the requested size")

                volume_list = volume_utils.volume_list(
                                     self.tenant_id, self.auth_token)
            try:
                self.assertEqual(
                      config.volume_limit,
                      len(volume_list["volumes"]),
                      "Number of volumes does not meet the maximum limit")
            except Exception as e:
                LOG.error(self.id() + " Number of volumes " +
                                      "does not meet the maximum limit")
                raise e

        def test_03(self):
            """ Create bootable volume """
            volume_id = volume_utils.create_bootable_volume(
                               self.tenant_id, self.auth_token,
                               config.bootable_volume_name,
                               config.bootable_volume_size,
                               config.image_name)
            volume_details = volume_utils.volume_details(
                               self.tenant_id,
                               self.auth_token,
                               volume_id)
            is_available = volume_utils.is_volume_available(
                                self.tenant_id, self.auth_token,
                                volume_id)
            try:
                self.assertEqual(
                      True, is_available,
                      "Volume is not in available state")
            except Exception as e:
                LOG.error(self.id() +
                          " Volume is not in available state")
                raise e
            try:
                self.assertEqual(
                     config.bootable_volume_size,
                     volume_details["volume"]["size"],
                     "Volume size " +
                     "is different than the requested size")
            except Exception as e:
                LOG.error(
                     self.id() + "Volume size " +
                                 "is different than the requested size")
                raise e
            try:
                self.assertEqual(
                      "true",  volume_details["volume"]["bootable"],
                      "volume is non-bootable")
            except Exception as e:
                LOG.error(self.id() + " Volume is non-bootable")
                raise e

        def test_04(self):
            """ Create bootable volume while creating instance """
            image_id = image_utils.image_id(
                            self.tenant_id, self.auth_token,
                            config.image_name)
            content = volume_utils.volume_create_while_creating_instance(
                             self.tenant_id, self.auth_token, image_id,
                             config.bootable_volume_size, config.key_name,
                             config.instance_name, config.flavor,
                             config.network,
                             config.security_group)
            instance_id = instance_utils.instance_id(
                            self.tenant_id, self.auth_token,
                            config.instance_name)
            is_active = instance_utils.is_instance_active(
                              self.tenant_id, self.auth_token, instance_id)
            if is_active is not True:
                LOG.error(self.id() + " Instance is not in active state")
                raise Exception("Instance is not in active state")
            instance_details = instance_utils.instance_details(
                                     self.tenant_id,  self.auth_token,
                                     instance_id)
            details = instance_details["server"]
            attachments = details["os-extended-volumes:volumes_attached"]
            volume_id = attachments[0]["id"]
            volume_details = volume_utils.volume_details(
                                  self.tenant_id,
                                  self.auth_token,
                                  volume_id)
            try:
                self.assertEqual(
                      instance_id,
                      volume_details["volume"]["attachments"][0]["server_id"],
                      "Instance id not found in volume details")
            except Exception as e:
                LOG.error(self.id() + " Instance id \
                          not found in volume details")
                raise e

        def test_05(self):
            """ Create muliple boot volumes """
            for volume in range(config.multiple_boot_volumes_limit):
                volume_name = config.bootable_volume_name + str(volume)
                volume_id = volume_utils.create_bootable_volume(
                                  self.tenant_id, self.auth_token,
                                  config.bootable_volume_name,
                                  config.bootable_volume_size,
                                  config.image_name)
                is_available = volume_utils.is_volume_available(
                                  self.tenant_id, self.auth_token,
                                  volume_id)
                if is_available is not True:
                    LOG.error(self.id() + " Volume is not in available state")
                    raise Exception("Volume is not in available state")
                volume_details = volume_utils.volume_details(
                                      self.tenant_id,
                                      self.auth_token,
                                      volume_id)
                if volume_details["volume"]["size"] != \
                   config.bootable_volume_size:
                    LOG.error(self.id() + " Volume size is\
                              different than the specified size")
                    raise Exception("Volume size is \
                                    different than the specified size")
                if volume_details["volume"]["bootable"] != "true":
                    LOG.error(self.id() + " Volume is non-bootable")
                    raise Exception("Volume is non-bootable")
                volume_list = volume_utils.volume_list(
                                      self.tenant_id,
                                      self.auth_token)
            try:
                self.assertEqual(
                     config.multiple_boot_volumes_limit,
                     len(volume_list["volumes"]),
                     "Number of volume" +
                     " not equal to the specified limit")
            except Exception as e:
                LOG.error(self.id() + " Number of volume \
                          not equal to the specified limit")
                raise e

        def test_06(self):
            """ Create multiple bootable and non_bootable volumes """
            image_id = image_utils.image_id(
                              self.tenant_id, self.auth_token,
                              config.image_name)
            my_list = [volume_utils.volume_create(
                                tenant_id=self.tenant_id,
                                auth_token=self.auth_token,
                                name="",
                                size=config.non_bootable_volume_size,
                                image_id=""),
                       volume_utils.volume_create(
                                    self.tenant_id,
                                    self.auth_token,
                                    config.bootable_volume_name,
                                    config.bootable_volume_size,
                                    image_id)]
            func = common_utils.random_pick(my_list)
            for i in range(4):
                volume = (next(func))
                volume_id = volume["volume"]["id"]
                is_available = volume_utils.is_volume_available(
                                     self.tenant_id, self.auth_token,
                                     volume_id)
                try:
                    self.assertEqual(True, is_available)
                except Exception as e:
                    LOG.error(self.id() + " Volume is not in available state")
                    raise e

        def test_07(self):
            """  Negative-Create volumes greater than maximum limit """
            for volume in range(1, config.volume_limit):
                volume_name = config.non_bootable_volume_name + str(volume)
                try:
                    volume_id = volume_utils.create_non_bootable_volume(
                                      self.tenant_id, self.auth_token,
                                      config.non_bootable_volume_name,
                                      config.non_bootable_volume_size)
                except Exception as e:
                    try:
                        self.assertIn(
                                "VolumeLimitExceeded", str(e),
                                "Exception not found")
                    except Exception as e:
                        LOG.error(self.id() + " Exception not found")
                        raise e

        def test_08(self):
            """ Attach volume while creating instance """
            content = volume_utils.volume_create(
                             self.tenant_id, self.auth_token,
                             config.non_bootable_volume_name,
                             config.non_bootable_volume_size)
            volume_id = content["volume"]["id"]
            is_available = volume_utils.is_volume_available(
                              self.tenant_id, self.auth_token, volume_id)
            if is_available is not True:
                LOG.error(self.id() + " Volume is not in available state")
                raise Exception("Volume is not in available state")
            image_id = image_utils.image_id(
                            self.tenant_id, self.auth_token,
                            config.image_name)
            content = volume_utils.volume_attach_while_creating_instance(
                             self.tenant_id, self.auth_token, image_id,
                             volume_id, config.key_name,
                             config.instance_name,
                             config.flavor, config.network,
                             config.security_group)
            instance_id = instance_utils.instance_id(
                                  self.tenant_id,
                                  self.auth_token,
                                  config.instance_name)
            is_active = instance_utils.is_instance_active(
                                self.tenant_id, self.auth_token,
                                instance_id)
            if is_active is not True:
                LOG.error(self.id() + " Instance is not in active state")
                raise Exception("Instance is not in active state")
            volume_details = volume_utils.volume_details(
                                   self.tenant_id,
                                   self.auth_token, volume_id)
            try:
                self.assertEqual(
                      instance_id,
                      volume_details["volume"]["attachments"][0]["server_id"],
                      "Instance id not found in volume details")
            except Exception as e:
                LOG.error(self.id() + " Instance id \
                          not found in volume details")
                raise e

        def test_09(self):
            """ Attach non bootable volume """
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
            try:
                self.assertNotEqual(
                          0, device,
                          "Volume not attached successfully")
            except Exception as e:
                LOG.error(self.id() + " Volume not attached successfully")
                raise e

        def test_10(self):
            """ Attach multiple non bootable volume """
            instance_id = instance_utils.create_instance(
                                      self.tenant_id, self.auth_token,
                                      config.image_name, config.flavor,
                                      config.key_name, config.network,
                                      config.security_group,
                                      config.instance_name)
            for i in range(3):
                volume_name = config.non_bootable_volume_name + str(i)
                volume_id = volume_utils.create_non_bootable_volume(
                                       self.tenant_id,
                                       self.auth_token,
                                       config.non_bootable_volume_name,
                                       config.non_bootable_volume_size)
                device = volume_utils.attach_volume(
                                 self.tenant_id,
                                 self.auth_token,
                                 instance_id,
                                 volume_id)
                try:
                    self.assertNotEqual(
                           0, device,
                           "Volume not attached successfully")
                except Exception as e:
                    LOG.error(self.id() + " Volume not attached successfully")
                    raise e

        def test_11(self):
            """ Attach_non_bootable_when_vm is shut off """
            instance_id = instance_utils.create_instance(
                                   self.tenant_id, self.auth_token,
                                   config.image_name, config.flavor,
                                   config.key_name, config.network,
                                   config.security_group,
                                   config.instance_name)
            content = instance_utils.nova_stop_instance(
                                   self.tenant_id, self.auth_token,
                                   instance_id)
            time.sleep(10)
            instance_details = instance_utils.instance_details(
                                        self.tenant_id, self.auth_token,
                                        instance_id)
            while instance_details["server"]["OS-EXT-STS:task_state"] == \
                    "powering-off":
                    time.sleep(5)
                    instance_details = instance_utils.instance_details(
                                            self.tenant_id, self.auth_token,
                                            instance_id)

            if instance_details["server"]["status"] != "SHUTOFF":
                LOG.error(self.id() + " Instance is not in SHUTOFF state")
                raise Exception("Instance is not in SHUTOFF state")
            volume_id = volume_utils.create_non_bootable_volume(
                                  self.tenant_id, self.auth_token,
                                  config.non_bootable_volume_name,
                                  config.non_bootable_volume_size)
            device = volume_utils.attach_volume(
                                 self.tenant_id, self.auth_token,
                                 instance_id, volume_id)
            content = instance_utils.nova_start_instance(
                                 self.tenant_id, self.auth_token,
                                 instance_id)
            time.sleep(3)
            instance_details = instance_utils.instance_details(
                                         self.tenant_id, self.auth_token,
                                         instance_id)
            while instance_details["server"]["OS-EXT-STS:task_state"] == \
                    "powering-on":
                time.sleep(5)
                instance_details = instance_utils.instance_details(
                                               self.tenant_id, self.auth_token,
                                               instance_id)
            if instance_details["server"]["status"] != "ACTIVE":
                LOG.error(self.id() + "Instance is non in active state")
                raise Exception("Instance is non in active state")
            volume_details = volume_utils.volume_details(
                                      self.tenant_id, self.auth_token,
                                      volume_id)
            try:
                self.assertEqual("in-use", volume_details["volume"]["status"],
                                 "Volume is not in in-use state")
            except Exception as e:
                LOG.error(self.id() + " Volume is not in in-use state")
                raise e

        def test_12(self):
            """ Attach boot volume_while_creating_instance """
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
                LOG.error(self.id() + " Volume is not in available state")
                raise Exception("Volume is not in available state")
            content = volume_utils.volume_boot_attach_while_creating_instance(
                              self.tenant_id, self.auth_token, volume_id,
                              config.key_name, config.instance_name,
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
                LOG.error(self.id() + " Instance is non in active state")
                raise Exception("Instance is non in active state")
            volume_details = volume_utils.volume_details(
                                   self.tenant_id, self.auth_token,
                                   volume_id)
            try:
                self.assertEqual(
                      instance_id,
                      volume_details["volume"]["attachments"][0]["server_id"],
                      "Instance id not found in volume details")
            except Exception as e:
                LOG.error(self.id() + " Instance id " +
                                      "not found in volume details")

        def test_13(self):
            """ Write data on bootable volume """
            image_id = image_utils.image_id(
                              self.tenant_id, self.auth_token,
                              config.image_name)
            content = volume_utils.volume_create(
                               self.tenant_id, self.auth_token,
                               config.bootable_volume_name,
                               config.bootable_volume_size_for_data,
                               image_id)
            volume_id = content["volume"]["id"]
            is_available = volume_utils.is_volume_available(
                                self.tenant_id, self.auth_token,
                                volume_id)
            self.assertEquals(True, is_available)
            content = volume_utils.volume_boot_attach_while_creating_instance(
                              self.tenant_id, self.auth_token, volume_id,
                              config.key_name,
                              config.instance_name,
                              config.flavor,
                              config.network, config.security_group)
            instance_id = instance_utils.instance_id(
                              self.tenant_id, self.auth_token,
                              config.instance_name)
            is_active = instance_utils.is_instance_active(
                              self.tenant_id, self.auth_token,
                              instance_id)
            if is_active is not True:
                LOG.error(self.id() + " Instance is non in active state")
                raise Exception("Instance is non in active state")
            volume_details = volume_utils.volume_details(
                                    self.tenant_id, self.auth_token,
                                    volume_id)
            if volume_details["volume"]["attachments"][0]["server_id"] != \
               instance_id:
                LOG.error(self.id() + " Instance id \
                          not found in volume details")
                raise Exception("Instance id not found in volume details")
            instance_ip = network_utils.floating_ip_associate(
                                     self.tenant_id, self.auth_token,
                                     "public", instance_id)
            time.sleep(30)
            size = config.volume_block_size
            count = config.count
            file_size = size*count
            try:
                data_volume.write_data_on_volume(
                        instance_ip, size, count, "/")
            except Exception as e:
                LOG.error(self.id() + str(e))
            time.sleep(30)
            try:
                value = data_volume.is_file_exists(
                             instance_ip, "/", file_size)
                print value
            except:
                try:
                    self.assertEqual(True, value,
                                     "File not found")
                except Exception as e:
                    LOG.error(self.id() + "File not found")
                    raise e

        def test_14(self):
            """ Data on volume persists when attached to different instance """
            instance_id = instance_utils.create_instance(
                                  self.tenant_id, self.auth_token,
                                  config.image_name, config.flavor,
                                  config.key_name, config.network,
                                  config.security_group, config.instance_name)
            volume_id = volume_utils.create_non_bootable_volume(
                                  self.tenant_id, self.auth_token,
                                  config.non_bootable_volume_name,
                                  config.non_bootable_volume_size)
            device = volume_utils.attach_volume(
                                  self.tenant_id,
                                  self.auth_token,
                                  instance_id,
                                  volume_id)
            instance_ip = network_utils.floating_ip_associate(
                                  self.tenant_id, self.auth_token,
                                  "public", instance_id)
            time.sleep(30)
            value = data_volume.create_filesystem(instance_ip,
                                                  device, "/mnt/temp")
            if value != "Filesystem Created":
                LOG.error(self.id() + "File system not created")
                raise Exception("File system not created")
            value = data_volume.mount_volume(
                         instance_ip, device, "/mnt/temp")
            if value != "Successfully mounted":
                LOG.error(self.id() + " Volume is not mounted successfully")
                raise Exception("Volume is not mounted successfully")
            size = config.volume_block_size
            count = config.count
            file_size = size*count
            data_volume.write_data_on_volume(
                    instance_ip, size, count, "/mnt/temp")
            value = data_volume.is_file_exists(
                         instance_ip, "/mnt/temp", file_size)
            if value is not True:
                LOG.error(self.id() + " File doesnot exists")
                raise Exception("File doesnot exists")
            value = data_volume.unmount_volume(instance_ip, "/mnt/temp")
            if value != "Successfully unmounted":
                LOG.error(self.id() + " Volume is not unmounted successfully")
                raise Exception("Volume is not unmounted successfully")
            value = instance_utils.instance_delete(
                             self.tenant_id, self.auth_token, instance_id)
            if value is True:
                LOG.error(self.id() + " Instance is not deleted successfully")
                raise Exception("Instance is not deleted successfully")
            instance_id = instance_utils.create_instance(
                                   self.tenant_id, self.auth_token,
                                   config.image_name, config.flavor,
                                   config.key_name, config.network,
                                   config.security_group, config.instance_name)
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
                LOG.error(self.id() + " Volume is not mounted successfully")
                raise Exception("Volume is not mounted successfully")
            value = data_volume.is_file_exists(
                           instance_ip, "/mnt/temp", file_size)
            try:
                self.assertEqual(True, value,
                                 "File doesnot exists")

            except Exception as e:
                LOG.error(self.id() + " File doesnot exists")
                raise e

        def test_15(self):
            """ Negative-Attach same
                non bootable volume to multiple instance
            """
            for i in range(1):
                instance_id = instance_utils.create_instance(
                                           self.tenant_id, self.auth_token,
                                           config.image_name, config.flavor,
                                           config.key_name, config.network,
                                           config.security_group,
                                           config.instance_name + str(i))
                if i == 0:
                    instance_1 = instance_id
                else:
                    instance_2 = instance_id
            volume_id = volume_utils.create_non_bootable_volume(
                                           self.tenant_id, self.auth_token,
                                           config.non_bootable_volume_name,
                                           config.non_bootable_volume_size)
            for instance_id in [instance_1, instance_1]:
                try:
                    device = volume_utils.attach_volume(
                                         self.tenant_id, self.auth_token,
                                         instance_id, volume_id)
                except Exception as e:
                    try:
                        self.assertIn("Invalid volume" and "in-use", str(e),
                                      "Exception not found")
                    except Exception as e:
                        LOG.error(self.id() + " Exception not found")
                        raise e

        def test_16(self):
            """ Detach non bootable volume from running instance """
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
                                   self.tenant_id,
                                   self.auth_token,
                                   instance_id,
                                   volume_id)
            value = volume_utils.detach_volume(
                                   self.tenant_id,
                                   self.auth_token,
                                   instance_id,
                                   volume_id)
            try:
                self.assertEqual(
                      True, value,
                      "Volume is not detached successfully")
            except Exception as e:
                LOG.error(self.id() + " Volume is " +
                                      "not detached successfully")
                raise e

        def test_17(self):
            """ Detach non bootable volume when instance is shut off """
            instance_id = instance_utils.create_instance(
                                    self.tenant_id, self.auth_token,
                                    config.image_name, config.flavor,
                                    config.key_name, config.network,
                                    config.security_group,
                                    config.instance_name)
            content = instance_utils.nova_stop_instance(
                                    self.tenant_id, self.auth_token,
                                    instance_id)
            time.sleep(10)
            instance_details = instance_utils.instance_details(
                                        self.tenant_id, self.auth_token,
                                        instance_id)
            while instance_details["server"]["OS-EXT-STS:task_state"] == \
                    "powering-off":
                time.sleep(5)
                instance_details = instance_utils.instance_details(
                                          self.tenant_id, self.auth_token,
                                          instance_id)
            self.assertEquals("SHUTOFF", instance_details["server"]["status"])
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
                LOG.error(self.id() + " Volume is not attached successfully")
                raise Exception("Volume is not attached successfully")
            value = volume_utils.detach_volume(
                                self.tenant_id, self.auth_token,
                                instance_id, volume_id)
            try:
                self.assertEqual(
                    True, value,
                    "Volume is not detached successfully")
            except Exception as e:
                LOG.error(self.id() + " Volume is not detached successfully")
                raise e

        def test_18(self):
            """ Detach boot volume when vm is shutoff """
            image_id = image_utils.image_id(
                            self.tenant_id, self.auth_token,
                            config.image_name)
            content = volume_utils.volume_create(
                            tenant_id=self.tenant_id,
                            auth_token=self.auth_token,
                            name=config.bootable_volume_name,
                            size=config.bootable_volume_size,
                            image_id=image_id)
            volume_id = content["volume"]["id"]
            is_available = volume_utils.is_volume_available(
                            self.tenant_id, self.auth_token,
                            volume_id)
            if is_available is not True:
                LOG.error(self.id() + " Volume is not in available state")
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
                LOG.error(self.id() + " Instance is not in active state")
                raise Exception("Instance is not in active state")
            volume_details = volume_utils.volume_details(
                                        self.tenant_id,
                                        self.auth_token,
                                        volume_id)
            if volume_details["volume"]["attachments"][0]["server_id"] != \
               instance_id:
                LOG.error(self.id() + " Instance " +
                                      "id not found in volume details")
                raise Exception("Instance id not found in volume details")
            content = instance_utils.nova_stop_instance(
                              self.tenant_id, self.auth_token, instance_id)
            time.sleep(10)
            instance_details = instance_utils.instance_details(
                                      self.tenant_id,
                                      self.auth_token,
                                      instance_id)
            while instance_details["server"]["OS-EXT-STS:task_state"] == \
                    "powering-off":
                time.sleep(5)
                instance_details = instance_utils.instance_details(
                                        self.tenant_id,
                                        self.auth_token,
                                        instance_id)
            if instance_details["server"]["status"] != "SHUTOFF":
                LOG.error(self.id() + " Instance is not in SHUTOFF state")
                raise Exception("Instance is not in SHUTOFF state")
            try:
                content = volume_utils.volume_detach(
                                 self.tenant_id,
                                 self.auth_token,
                                 instance_id, volume_id)
            except Exception as e:
                exception = "Can\\'t detach root device volume"
                try:
                    self.assertIn(
                       exception, str(e),
                       "Exception not found")
                except Exception as e:
                    LOG.error(self.id() + " Exception not found")
                    raise e

        def test_19(self):
            """ Detach boot volume from running instance """
            image_id = image_utils.image_id(
                               self.tenant_id,
                               self.auth_token,
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
                LOG.error(self.id() + " Volume is not in available state")
                raise Exception("Volume is not in available state")
            content = volume_utils.volume_boot_attach_while_creating_instance(
                                   self.tenant_id, self.auth_token,
                                   volume_id, config.key_name,
                                   config.instance_name,
                                   config.flavor, config.network,
                                   config.security_group)
            instance_id = instance_utils.instance_id(
                                    self.tenant_id, self.auth_token,
                                    config.instance_name)
            is_active = instance_utils.is_instance_active(
                                    self.tenant_id, self.auth_token,
                                    instance_id)
            if is_active is not True:
                LOG.error(self.id() + " Instance is not in active state")
                raise Exception("Instance is not in active state")
            volume_details = volume_utils.volume_details(
                                    self.tenant_id, self.auth_token, volume_id)
            if volume_details["volume"]["attachments"][0]["server_id"] != \
               instance_id:
                LOG.error(self.id() + " Instance id " +
                                      "not found in volume details")
                raise Exception("Instance id not found in volume details")
            try:
                content = volume_utils.volume_detach(
                                       self.tenant_id,
                                       self.auth_token,
                                       instance_id, volume_id)
            except Exception as e:
                exception = "Can\\'t detach root device volume"
                try:
                    self.assertIn(
                       exception, str(e),
                       "Exception not found")
                except Exception as e:
                    LOG.error(self.id() + "Exception not found")
                    raise e

        def tearDown(self):
            instances = instance_utils.instance_list(
                                self.tenant_id,
                                self.auth_token)
            if len(instances["servers"]) > 0:
                for instance in range(len(instances["servers"])):
                    instance_id = instances["servers"][instance]["id"]
                    value = instance_utils.instance_delete(
                                          self.tenant_id, self.auth_token,
                                          instance_id)
                    if value is True:
                        LOG.error(self.id() + " Instance not deleted")
                        raise Exception("Instance \
                                        not deleted")
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
            volumes = volume_utils.volume_list(self.tenant_id, self.auth_token)
            if len(volumes["volumes"]) > 0:
                for volume in range(len(volumes["volumes"])):
                    volume_id = volumes["volumes"][volume]["id"]
                    value = volume_utils.volume_delete(
                                   self.tenant_id, self.auth_token, volume_id)
                    if value is True:
                        LOG.error(self.id() + " Volume not deleted")
                        raise Exception("Volume not deleted")

    suite = unittest.TestLoader().loadTestsFromTestCase(Functional_tests)
    testResult = unittest.TextTestRunner(verbosity=2).run(suite)
    errors = testResult.errors
    failures = testResult.failures
    return errors, failures


if __name__ == "__main__":
    main()
