"""

Reusable nova functions

author: pandiselvi.rajangam@ril.com

"""

import time
import common_utils
import paramiko
import shlex
import image_utils
import network_utils


def instance_create(tenant_id, auth_token, server_name,
                    image_ref, flavor, key_name, network, security_group):
    """
      Creates an instance
      Return value : instance_id
    """
    net_id = network_utils.network_id(
                  tenant_id, auth_token, network)
    body = ('{"server": {"name": "%s", \
                         "imageRef": "%s", "key_name": "%s", \
                         "flavorRef": "%d", "max_count": 1, \
                         "min_count": 1, \
                         "networks": [{"uuid": "%s"}], \
                         "security_groups": [{"name": "%s"}]}}'
            % (server_name, image_ref,
               key_name, flavor, net_id,
               security_group))
    content = common_utils.do_request(
                    tenant_id, auth_token, method="POST",
                    body=body, service="servers", path="servers")
    return content['server']['id']


def instance_create_2(tenant_id, auth_token, volume_id,
                      server_name, flavor, delete="false"):
    """
      Creates an instance with delete option
      Return value : Content
    """
    content = common_utils.do_request(
                  tenant_id, auth_token,
                  method="POST",
                  body='{"server": {"name": "%s", \
                                    "imageRef": "", \
                                    "block_device_mapping_v2": \
                                    [{"source_type": "volume", \
                                      "delete_on_termination": "%s", \
                                      "boot_index": 0, "uuid": "%s", \
                                      "destination_type": "volume"}], \
                                    "flavorRef": "%s", "max_count": 1, \
                                    "min_count": 1}}'
                  % (server_name, delete, volume_id,
                     flavor),
                  service="servers", path="os-volumes_boot")
    return content


def is_instance_active(tenant_id, auth_token, instance_id):
    """
       Checks if an instance is active
       Return value : True if active,False if not active
    """
    content = common_utils.do_request(
                  tenant_id, auth_token, method='GET',
                  body='', service="servers", path='servers/%s' % instance_id)
    status = content['server']['status']
    while content['server']['status'] == 'BUILD':
        time.sleep(5)
        content = common_utils.do_request(
                    tenant_id, auth_token, method='GET',
                    body='', service="servers",
                    path='servers/%s' % instance_id)
    if content['server']['status'] == 'ACTIVE':
        return True
    elif content['server']['status'] == 'ERROR':
        details = instance_details(tenant_id, auth_token, instance_id)
        raise Exception('Instance went into ERROR state',
                        details['server']['fault'])
    else:
        return False


def instance_list(tenant_id, auth_token):
    """
      Lists all instances
      Return value: content-Content of API Response
    """
    content = common_utils.do_request(
                   tenant_id, auth_token, method="GET",
                   body='', service="servers", path="servers")
    return content


def instance_delete(tenant_id, auth_token, instance_id):
    """
      Deletes an instance
      Return value: True if instance found in instance list, \
      False if instance found in instance list
    """
    content = common_utils.do_request(
                     tenant_id, auth_token, method="DELETE",
                     body='', service="servers",
                     path="servers/%s" % (instance_id))

    try:
        details = instance_details(tenant_id, auth_token, instance_id)
        if details["server"]["status"] == "ACTIVE" or "SHUTOFF":
            time.sleep(60)
            details = instance_details(tenant_id, auth_token, instance_id)
        while details["server"]["status"] == "deleting":
            time.sleep(5)
            details = instance_details(tenant_id, auth_token, instance_id)
    except Exception as e:
        if "Instance %s could not be found" % instance_id in str(e):
            return False
    instances = instance_list(tenant_id, auth_token)
    for instance in range(len(instances)):
        if instances["servers"][instance]["id"] == instance_id:
            return True


def instance_ip_address(tenant_id, auth_token, instance_id):
    """
      Finds instance ip address with instance name
      Return value : ip_address
    """
    content = common_utils.do_request(
                  tenant_id, auth_token, method='GET',
                  body='', service="servers",
                  path='servers/%s' % instance_id)
    ip_address = content['server']['addresses']['private'][1]['addr']
    return ip_address


def instance_details(tenant_id, auth_token, instance_id):
    """
      Gets details of an instance
      Return value: content-Content of API Response
    """
    content = common_utils.do_request(
                  tenant_id, auth_token, method='GET',
                  body='', service="servers",
                  path='servers/%s' % instance_id)
    return content


def instance_id(tenant_id, auth_token, instance_name):
    """
      Finds instance_id address with instance name
      Return value : instance_id
    """
    content = common_utils.do_request(
                  tenant_id, auth_token, method='GET',
                  body='', service="servers", path='servers')
    for instance in content['servers']:
        if instance['name'] == instance_name:
            return instance['id']
    raise Exception('Cannot find server')


def nova_stop_instance(tenant_id, auth_token, instance_name):
    """
      Stops an instance
      Return value : content-Content of API Response
    """
    content = common_utils.do_request(
                          tenant_id, auth_token,
                          method='POST',
                          body='{"os-stop": null}',
                          service="servers",
                          path='servers/%s/action' % instance_name)
    return content


def nova_start_instance(tenant_id, auth_token, instance_name):
    """
      Starts an instance
      Return value : content-Content of API Response
    """
    content = common_utils.do_request(
                  tenant_id, auth_token, method='POST',
                  body='{"os-start": null}', service="servers",
                  path='servers/%s/action' % instance_name)
    return content


def instance_mac_id_fixed(tenant_id, auth_token, instance_id):
    """
       Finds the mac_id for an instance
       Return value : mac_id
    """
    content = instance_details(tenant_id, auth_token, instance_id)
    for ip in range(len(content["server"]["addresses"]["private"])):
        if content["server"]["addresses"]["private"][ip]["OS-" +
                                                         "EXT-IPS:type"] \
                                                         == "fixed":
            mac_id = content["server"]["addresses"][
                "private"][ip]["OS-EXT-IPS-MAC:mac_addr"]
            return mac_id


def instance_port_id(tenant_id, auth_token, instance_id):
    """
      Finds the port_id for an instance
      Return value : port_id
    """
    content = common_utils.do_request(
                  tenant_id, auth_token, method='GET', body='',
                  service="network",
                  path='ports.json?device_id=%s' % instance_id)
    instance_mac_id = instance_mac_id_fixed(tenant_id, auth_token, instance_id)
    for port in range(len(content["ports"])):
        if content["ports"][port]["mac_address"] == instance_mac_id:
            port_id = content["ports"][port]["id"]
            return port_id


def create_instance(tenant_id, auth_token, image_name,
                    flavor, key_name, network,
                    security_group, instance_name):
    """
      Create an instance
      Return value : instance_id
    """
    image_id = image_utils.image_id(
                           tenant_id, auth_token, image_name)
    content = instance_create(
                           tenant_id, auth_token, instance_name,
                           image_id, flavor, key_name, network,
                           security_group)
    inst_id = instance_id(tenant_id, auth_token, instance_name)
    is_active = is_instance_active(tenant_id, auth_token, inst_id)
    if is_active is True:
        return inst_id
    else:
        raise Exception("Instance is not in active state")
