"""

Reusable functions,common to all modules

author: pandiselvi.rajangam@ril.com

"""

import random
import httplib
import httplib2
import json
import config
import time


def do_request(tenant_id, auth_token, method, body='', service="", path=""):
    """
      Common method for all API calls
      Return value : content-Content of API Response
    """
    if service == "volumes":
        url = '%s%s/%s' % (config.volume_url, tenant_id, path)
    elif service == "glance":
        url = '%s%s' % (config.glance_url, path)
    elif service == "servers":
        url = '%s%s/%s' % (config.nova_url, tenant_id, path)
    elif service == "network":
        url = '%s%s' % (config.network_url, path)
    else:
        raise Exception("unknown service")

    conn = httplib2.Http(disable_ssl_certificate_validation=True)

    resp, content = conn.request(url, method, body,
                                 headers={"Content-Type": "application/json",
                                          "X-Auth-Token": auth_token})
    if int(resp['status']) in [200, 201, 202, 203, 204]:
        if content:
            content = json.loads(content)
        return content
    else:
        raise Exception('%s %s failed' % (method, url), body, resp, content)


def keystone_login(tenant, username, password):
    """
      Kesytone login
      Return values: tenant_id,auth_token
    """
    conn = httplib2.Http(disable_ssl_certificate_validation=True)
    url = '%s/v2.0/tokens' % ("http://127.0.0.1:5000")
    body = json.dumps({'auth':
                       {'tenantName': tenant,
                        'passwordCredentials': {'username': username,
                                                'password': password}}})
    resp, content = conn.request(url, 'POST', body,
                                 headers={"Content-Type": "application/json",
                                          "Content-Type": "application/json",
                                          "User-Agent": "python-cinderclient"})
    if resp['status'] == '200' and content:
        content = json.loads(content)
        return (content['access']['token']['tenant']['id'],
                content['access']['token']['id'])
    else:
        raise Exception('Keystone login POST %s failed' %
                        url, body, resp, content)


def random_pick(a_list):
    """
      Picks a random value
      in a list does not return the previous value
      Return value : value
    """
    previous_value = None
    while True:
        value = random.choice(a_list)
        if value != previous_value:
            yield value
            previous_value = value
