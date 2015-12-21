"""

Reusable network functions

author: pandiselvi.rajangam@ril.com

"""

import json
import common_utils
import instance_utils
import volume_utils
import image_utils


def floating_ip_associate(tenant_id, auth_token, network, instance_id):
    """
       Associates floating ip to an instance
       Return value : floating_ip
    """
    port_id = instance_utils.instance_port_id(
                      tenant_id, auth_token, instance_id)
    floating_ip_id = floating_ip_create(tenant_id, auth_token, network)
    content = common_utils.do_request(
                     tenant_id, auth_token, method='PUT',
                     body='{"floatingip": {"port_id": "%s"}}'
                     % port_id, service="network", path='floatingips/%s.json'
                     % floating_ip_id)
    if content["floatingip"]["port_id"] == port_id:
        floating_ip = content["floatingip"]["floating_ip_address"]
        return floating_ip


def network_id(tenant_id, auth_token, network_name):
    """
      Finds the network_id for a network
      Return value : network_id
    """
    content = common_utils.do_request(
                         tenant_id, auth_token,
                         method='GET',
                         body='', service="network",
                         path='networks.json')
    for network in range(len(content["networks"])):
        if content["networks"][network]["name"] == network_name:
            network_id = content["networks"][network]["id"]
            return network_id


def floating_ip_create(tenant_id, auth_token, network):
    """
      Creates a floating ip
      Return value : floatingip_id
    """
    net_id = network_id(tenant_id, auth_token, network)
    content = common_utils.do_request(
                        tenant_id, auth_token,
                        method='POST',
                        body='{"floatingip": {"floating_network_id": "%s"}}'
                        % net_id, service="network",
                        path='floatingips.json')
    floatingip_id = content['floatingip']["id"]
    return floatingip_id


def floating_ip_delete(tenant_id, auth_token, floating_ip_id):
    """
      Deletes a floating ip
      Return value: True is not deleted,False if deleted
    """
    content = common_utils.do_request(
                          tenant_id, auth_token,
                          method='DELETE',
                          body='',
                          service="network",
                          path="floatingips/%s"
                          % floating_ip_id)
    ip_list = floating_ip_list(tenant_id, auth_token)
    for ip in range(len(ip_list["floatingips"])):
        if ip_list["floatingips"][ip]["id"] == floating_ip_id:
            return True
        else:
            return False


def floating_ip_list(tenant_id, auth_token):
    """
      Lists all floating ips
      Return value : content-Content of API response
    """
    content = common_utils.do_request(
                     tenant_id, auth_token,
                     method='GET',
                     body='',
                     service="network",
                     path="floatingips.json")
    return content
