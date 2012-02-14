# -*- coding: utf-8 -*-
# Licensed under the MIT license.

import  urllib2
import json

from qbittorrentrpc.constants import DEFAULT_PORT, DEFAULT_TIMEOUT, LOGGER
from qbittorrentrpc.utils import id_generator

class Client(object):
    user = None
    password = None
    host = None
    port = None 
    headers = {}
    auth_header = None
    rcv_headers = None
    def __init__(self, host='localhost', port=DEFAULT_PORT, user=None, password=None, timeout=None):
        if isinstance(timeout, (int, long, float)):
            self._query_timeout = float(timeout)
        else:
            self._query_timeout = DEFAULT_TIMEOUT

        self.url = 'http://%s:%s' % (host, port)
        LOGGER.debug('Result url: %s' % self.url)
        
        self.user = user
        self.password = password
        self.host = host
        self.port = port

        if user and password:
            self.authenticate(self.url)
        else:
            LOGGER.warning('Either user or password missing, not using authentication.') 

    def authenticate(self, url):
        LOGGER.info('Setting authentification in host "%s" with user: %s and password: %s.' % (self.host, self.user, self.password))
        password_manager = urllib2.HTTPPasswordMgrWithDefaultRealm()
        password_manager.add_password(realm=None, uri=url, user=self.user, passwd=self.password)
        opener = urllib2.build_opener(
            urllib2.HTTPBasicAuthHandler(password_manager),
            urllib2.HTTPDigestAuthHandler(password_manager)
        )
        urllib2.install_opener(opener)
        urllib2.urlopen(url)
            
    def get_torrent_list(self):                                                  
        handle = urllib2.urlopen(self.url + '/json/events?noCache=' + id_generator())
        body = handle.read()
        torrent_list = json.loads(body)
        return torrent_list

    def get_torrent_count(self):
        return len(self.get_torrent_list())

    def get_downloading_torrent_list(self):
        torrents = self.get_torrent_list()
        dtorrents = []
        for torrent in torrents:
            if torrent['state'] == 'downloading':
                dtorrents.append(torrent)        
        return dtorrents

    def get_downloading_torrent_count(self):
        return len(self.get_downloading_torrent_list())

    def get_downloading_torrent_progress(self):
        torrents = self.get_downloading_torrent_list()
        if len(torrents) > 0:        
            total = 0;        
            for torrent in torrents:
                total += float(torrent['progress'])

            return total / len(torrents)

        return 0

    def resume_all(self):
        urllib2.urlopen(self.url + '/command/resumeall')
        
    def pause_all(self):
        urllib2.urlopen(self.url + '/command/pauseall')

    def all_paused(self):
        torrents = self.get_torrent_list()
        for torrent in torrents:
            if torrent['state'].count('paused') > 0:
                return True

        return False
        
        


                    
        
        
             
    

