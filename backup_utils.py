"""

Reusable backup functions

author: pandiselvi.rajangam@ril.com

"""


import volume_utils
import image_utils
import network_utils
import common_utils
import time


def backup_create(tenant_id, auth_token, volume_id, name):
    """
      Creates a backup for volume
      Return value: content-Content of API response
    """
    content = common_utils.do_request(
                  tenant_id, auth_token,
                  method="POST",
                  body='{"backup": {"description": null, \
                                    "container": null, \
                                    "name": "%s", \
                                    "volume_id": "%s"}}'
                  % (name, volume_id),
                  service="volumes", path="backups")
    return content


def is_backup_available(tenant_id, auth_token, backup_id):
    """
      Checks if a backup is in available state
      Return value : True if available ,False if not available
    """
    content = backup_details(tenant_id, auth_token, backup_id)
    while content["backup"]["status"] == "creating":
        time.sleep(5)
        content = backup_details(tenant_id, auth_token, backup_id)
    if content["backup"]["status"] == "available":
        return True
    else:
        return False


def backup_restore(tenant_id, auth_token, backup_id, volume_id="null"):
    """
      Restores a backup
      Return value: content-Content of API Response
    """
    content = common_utils.do_request(
                  tenant_id, auth_token,
                  method="POST",
                  body='{"restore":{"volume_id": %s}}'
                  % (volume_id),
                  service="volumes",
                  path="backups/%s/restore" % (backup_id))
    return content


def backup_list(tenant_id, auth_token):
    """
      Lists all backups
      Return value: content-Content of API Response
    """
    content = common_utils.do_request(
                   tenant_id, auth_token,
                   method="GET",
                   body='', service="volumes",
                   path="backups")
    return content


def backup_delete(tenant_id, auth_token, backup_id):
    """
      Deletes a backup
      Return value: True if backup still exists, False if deleted
    """
    content = common_utils.do_request(
                  tenant_id, auth_token,
                  method="DELETE",
                  body='', service="volumes",
                  path="backups/%s" % (backup_id))
    try:
        details = backup_details(tenant_id, auth_token, backup_id)
        while details["backup"]["status"] == "deleting":
            time.sleep(5)
            details = backup_details(tenant_id, auth_token, backup_id)
    except Exception as e:
        if "Backup %s could not be found" % backup_id in str(e):
            return False
    backups = backup_list(tenant_id, auth_token)
    for backup in range(len(backups)):
        if backups["backups"][backup]["id"] == backup_id:
            return True


def backup_details(tenant_id, auth_token, backup_id):
    """
      Gets details of a  backup
      Return value: content-Content of API Response
    """
    content = common_utils.do_request(
                  tenant_id, auth_token, method='GET',
                  body='',
                  service="volumes",
                  path='backups/%s' % backup_id)
    return content


def create_backup(tenant_id, auth_token, volume_id, backup_name):
    """
      Creates a backup
      Return value : backup_id
    """
    content = backup_create(
                      tenant_id, auth_token,
                      volume_id, backup_name)
    backup_id = content["backup"]["id"]
    time.sleep(10)
    is_available = is_backup_available(
                            tenant_id, auth_token, backup_id)
    if is_available is True:
        pass
    else:
        raise Exception("Backup creation failed")
    details = backup_details(tenant_id, auth_token, backup_id)
    if details["backup"]["volume_id"] == volume_id:
        return backup_id
    else:
        return 0


def restore_backup(tenant_id, auth_token, backup_id):
    """
      Restores  backup
      Return value : volume_id
    """
    content = backup_restore(tenant_id, auth_token, backup_id)
    volume_id = content["restore"]["volume_id"]
    is_available = volume_utils.is_volume_available(
                                       tenant_id, auth_token,
                                       volume_id)
    if is_available is True:
        return volume_id
    else:
        return 0
