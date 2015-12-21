"""

Reusable cinder functions

author: pandiselvi.rajangam@ril.com

"""

import common_utils
import time
import config
import network_utils
import image_utils


def volume_create(tenant_id, auth_token, name, size, image_id=''):
    """
      Creates bootable or non bootable volume w.r.t image_id parameter
      Return value: content-Content of API response
    """
    if image_id:
        content = common_utils.do_request(
                      tenant_id, auth_token,
                      method="POST",
                      body='{"volume": {"name": "%s", "size": "%s",\
                                         "image_id": "%s"}}'
                      % (name, size, image_id),
                      service="volumes",
                      path="volumes")
        return content
    else:
        content = common_utils.do_request(
                       tenant_id, auth_token,
                       method="POST",
                       body='{"volume":{"name": "%s", "size": "%s"}}'
                       % (name, size),
                       service="volumes", path="volumes")
    return content


def volume_create_while_creating_instance(
        tenant_id, auth_token, image_id, size,
        key_name, instance_name, flavor, network,
        security_group, delete="false"):
    """
      Creates bootable volume while creating instance
      Return value: content-Content of API response
    """
    net_id = network_utils.network_id(tenant_id, auth_token, network)
    content = common_utils.do_request(
                  tenant_id, auth_token,
                  method="POST",
                  body='{"server": {"name": "%s", "imageRef": "", \
                                    "block_device_mapping_v2": \
                                    [{"boot_index": "0", "uuid": "%s", \
                                      "volume_size": "%s", \
                                      "source_type": "image", \
                                      "destination_type": "volume", \
                                      "delete_on_termination": "%r"}], \
                                    "key_name": "%s", \
                                    "flavorRef": "%s", "max_count": 1, \
                                    "min_count": 1, \
                                    "networks": [{"uuid": "%s"}], \
                                    "security_groups": [{"name": "%s"}]}}'
                  % (instance_name, image_id,
                     size, delete, key_name,
                     flavor, net_id, security_group),
                  service="servers",
                  path="os-volumes_boot")
    return content


def volume_boot_attach_while_creating_instance(
        tenant_id, auth_token, volume_id, key_name, instance_name,
        flavor, network, security_group, delete="false"):
    """
      Creates instance with bootable volume
      Return value: content-Content of API response
    """
    net_id = network_utils.network_id(tenant_id, auth_token, network)
    content = common_utils.do_request(
                 tenant_id, auth_token,
                 method="POST",
                 body='{"server": {"name": "%s", "imageRef": "", \
                                   "block_device_mapping_v2": \
                                   [{"source_type": "volume", \
                                     "delete_on_termination": "%s", \
                                     "boot_index": 0, "uuid": "%s", \
                                     "destination_type": "volume"}], \
                                   "key_name": "%s", "flavorRef": "%s", \
                                   "max_count": 1, "min_count": 1, \
                                   "networks": [{"uuid": "%s"}], \
                                   "security_groups": [{"name": "%s"}]}}'
                 % (instance_name, delete, volume_id,
                    key_name, flavor, net_id, security_group),
                 service="servers", path="os-volumes_boot")
    return content


def volume_attach_while_creating_instance(
        tenant_id, auth_token, image_id, volume_id, key_name,
        instance_name, flavor, network, security_group, delete="false"):
    """
      Creates instance with non bootable volume attached
      Return value: content-Content of API response
    """
    net_id = network_utils.network_id(tenant_id, auth_token, network)
    content = common_utils.do_request(
                  tenant_id, auth_token,
                  method="POST",
                  body='{"server": {"name": "%s", \
                                    "imageRef": "%s", \
                                    "block_device_mapping_v2": \
                                    [{"boot_index": "0", "uuid": "%s", \
                                      "source_type": "volume", \
                                      "destination_type": "volume", \
                                      "delete_on_termination": "%s"}], \
                                    "key_name": "%s", \
                                    "flavorRef": "%s", "max_count": 1, \
                                    "min_count": 1, \
                                    "networks": [{"uuid": "%s"}], \
                                    "security_groups": [{"name": "%s"}]}}'
                  % (instance_name, image_id, volume_id,
                     delete, key_name, flavor, net_id,
                     security_group),
                  service="servers",
                  path="os-volumes_boot")
    return content


def is_volume_available(tenant_id, auth_token, volume_id):
    """
      Checks if a volume is in available state
      Return volume: True if available,volume_status if not available
    """
    content = volume_details(tenant_id, auth_token, volume_id)
    while content["volume"]["status"] == "creating" or \
        content["volume"]["status"] == "downloading" or \
        content["volume"]["status"] == "restoring-backup" or \
        content["volume"]["status"] == "extending" or \
            content["volume"]["status"] == "uploading":
                time.sleep(5)
                content = volume_details(tenant_id, auth_token, volume_id)
    if content["volume"]["status"] == "available":
        return True
    else:
        return content["volume"]["status"]


