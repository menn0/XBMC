import xbmc, xbmcgui, xbmcaddon
import threading
import time
import socket
import json

from utilities import *

ABORT_REQUESTED = False

class ApiThread(threading.Thread):
    def __init__(self):
        super(ApiThread, self).__init__()
        self.sock = socket.socket()
        self.sock.settimeout(None)
        self.sock.connect(("localhost", 9090))
        # self.sock.connect(("localhost", get_api_port()))

    def process(self, data):
        pass

    def run(self):
        global ABORT_REQUESTED    
        while True:
            data = self.sock.recv(1024)
            xbmc.log('At {0}: {1}'.format(time.time(), str(data)))
            try:
                data_json = json.loads(str(data))
                method = data_json.get("method")

                API_CACHE = data_json.copy()
            except ValueError:
                continue

            if method == "System.OnQuit":
                ABORT_REQUESTED = True
                break
            else:
                self.process(data_json)


class Cache(object):
    """
    Library cache.
    """
    def __init__(self):
        super(Cache, self).__init__()
        self.hash_table = {}
        self.unhashed = {}
        self.parsed = True

    def rebuild():
        """
        If library cache is broken.
        """
        pass

    def get():
        """
        Get library cache object.
        """
        try:
            return json.loads(__addon__.getSetting("LIBRARY"))
        except ValueError, e:
            return None

    def save():
        """
        Save library from memory to file.
        """
        global LIBRARY_CACHE
        __addon__.setSetting(id="LIBRARY", value=LIBRARY_CACHE)

    def add(self, lib_id, lib_type, stv_id, hash, imdb = None):
        self.hash_table[hash] = {
            "id" : lib_id,
            "stvid" : stv_id,
            "type" : lib_type
        }
        if imdb:
            self.hash_table[hash] = imdb

    def get_hash_by_id(self, _id, _type):
        return [k for k, v in self.hash_table.iteritems() if v["id"] == _id and v["type"] == _type]

    def get_id_by_hash(self, _hash):
        return (self.hash_table[_hash]["id"], self.hash_table[_hash]["type"])

    def get_hash_by_stvid(self, stvid):
        return [k for k, v in self.hash_table.iteritems() if v["stvid"] == stvid]

    def get_stvid_by_hash(self, _hash):
        return self.hash_table[_hash]["stvid"]
 
    def get_id_by_stvid(self, stvid):
        return [(v["id"], v["type"]) for v in self.hash_table.values() if v["stvid"] == stvid]

    def get_stvid_by_id(self, _id, _type):
        return [v["stvid"] for v in self.hash_table.values() if v["id"] == _id and v["type"] == _type]


    def exists(self, _id = None, _type = None, stv_id = None, _hash = None):
        if _id and _type:
            rtrn = False
            for v in self.hash_table.values():
                if v["id"] == _id and v["type"] == _type:
                    rtrn = True
            return rtrn
        elif stv_id:
            rtrn = False
            for v in self.hash_table.values():
                if v["stvid"] == stvid:
                    rtrn = True
            return rtrn
        elif _hash:
            return self.hash_table.has_key(_hash)
        else:
            raise ValueError("Not enough parameters defined.")

    def delete(self, _id = None, _type = None, stv_id = None, _hash = None):
        if _id and _type:
            del self.hash_table[get_hash_by_id(_id, _type)]
        elif stv_id:
            del self.hash_table[get_hash_by_stvid(stv_id)]
        elif _hash:
            del self.hash_table[_hash]
        else:
            raise ValueError("Not enough parameters defined.")

    def list_all_ids(self):
        array = [(v["id"], v["type"]) for v in self.hash_table.values()]
        for i in array:
            count = array.count(i)
            if count > 1:
                for j in range(count-1):
                    array.remove(i)
        return array


CACHE = Cache()


class Library(ApiThread):
    """
    Just a Library.
    """
    def __init__(self):
        super(Library, self).__init__()

    def create(self):
        pass

    def read(self):
        pass

    def update(self):
        pass

    def delete(self):
        pass

    def addorupdate(self, _id, _type):
        print "{0}: {1}".format(_type, _id)
        if CACHE.exists( _id = _id, _type = _type):
            if _type == "movie":
                print get_movie_details(_id)
            elif _type == "episode":
                print get_episode_details(_id)
        else:
            if _type == "movie":
                movie = get_movie_details(_id)
                CACHE.add()
            elif _type == "episode":
                print get_episode_details(_id)

    def remove(self, _id, _type):
        pass

    def process(self, data):
        if "VideoLibrary" in data['method']:
            print data
            if data['method'] == 'VideoLibrary.OnUpdate':
                self.addorupdate(data['params']['data']['item']['id'], data['params']['data']['item']['type'])
            elif data['method'] == 'VideoLibrary.OnRemove':
                self.addorupdate(data['params']['data']['id'], data['params']['data']['type'])
