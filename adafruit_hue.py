# The MIT License (MIT)
#
# Copyright (c) 2019 Brent Rubell for Adafruit Industries
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
"""
`adafruit_hue`
================================================================================

CircuitPython helper library for the Philips Hue

* Author(s): Brent Rubell

Implementation Notes
--------------------

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://github.com/adafruit/circuitpython/releases

* Adafruit ESP32SPI or ESP_ATcontrol library:
    https://github.com/adafruit/Adafruit_CircuitPython_ESP32SPI
    https://github.com/adafruit/Adafruit_CircuitPython_ESP_ATcontrol
"""
import time
from random import randint

__version__ = "0.0.0-auto.0"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_Hue.git"

class Bridge:
    """
    HTTP Interface for interacting with a Philips Hue Bridge.
    """
    def __init__(self, wifi_manager, bridge_ip=None, username=None):
        """
        Creates an instance of the Philips Hue Bridge Interface.
        :param wifi_manager wifi_manager: WiFiManager from ESPSPI_WiFiManager/ESPAT_WiFiManager
        """
        wifi_type = str(type(wifi_manager))
        if ('ESPSPI_WiFiManager' in wifi_type or 'ESPAT_WiFiManager' in wifi_type):
            self._wifi = wifi_manager
        else:
            raise TypeError("This library requires a WiFiManager object.")
        if bridge_ip and username is not None:
            self._bridge_url = 'http://{}/api'.format(bridge_ip)
            self._username_url = self._bridge_url+'/'+ username
        else:
            self._bridge_ip = self.discover_bridge()
            self._username = self.register_username()
            raise AssertionError('ADD THESE VALUES TO SECRETS.PY: \
                                 \n\t"bridge_ip":"{0}", \
                                 \n\t"username":"{1}"'.format(self._bridge_ip, self._username))

    def discover_bridge(self):
        """Discovers Philips Hue Bridge IP from the hosted broker discovery service.
        Returns the bridge's IP address.
        """
        try:
            resp = self._wifi.get('https://discovery.meethue.com')
            json_data = resp.json()
            bridge_ip = json_data[0]['internalipaddress']
            resp.close()
        except:
            raise TypeError('Ensure the Philips Bridge and CircuitPython device are both on the same WiFi network.')
        self._ip = bridge_ip
        # set up hue bridge address path
        self.bridge_url = 'http://{}/api'.format(self._ip)
        return self._ip

    def register_username(self):
        """Attempts to register a Hue application username for use with your bridge.
        Provides a 30 second delay to press the link button on the bridge.
        Returns username or None.
        """
        self._bridge_url = 'http://{}/api'.format(self._bridge_ip)
        data = {"devicetype":"CircuitPython#pyportal{0}".format(randint(0,100))}
        resp = self._wifi.post(self._bridge_url,json=data)
        connection_attempts = 30
        username = None
        while username == None and connection_attempts > 0:
            resp = self._wifi.post(self._bridge_url, json=data)
            json = resp.json()[0]
            if json.get('success'):
                username = str(json['success']['username'])
                self._username_url = self._bridge_url+'/'+ username
            connection_attempts-=1
            time.sleep(1)
        resp.close()
        return username

    # Lights API
    def show_light_info(self, light_id):
        """Gets the attributes and state of a given light.
        :param int light_id: Light identifier.
        """
        resp = self._get('{0}/lights/{1}'.format(self._username_url, light_id))
        resp_json = resp.json()
        resp.close()
        return resp_json

    def set_light(self, light_id, **kwargs):
        """Allows the user to turn the light on and off, modify the hue and effects.
        You can pass the following as valid kwargs into this method:
        :param bool on: On/Off state of the light
        :param int bri: Brightness value of the light (1 to 254)
        :param int hue: Hue value to set the light to (0 to 65535)
        :param int sat: Saturation of the light (0 to 254)
        (more settings at https://developers.meethue.com/develop/hue-api/lights-api/#set-light-state)
        """
        resp = self._put('{0}/lights/{1}/state'.format(self._username_url, light_id), kwargs)
        resp_json = resp.json()
        resp.close()
        return resp_json

    def get_light(self, light_id):
        """Gets the attributes and state of a provided light.
        :param int light_id: Light identifier.
        """
        resp = self._get('{0}/lights/{1}'.format(self._username_url, light_id))
        resp_json = resp.json()
        resp.close()
        return resp_json

    def get_lights(self):
        """Returns all the light resources available for a bridge.
        """
        resp = self._get(self._username_url+'/lights')
        resp_json = resp.json()
        resp.close()
        return resp_json

    # Groups API
    def create_group(self, lights, group_id):
        """Creates a new group containing the lights specified and optional name.
        :param list lights: List of light identifiers.
        :param str group_id: Optional group name.
        """
        data = {'lights':lights,
                'name':group_id,
                'type':lightGroup
        }
        resp = self._post(self._username_url+'/groups', data)
        resp_json = resp.json()
        resp.close()
        return resp_json

    def set_group(self, group_id, **kwargs):
        """Allows the user to turn the light on and off, modify the hue and effects.
        :param int group_id: Group identifier.
        You can pass the following as (optional) valid kwargs into this method:
        :param bool on: On/Off state of the light
        :param int bri: Brightness value of the light (1 to 254)
        :param int hue: Hue value to set the light to (0 to 65535)
        :param int sat: Saturation of the light (0 to 254)
        (more settings at https://developers.meethue.com/develop/hue-api/lights-api/#set-light-state)
        """
        print(kwargs)
        resp = self._put('{0}/groups/{1}/action'.format(self._username_url, group_id), kwargs)
        resp_json = resp.json()
        resp.close()
        return resp_json

    def get_groups(self):
        """Returns all the light groups available for a bridge.
        """
        resp = self._get(self._username_url+'/groups')
        resp_json = resp.json()
        resp.close()
        return resp_json

    # Scene API
    def set_scene(self, group_id, scene_id):
        """Sets a group scene.
        :param str scene: The scene identifier
        """
        # To recall an existing scene, use the Groups API.
        self.set_group(group_id, scene=scene_id)

    def get_scenes(self):
        """Returns a list of all scenes currently stored in the bridge. 
        """
        resp = self._get(self._username_url+'/scenes')
        resp_json = resp.json()
        resp.close()
        return resp_json

    # HTTP Helpers for the Hue API
    def _post(self, path, data):
        """POST data
        :param str path: Formatted Hue API URL
        :param json data: JSON data to POST to the Hue API.
        """
        response = self._wifi.post(
            path,
            json=data
        )
        return response

    def _put(self, path, data):
        """PUT data
        :param str path: Formatted Hue API URL
        :param json data: JSON data to PUT to the Hue API.
        """
        response = self._wifi.put(
            path,
            json=data
        )
        return response

    def _get(self, path, data=None):
        """GET data
        :param str path: Formatted Hue API URL
        :param json data: JSON data to GET from the Hue API.
        """
        response = self._wifi.get(
            path,
            json=data
        )
        return response