def volume_details(tenant_id, auth_token, volume_id):
    """
      Returns details of a volume
      Return value: content-Content of API response
    """
    content = common_utils.do_request(
                  tenant_id, auth_token, method="GET",
                  body='', service="volumes",
                  path="volumes/%s" % (volume_id))
    return content


def volume_list(tenant_id, auth_token):
    """
      Returns list of volumes
      Return value: content-Content of API response
    """
    content = common_utils.do_request(
                  tenant_id, auth_token, method="GET",
                  body='', service="volumes", path="volumes")
    return content


def volume_attach(tenant_id, auth_token, server_id, volume_id, device=''):
    """
      Attaches volume to an instance
      Return value: content-Content of API response
    """
    content = common_utils.do_request(
                  tenant_id, auth_token,
                  method="POST",
                  body='{"volumeAttachment": \
                         {"device": "%s", "volumeId": "%s"}}'
                  % (device, volume_id),
                  service="servers",
                  path="servers/%s/os-volume_attachments" % server_id)
    return content


def volume_detach(tenant_id, auth_token, server_id, volume_id):
    """
      Detaches volume to an instance
      Return value: content-Content of API response
    """
    content = common_utils.do_request(
                  tenant_id, auth_token,
                  method="DELETE", body='',
                  service="servers",
                  path="servers/%s/os-volume_attachments/%s"
                  % (server_id, volume_id))
    return content


def volume_delete(tenant_id, auth_token, volume_id):
    """
      Deletes a volume
      Return value: True-if not deleted,
      False-if deleted
    """
    content = common_utils.do_request(
                  tenant_id, auth_token, method="DELETE",
                  body='', service="volumes",
                  path="volumes/%s" % (volume_id))

    try:
        details = volume_details(tenant_id, auth_token, volume_id)
        if details["volume"]["status"] == "in-use" or \
           details["volume"]["status"] == "available" or \
           details["volume"]["status"] == "extending" or \
           details["volume"]["status"] == "uploading":
            time.sleep(60)
        while details["volume"]["status"] == "deleting":
            time.sleep(5)
            details = volume_details(tenant_id, auth_token, volume_id)

    except Exception as e:
        if "Volume could not be found" in str(e):
            return False
    volumes = volume_list(self.tenant_id, self.auth_token)
    for volume in range(len(volumes["volumes"])):
        if content["volumes"][volume]["id"] == volume_id:
            return True


def create_non_bootable_volume(tenant_id, auth_token, name, size):
    """
      Creates non bootable volume
      Return value : volume_id
    """
    content = volume_create(tenant_id,
                            auth_token, name, size)
    volume_id = content["volume"]["id"]
    is_available = is_volume_available(
                       tenant_id, auth_token, volume_id)
    if is_available is True:
        return volume_id
    else:
        raise Exception("volume is not in available state")


def create_bootable_volume(tenant_id, auth_token, name, size, image_name):
    """
      Creates bootable volume
      Return value : volume_id
    """
    image_id = image_utils.image_id(tenant_id, auth_token, image_name)
    content = volume_create(tenant_id,
                            auth_token, name, size, image_id)
    volume_id = content["volume"]["id"]
    is_available = is_volume_available(tenant_id,
                                       auth_token, volume_id)
    if is_available is True:
        return volume_id
    else:
        raise Exception("volume is not in available state")


def attach_volume(tenant_id, auth_token, instance_id, volume_id):
    """
      Attaches volume to an instance
      Return value : device - if successfully attached,
      0 - if failed to attach
    """
    content = volume_attach(tenant_id, auth_token, instance_id, volume_id)
    assert content["volumeAttachment"]["serverId"] == instance_id, \
        "Instance id not found in volume attachments"
    details = volume_details(tenant_id, auth_token, volume_id)
    while details["volume"]["status"] == "attaching":
        time.sleep(5)
        details = volume_details(tenant_id, auth_token, volume_id)
    if details["volume"]["status"] == "in-use":
        pass
    else:
        raise Exception("Volume is not in in-use state")
    for instance in range(len(details["volume"]["attachments"])):
        attachments = details["volume"]["attachments"]
        inst = attachments[instance]
        if inst["server_id"] == instance_id:
            device = details["volume"]["attachments"][instance]["device"]
            return device
        else:
            return 0


def detach_volume(tenant_id, auth_token, instance_id, volume_id):
    """
      Detaches volume
      Return value : True - if available after detach,
      False - if not available
    """
    content = volume_detach(tenant_id, auth_token, instance_id, volume_id)
    content = volume_details(tenant_id, auth_token, volume_id)
    while content["volume"]["status"] == "detaching":
        time.sleep(5)
        content = volume_details(tenant_id, auth_token, volume_id)
    if content["volume"]["status"] == "available":
        return True
    else:
        raise False
