#!/usr/bin/env python3
#
#########################################################################
#  Copyright 2016 René Frieß                      rene.friess(a)gmail.com
#  Copyright of data provided by odlinfo.bfs.de API and retrieved by this
#  plugin see README.md
#  Version 1.1.1
#########################################################################
#
#  Plugin for the API of odlinfo.bfs.de, which allows to read values of
#  radioactive radiation within Germany.
#  This plugin only provides access to the API of ODLInfo and does not
#  modify that data, according to the ODLINFO Terms of Service.
#
#  For accessing the ODLINFO API you need a personal username and password.
#  For your own username and password register to the E-Mail provided in
#  https://odlinfo.bfs.de/DE/service/datenschnittstelle.html
#
#  This file is part of SmartHomeNG.
#
#  SmartHomeNG is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  SmartHomeNG is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with SmartHomeNG. If not, see <http://www.gnu.org/licenses/>.
#
#########################################################################

import logging
import requests
from lib.model.smartplugin import SmartPlugin
from requests.auth import HTTPBasicAuth
from .webif import WebInterface
import cherrypy

class ODLInfo(SmartPlugin):
    PLUGIN_VERSION = "1.5.0"
    _base_url = 'https://www.imis.bfs.de/ogc/opendata/ows'

    def __init__(self, sh, *args, **kwargs):
        """
        Initializes the plugin
        """
        # Call init code of parent class (SmartPlugin or MqttPlugin)
        super().__init__()

        self._session = requests.Session()
        if not self.init_webinterface(WebInterface):
            self._init_complete = False
        self._cycle = self.get_parameter_value('cycle')
        self._stations = []
        return

    def run(self):
        self.logger.debug("Run method called")
        self.scheduler_add('get_stations_from_odlinfo', self._get_stations, cycle=self._cycle)
        self.alive = True

    def stop(self):
        self.logger.debug("Stop method called")
        self.scheduler_remove('get_stations_from_odlinfo')
        self.alive = False

    def _get_stations(self):
        """
        Returns an array of dicts with information on all radiation measurement stations.
        """
        try:
            parameters = "service=WFS&version=1.1.0&request=GetFeature&typeName=opendata:odlinfo_odl_1h_latest&outputFormat=application/json&sortBy=plz"
            response = self._session.get(self._build_url(parameters))

        except Exception as e:
            self.logger.error(
                "Exception when sending GET request for _get_stations: %s" % str(e))
            return
        json_obj = response.json()
        self._stations = []
        for element in json_obj["features"]:
            self._stations.append(element['properties'])

        return stations

    def get_stations(self):
        if len(self._stations) == 0:
            self._get_stations()
        return self._stations

    def get_station_for_id(self, odlinfo_id):
        """
        Returns a dict of information for a radiation measurement station
        @param odlinfo_id: internal odlinfo_id
        """
        for element in self.get_stations():
            if odlinfo_id == element['kenn'] or odlinfo_id == element['id']:
                return element
        return None

    def get_stations_for_ids(self, odlinfo_ids):
        """
        Returns an array of dicts of information for multiple radiation measurement stations
        @param odlinfo_ids: array if internal odlinfo_ids
        """
        result_stations = []
        for result_station in self.get_stations():
            if (result_station['kenn'] in odlinfo_ids) or (result_station['id'] in odlinfo_ids):
                result_stations.append(result_station)
        return result_stations

    def _build_url(self, parameters=''):
        """
        Builds a request url, method included for a later use vs other data files of ODLINFO
        @return: string of the url
        """
        url = self._base_url
        if parameters != '':
            return "%s?%s" % (url, parameters)
        else:
            return url
