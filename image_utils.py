"""

Reusable glance api calls

author: pandiselvi.rajangam@ril.com

"""

import common_utils


def image_id(tenant_id, auth_token, image_name):
    """
      Finds image_id address with instance name
      Return value : image_id
    """
    content = common_utils.do_request(
                  tenant_id, auth_token, method="GET",
                  body='',
                  service="glance", path="images")
    for image in content['images']:
        if image['name'] == image_name:
            return image['id']
    raise Exception('Cannot find image')
