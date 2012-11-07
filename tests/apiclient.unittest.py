import os, sys
import unittest
import logging
import json
from copy import copy

sys.path.insert(0, os.path.abspath('..'))
from apiclient import *

def pprint(data):
	global logger

	if data is dict and data.has_key('_db_queries'):
		del data['_db_queries']
	msg = json.dumps(data, indent=4)
	# print msg
	logger.debug(msg)


class ApiTest(unittest.TestCase):
	def test_auth(self):
		global connection

		c = connection		
		client = ApiClient(c['base_url'], c['key'], c['secret'], c['username'], c['password'], c['device_id'], debugLvl = logging.WARNING, rel_api_url=c['rel_api_url'])
		client.getAccessToken()
		self.assertIsInstance(client, ApiClient)
		return client

	def test_auth_fail(self):
		global connection

		c = copy(connection)
		c['password'] = 'aax'		# bad password
		client = ApiClient(c['base_url'], c['key'], c['secret'], c['username'], c['password'], c['device_id'], debugLvl=logging.WARNING, rel_api_url=c['rel_api_url'])
		
		self.assertRaises(AuthenticationError, client.getAccessToken)
		self.assertTrue(client.isAuthenticated()==False)

	def test_unwatched_episodes(self):
		global connection

		c = copy(connection)
		client = ApiClient(c['base_url'], c['key'], c['secret'], c['username'], c['password'], c['device_id'], debugLvl=logging.WARNING, rel_api_url=c['rel_api_url'])
		data = client.unwatchedEpisodes()

		self.assertTrue(data.has_key('lineup'))
		self.assertTrue(data.has_key('new'))
		self.assertTrue(data.has_key('top'))
		self.assertTrue(data.has_key('upcoming'))

	def test_library_add(self):
		global connection

		c = connection		
		client = ApiClient(c['base_url'], c['key'], c['secret'], c['username'], c['password'], c['device_id'], debugLvl=logging.WARNING, rel_api_url=c['rel_api_url'])
		client.getAccessToken()

		# 60569 "Malcolm X"
		data = client.titleIdentify(imdb_id=60569, stv_title_hash='')

		stv_title_id = data['title_id']

		data = client.libraryTitleAdd(stv_title_id)

		exampleEvents = [
			{
			    "event": "start", 
			    "timestamp": '2012-10-08 16:54:34', 
			    "position": 1222
			}, 
			{
			    "event": "pause", 
			    "timestamp": '2012-10-08 16:54:40', 
			    "position": 1359
			}, 
			{
			    "event": "resume", 
			    "timestamp": '2012-10-08 16:55:10', 
			    "position": 1359
			}, 
			{
			    "event": "stop", 
			    "timestamp": '2012-10-08 16:55:15', 
			    "position": 1460
			},
		]

		#exampleEvents = []

		watched_data = {
			'rating': 1, 
			'player_events': json.dumps(exampleEvents)
		}

		data = client.titleWatched(stv_title_id, **watched_data)

		data = client.libraryTitleRemove(stv_title_id)

	def test_profile_recco(self):
		global connection

		c = connection		
		client = ApiClient(c['base_url'], c['key'], c['secret'], c['username'], c['password'], c['device_id'], debugLvl=logging.WARNING, rel_api_url=c['rel_api_url'])

		props = [ 'year', 'cover_small' ]
		data = client.profileRecco('movie', False, props)

		self.assertTrue(data.has_key('recco_id'))
		self.assertTrue(data.has_key('titles'))
		self.assertTrue(len(data['titles']) > 0)

	def test_profile_recco_local(self):
		global connection

		c = connection		
		client = ApiClient(c['base_url'], c['key'], c['secret'], c['username'], c['password'], c['device_id'], debugLvl=logging.WARNING, rel_api_url=c['rel_api_url'])

		props = [ 'year', 'cover_small' ]
		data = client.profileRecco('movie', True, props)

		self.assertTrue(data.has_key('recco_id'))
		self.assertTrue(data.has_key('titles'))
		self.assertTrue(len(data['titles']) > 0)


	def test_title_similar(self):
		c = connection		
		client = ApiClient(c['base_url'], c['key'], c['secret'], c['username'], c['password'], c['device_id'], debugLvl=logging.WARNING, rel_api_url=c['rel_api_url'])

		# 1947362 "Ben-Hur (1959)"
		data_similar = client.titleSimilar(1947362)
		self.assertTrue(data_similar.has_key('recco_id'))
		self.assertTrue(data_similar.has_key('titles'))
		self.assertTrue(len(data_similar['titles']) > 0)

	def test_title(self):
		c = connection		
		client = ApiClient(c['base_url'], c['key'], c['secret'], c['username'], c['password'], c['device_id'], debugLvl=logging.WARNING, rel_api_url=c['rel_api_url'])
		title = client.title(1947362)
		self.assertTrue(title.has_key('cover_full'))
		self.assertTrue(title.has_key('genres'))



if __name__ == '__main__': 
	connection = {
		'base_url': 'http://test.papi.synopsi.tv/',
		'key': 'e20e8f465f42e96d8340e81bfc48c757',
		'secret': '72ab379c50650f7aec044b14db306430a55f09a2da1eb8e40b297a54b30e4b4f',
		'rel_api_url': '1.0/',
		# 'base_url': 'http://neptune.local:8000/',
		# 'key': '76ccb5ec8ecddf15c29c5decac35f9',
		# 'secret': '261029dbbdd5dd481da6564fa1054e',
		# 'rel_api_url': 'api/public/1.0/',
		'username': 'martin.smid@gmail.com',
		'password': 'aaa',
		'device_id': '7caa970e-0e37-11e2-9462-7cc3a1719bfd',
	}

	logger = logging.getLogger()

	suite = unittest.TestLoader().loadTestsFromTestCase(ApiTest)

	unittest.TextTestRunner(verbosity=2).run(suite)


