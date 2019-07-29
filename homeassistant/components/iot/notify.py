"""iot platform for notify component."""
import logging
import mimetypes
import yaml
import jwt
import time
import requests
import json

from jwt.contrib.algorithms.pycrypto import RSAAlgorithm
from Crypto.PublicKey import RSA

import voluptuous as vol

from homeassistant.const import CONF_FILE_PATH
import homeassistant.helpers.config_validation as cv

from homeassistant.components.notify import (
    ATTR_DATA, ATTR_TARGET, ATTR_TITLE, ATTR_TITLE_DEFAULT, PLATFORM_SCHEMA,
    BaseNotificationService)

_LOGGER = logging.getLogger(__name__)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_FILE_PATH): cv.string,
})


def get_service(hass, config, discovery_info=None):
    return IotNotificationService(config[CONF_FILE_PATH])

class IotNotificationService(BaseNotificationService):
    """Implement the notification service for iot."""

    def __init__(self, file_path):
        stream = open(file_path, "r")
        self.docs = yaml.safe_load(stream)
        self.url = "https://" + self.docs['iot']['host'] + ":" + str(self.docs['iot']['port']) + "/api/v1/update/" + self.docs['iot']['device']
        self.projectId = self.docs['iot']['project']
        self.deviceId = self.docs['iot']['device']
        key_file = open(self.docs['iot']['key'], "r")
        self.key = key_file.read()

    def send_message(self, message=None, **kwargs):
        payload = {
            "iat": int(time.time()),
            "exp": int(time.time()) + 120,
            "iss": "iot",
            "aud": self.projectId,
            "device": self.deviceId
        }
        jwt_token = jwt.encode(payload, bytes(self.key, encoding="utf-8"), algorithm='RS256')
        headers = {
            "X-ProjectId": self.docs['iot']['project'],
            "X-Key": str(jwt_token, encoding="utf-8"),
            "Content-type": "application/json",
            "Accept": "application/json"
        }
        data = json.loads(message)
        try:
            r = requests.post(self.url, json=data, headers=headers, verify=False)
        except requests.exceptions.Timeout as e:
            print(e)
        except requests.exceptions.TooManyRedirects as e:
            print(e)
        except requests.exceptions.RequestException as e:
            print(e)
        print(r)
