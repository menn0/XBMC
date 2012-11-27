# xbmc
import xbmc, xbmcgui, xbmcaddon

# python standart lib
import json


class xbmcRPCclient(object):

	def __init__(self, logLevel = 0):
		self.__logLevel = logLevel

	def execute(self, methodName, params):
		req = {
			'params': params,
			'jsonrpc': '2.0',
			'method': methodName,
			'id': 1
		}

		if self.__logLevel:
			xbmc.log('xbmc RPC request: ' + str(dump(req)))

		response = xbmc.executeJSONRPC(dump(req))
		
		json_response = json.loads(response)

		if self.__logLevel:
			xbmc.log('xbmc RPC response: ' + str(dump(json_response)))

		if json_response.has_key('error') and json_response['error']:
			xbmc.log('xbmc RPC ERROR: ' + json_response['error']['message'])
			xbmc.log('xbmc RPC request: ' + str(dump(req)))
			xbmc.log('xbmc RPC response: ' + str(dump(json_response)))
			raise Exception(json_response['error']['message'])

		return json_response['result']


	def get_movies(start, end):
		"""
		Get movies from xbmc library. Start is the first in list and end is the last.
		"""
		properties = ['file', 'imdbnumber', "lastplayed", "playcount"]

		response = self.execute(
			'VideoLibrary.GetMovies',
			{
				'properties': properties,
				'limits': {'end': end, 'start': start}
			}
		)

		return response

	def get_all_movies():
		"""
		Get movies from xbmc library. Start is the first in list and end is the last.
		"""
		properties = ['file', 'imdbnumber', "lastplayed", "playcount"]

		response = self.execute(
			'VideoLibrary.GetMovies',
			{
				'properties': properties
			}
		)

		return response

	def get_all_tvshows():
		"""
		Get movies from xbmc library. Start is the first in list and end is the last.
		"""
		properties = ['file', 'imdbnumber', "lastplayed", "playcount", "episode", "thumbnail"]

		response = self.execute(
			'VideoLibrary.GetTVShows',
			{
				'properties': properties
			}
		)

		return response

	def get_tvshows(start, end):
		"""
		Get movies from xbmc library. Start is the first in list and end is the last.
		"""
		properties = ['file', 'imdbnumber', "lastplayed", "playcount", "episode"]

		response = self.execute(
			'VideoLibrary.GetTVShows',
			{
				'properties': properties,
				'limits': {'end': end, 'start': start}
			}
		)

		return response


	def get_episodes(twshow_id, season=-1):
		"""
		Get episodes from xbmc library.
		"""
		properties = ['file', "lastplayed", "playcount", "season", "episode"]
		if season == -1:
			params = {
				'properties': properties,
				'tvshowid': twshow_id
			}
		else:
			params = {
				'properties': properties,
				'tvshowid': twshow_id,
				'season': season
			}

		response = self.execute(
			'VideoLibrary.GetEpisodes',
			params
		)

		return response

	def get_movie_details(movie_id, all_prop=False):
		"""
		Get dict of movie_id details.
		"""
		if all_prop:
			properties = [
				"title",
				"genre",
				"year",
				"rating",
				"director",
				"trailer",
				"tagline",
				"plot",
				"plotoutline",
				"originaltitle",
				"lastplayed",
				"playcount",
				"writer",
				"studio",
				"mpaa",
				"cast",
				"country",
				"imdbnumber",
				"premiered",
				"productioncode",
				"runtime",
				# "set",
				"showlink",
				"streamdetails",
				# "top250",
				"votes",
				# "fanart",
				# "thumbnail",
				"file",
				"sorttitle",
				"resume",
				# "setid
			]
		else:
			properties = ['file', 'imdbnumber', "lastplayed", "playcount"]

		response = self.execute(
			'VideoLibrary.GetMovieDetails',
			{
				'properties': properties,
				'movieid': movie_id  # s 1 e 2 writes 2
			}
		)

		return response['moviedetails']


	def get_tvshow_details(movie_id):
		"""
		Get dict of movie_id details.
		"""
		properties = ['file', 'imdbnumber', "lastplayed", "playcount"]
		#	"title", 
		#   "genre", 
		#   "year", 
		#   "rating", 
		#   "plot", 
		#   "studio", 
		#   "mpaa", 
		#   "cast", 
		#   "playcount", 
		#   "episode", 
		#   "imdbnumber", 
		#   "premiered", 
		#   "votes", 
		#   "lastplayed", 
		#   "fanart", 
		#   "thumbnail", 
		#   "file", 
		#   "originaltitle", 
		#   "sorttitle", 
		#   "episodeguide"

		response = self.execute(
			'VideoLibrary.GetTVShowDetails',
			{
				'properties': properties,
				'tvshowid': movie_id 
			}
		)

		return response


	def get_episode_details(movie_id):
		"""
		Get dict of movie_id details.
		"""
		properties = ['file', "lastplayed", "playcount", "season", "episode", "tvshowid"]

		response = self.execute(
			'VideoLibrary.GetEpisodeDetails',
			{
				'properties': properties,
				'episodeid': movie_id
			}
		)

		return response['episodedetails']

	def GetInfoLabels():
		"""
		"""

		response = self.execute(
			'XBMC.GetInfoLabels',
			{
				'properties' : [ 'System.CpuFrequency', 'System.KernelVersion','System.FriendlyName','System.BuildDate','System.BuildVersion' ]
			}
		)

		return response


# init local variables
xbmcRPC = xbmcRPCclient()