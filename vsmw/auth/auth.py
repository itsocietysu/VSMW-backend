#from each.auth.config import CONFIG, PROVIDER

import urllib.request
import json

#def Configure(**kwargs):
#    CONFIG.update(kwargs)

def Validate(url, token):
    try:
        response = urllib.request.urlopen('%s%s' % (url, token))
        certs = response.read().decode()
        json_load = json.loads(certs)
        return None, json_load['access_type'], json_load['email'], json_load['user_id'], json_load['name']
    except Exception as e:
        return str(e), None, None, None, None
