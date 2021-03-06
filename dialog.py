
# xbmc
import xbmcgui

# python standart lib
import urllib
import sys
import os
import time
import json
import os.path
from datetime import datetime
import CommonFunctions
import socket

# application
from utilities import *
from app_apiclient import AppApiClient, AuthenticationError
from cache import StvList, DuplicateStvIdException
import top
from threading import Thread

# temporary
import random

ACTIONS_CLICK = [7, 100]
LIST_ITEM_CONTROL_ID = 500
HACK_GO_BACK = -2

common = CommonFunctions
common.plugin = "SynopsiTV"

__addon__  = xbmcaddon.Addon()
__addonpath__	= __addon__.getAddonInfo('path')
__addonname__ = __addon__.getAddonInfo('name')
__cwd__	= __addon__.getAddonInfo('path')
__author__  = __addon__.getAddonInfo('author')
__version__   = __addon__.getAddonInfo('version')
__profile__      = __addon__.getAddonInfo('profile')

itemFolderBack = {'name': '...', 'cover_medium': 'DefaultFolderBack.png', 'id': HACK_GO_BACK, 'type': 'HACK'}

open_dialogs = []
closed_dialogs = []
stashed_dialogs = []

def get_current_dialog():
	if open_dialogs:
		return open_dialogs[-1]
	else:
		return None

def close_current_dialog():
	d = get_current_dialog()
	if d:
		d.close()

	return d

def close_all_dialogs():
	while 1:
		d = close_current_dialog()
		if not d:
			break

def stash_all_dialogs():
	while 1:
		d = close_current_dialog()
		if not d:
			break

		stashed_dialogs.append(d)

def unstash_all_dialogs():
	log('stashed_dialogs:' + str(stashed_dialogs))
	for d in stashed_dialogs:
		open_dialogs.append(d)
		d.doModal()

def open_dialog(dialogClass, xmlFile, tpl_data, close=False):		
	if close:
		close_current_dialog()
			
	ui = dialogClass(xmlFile, __cwd__, "Default", data=tpl_data)
	ui.doModal()
		
	result = ui.result
	return result	

class MyDialog(xbmcgui.WindowXMLDialog):
	def __init__(self):
		self.parentWindow = open_dialogs[-1] if open_dialogs else None
		open_dialogs.append(self)
		self.result = None
	
	def close(self):
		if open_dialogs:
			# check if closing the currently opened dialog
			if open_dialogs[-1] != self:
				log('WARNING: Dialog queue inconsistency. Non-top dialog close')
			
			open_dialogs.remove(self)
			
		xbmcgui.WindowXMLDialog.close(self)
	
class ListDialog(MyDialog):
	""" Dialog for synopsi listings with custom cover overlays """
	def __init__(self, strXMLname, strFallbackPath, strDefaultName, **kwargs):
		super(ListDialog, self).__init__()
		self.data = kwargs['data']

		if kwargs['data'].has_key('_async_init'):
			self._async_init = kwargs['data']['_async_init']
			
		self.controlId = None
		self.selectedMovie = None
		self.listControl = None


	def onInit(self):		
		win = xbmcgui.Window(xbmcgui.getCurrentWindowDialogId())
		
		self.listControl = self.getControl(LIST_ITEM_CONTROL_ID)
		self.listControl.reset()

		# asynchronous initialization
		if self.__dict__.get('_async_init'):
			result = {}
			kwargs = self._async_init.get('kwargs', {})
			kwargs['result'] = result
			try:
				self._async_init['method'](**kwargs)	# method(result=result, +kwargs)
			except (AuthenticationError, ListEmptyException) as e:
				self.close()
				return
				
			self.data.update(result['result'])

		# exception of incoming data format
		if self.data.has_key('episodes'):
			self.data['items'] = self.data['episodes']
			first_episode = self.data['items'][0]
			self.data['tvshow_name'] = first_episode['tvshow_name']
			self.data['_categoryName'] = self.data['tvshow_name'] + ' - Season ' + first_episode['season_number']
			
		win.setProperty('ContainerCategory', self.data.get('_categoryName', ''))
		
		self.updateItems()
		
				
	def updateItems(self):
		items = []
		items.append(self._getListItem(itemFolderBack))
		for item in self.data['items']:
			li = self._getListItem(item)
			items.append(li)
		try:
			self.listControl.addItems(items)
			self.setFocus(self.listControl)
		except:
			log('Adding items failed')
	
	def refresh(self):
		self.updateItems()
		
	def setWatched(self, stv_id):
		for item in self.data['items']:
			if item['id'] == stv_id:
				item['watched'] = True

	def correctItem(self, old_stv_id, new_item):
		for index, item in enumerate(self.data['items']):
			if item['id'] == old_stv_id:
				self.data['items'][index] = new_item

	def _getListItem(self, item):
		#~ itemPath = 'mode=' + str(ActionCode.VideoDialogShowById) + '&amp;stv_id=' + str(item['id'])
		itemName = item['name']
		
		# add year after name
		if item.has_key('year'):
			itemName += ' (' + str(item['year']) + ')'

		# for episodes, add epis-ident
		if item['type'] == 'episode':
			episident = get_episode_identifier(item)
			itemName = '%s - %s' % (episident, itemName)
		
		# create listitem with basic properties	
		li = xbmcgui.ListItem(itemName, iconImage=item['cover_medium'])
		li.setProperty('id', str(item['id']))
		li.setProperty('type', str(item['type']))

		if item['type'] == 'episode':
			li.setProperty('episode_number', str(item['episode_number']))
			li.setProperty('season_number', str(item['season_number']))
			li.setProperty('tvshow_name', str(item['tvshow_name']))
			
		#~ li.setProperty('path', str(itemPath))		
			
		# prefer already set custom_overlay, if N/A set custom overlay
		if item.get('custom_overlay'):
			li.setProperty('CustomOverlay', item['custom_overlay'])
		else:
			oc = self._getItemOverlayCode(item)
			li.setProperty('CustomOverlay', overlay_image[oc])
			
		return li

	def _getItemOverlayCode(self, item):
		overlayCode = OverlayCode.Empty
		if item.get('file'):
			overlayCode += OverlayCode.OnYourDisk
		if item.get('watched'):
			overlayCode += OverlayCode.AlreadyWatched
			
		return overlayCode

	def onFocus(self, controlId):
		self.controlId = controlId

	def onAction(self, action):
		#~ log('action: %s focused id: %s' % (str(action.getId()), str(self.controlId)))
		
		if action in CANCEL_DIALOG:
			self.close()
		# if user clicked/entered an item
		elif self.controlId == LIST_ITEM_CONTROL_ID and action in ACTIONS_CLICK:
			item = self.getControl(LIST_ITEM_CONTROL_ID).getSelectedItem()			
			stv_id = int(item.getProperty('id'))

			if stv_id == HACK_GO_BACK:
				self.close()
			elif stv_id == HACK_SHOW_ALL_LOCAL_MOVIES:
				show_submenu(ActionCode.LocalMovies)
			else:
				data = {'type': item.getProperty('type'), 'id': stv_id}
				if data['type'] == 'episode':
					data['season_number'] = item.getProperty('season_number')
					data['episode_number'] = item.getProperty('episode_number')
					data['tvshow_name'] = item.getProperty('tvshow_name')
					#~ data['tvshow_name'] = self.data['tvshow_name']

				show_video_dialog(data, close=False)

		

def open_list_dialog(tpl_data, close=False):
	open_dialog(ListDialog, "custom_MyVideoNav.xml", tpl_data, close)

def show_movie_list(item_list):
	open_list_dialog({ 'items': item_list })

def show_tvshows_episodes(stv_id):
	def init_data(result):
		result['result'] = top.apiClient.get_tvshow_season(stv_id)
	
	tpl_data = { '_async_init': { 'method': init_data }}

	open_list_dialog(tpl_data)


class VideoDialog(MyDialog):
	"""
	Dialog about video information.
	"""
	def __init__(self, *args, **kwargs):
		super(VideoDialog, self).__init__()
		self.data = kwargs['data']
		self.controlId = None

	def _init_data(self):
		json_data = self.data

		if json_data.get('type') == 'tvshow':
			stv_details = top.apiClient.tvshow(json_data['id'], cast_props=defaultCastProps)
		else:
			stv_details = top.apiClient.title(json_data['id'], defaultDetailProps, defaultCastProps)
			
		top.stvList.updateTitle(stv_details)

		# add xbmc id if available
		if json_data.has_key('id') and top.stvList.hasStvId(json_data['id']):
			cacheItem = top.stvList.getByStvId(json_data['id'])
			json_data['xbmc_id'] = cacheItem['id']
			try:
				json_data['xbmc_movie_detail'] = xbmc_rpc.get_details('movie', json_data['xbmc_id'], True)
			except:
				pass

		# add similars or seasons (bottom covers list)
		if stv_details['type'] == 'movie':
			# get similar movies
			t1_similars = top.apiClient.titleSimilar(stv_details['id'])
			if t1_similars.has_key('titles'):
				stv_details['similars'] = t1_similars['titles']
		elif stv_details['type'] == 'tvshow' and stv_details.has_key('seasons'):
			seasons = top.stvList.get_tvshow_local_seasons(stv_details['id'])
			log('seasons on disk:' + str(seasons))		
			stv_details['similars'] = [ {'id': i['id'], 'name': 'Season %d' % i['season_number'], 'cover_medium': i['cover_medium'], 'watched': i['episodes_count'] == i['watched_count'], 'file': i['season_number'] in seasons} for i in stv_details['seasons'] ]

		# similar overlays
		if stv_details.has_key('similars'):
			for item in stv_details['similars']:
				top.stvList.updateTitle(item)

				oc = 0
				if item.get('file'):
					oc |= OverlayCode.OnYourDisk
				if item.get('watched'):
					oc |= OverlayCode.AlreadyWatched

				if oc:
					item['overlay'] = overlay_image[oc]

		self.data = video_dialog_template_fill(stv_details, json_data)

	def onInit(self):
		# reset some default garbage
		self.getControl(59).reset()
		
		# initialze data for the form
		self._init_data()
		
		# fill-in the form
		win = xbmcgui.Window(xbmcgui.getCurrentWindowDialogId())
		str_title = self.data['name'] + '[COLOR=gray] (' + unicode(self.data.get('year')) + ')[/COLOR]'
		if self.data['type'] == 'episode':
			episident = get_episode_identifier(self.data)			
			str_title = self.data['tvshow_name'] + ' - [COLOR=gray]' + episident + ' -[/COLOR] ' + str_title
			
		win.setProperty("Movie.Title", str_title)
		win.setProperty("Movie.Plot", self.data["plot"])
		win.setProperty("Movie.Cover", self.data["cover_full"])

		for i in range(5):
			win.setProperty("Movie.Similar.{0}.Cover".format(i + 1), "default.png")

		# set available labels
		i = 1
		for key, value in self.data['labels']:
			win.setProperty("Movie.Label.{0}.1".format(i), key)
			win.setProperty("Movie.Label.{0}.2".format(i), value)
			i = i + 1

		# enable file playing and correction if available
		if self.data.has_key('file'):
			win.setProperty("Movie.File", self.data['file'])
			win.setProperty("Movie.FileInfo", '%s in [%s]' % (os.path.basename(self.data['file']), os.path.dirname(self.data['file'])))
			self.getControl(5).setEnabled(True)
			self.getControl(13).setEnabled(True)

		# disable watched button for non-released movies
		if self.data.has_key('release_date') and self.data['release_date'] > datetime.today():
			self.getControl(11).setEnabled(False)


		win.setProperty('BottomListingLabel', self.data['BottomListingLabel'])

		# similars
		items = []

		if self.data.has_key('similars'):
			for item in self.data['similars']:
				li = xbmcgui.ListItem(item['name'], iconImage=item['cover_medium'])
				if item.get('overlay'):
					li.setProperty('Overlay', item['overlay'])

				li.setProperty('id', str(item['id']))
				items.append(li)

			# similars alternative
			self.getControl(59).addItems(items)

		tmpTrail = self.data.get('trailer')
		if tmpTrail:
			_youid = tmpTrail.split("/")
			_youid.reverse()
			win.setProperty("Movie.Trailer.Id", str(_youid[0]))
		else:
			self.getControl(10).setEnabled(False)

		if not self.data['type'] in ['movie', 'episode']:
			self.getControl(11).setEnabled(False)

	def onClick(self, controlId):
		log('onClick: ' + str(controlId))

		# play
		if controlId == 5:
			close_all_dialogs()

		# trailer
		elif controlId == 10:
			close_all_dialogs()

		# already watched
		elif controlId == 11:
			rating = get_rating()
			if rating < 4:
				top.apiClient.titleWatched(self.data['id'], rating=rating)
				self.parentWindow.setWatched(self.data['id'])
			self.close()			
			self.parentWindow.refresh()

		# similars / tvshow seasons	cover
		elif controlId == 59:
			selected_item = self.getControl(59).getSelectedItem()
			stv_id = int(selected_item.getProperty('id'))

			if self.data['type'] == 'tvshow':
				show_tvshows_episodes(stv_id)				
			else:
				show_video_dialog_byId(stv_id, close=True)

		# correction
		elif controlId == 13:
			new_title = self.user_title_search()
			#~ log('old_title:' + dump(filtertitles(self.data)))
			#~ log('new_title:' + dump(filtertitles(new_title)))
			if new_title and self.data.has_key('id') and self.data.get('type') not in ['tvshow', 'season']:
				try:
					top.stvList.correct_title(self.data, new_title)
					self.close()
					self.parentWindow.correctItem(self.data['id'], new_title)
					self.parentWindow.refresh()
					show_video_dialog_byId(new_title['id'])
				except DuplicateStvIdException, e:
					log(unicode(e))
					dialog_ok('This title is already in library. Cannot correct identity to this title')


	def onFocus(self, controlId):
		self.controlId = controlId

	def onAction(self, action):
		#~ log('action: %s focused id: %s' % (str(action.getId()), str(self.controlId)))
		if (action.getId() in CANCEL_DIALOG):
			self.close()

	def user_title_search(self):
		try:
			search_term = common.getUserInput(t_correct_search_title, "")
			if search_term:
				data = { 'search_term': search_term }
				return open_select_movie_dialog(data)				
			else:
				dialog_ok(t_enter_title_to_search)
		except:
			dialog_ok('Search failed. Unknown error.')

		return


class SelectMovieDialog(MyDialog):
	""" Dialog for choosing movie corrections """
	def __init__(self, *args, **kwargs):
		super(SelectMovieDialog, self).__init__()
		self.data = kwargs['data']
		self.controlId = None
		self.selectedMovie = None

	def _init_data(self):
		results = top.apiClient.search(self.data['search_term'], SEARCH_RESULT_LIMIT)
		if len(results['search_result']) == 0:
			dialog_ok('No results')
			self.close()
			return False
		else:
			self.data.update({ 'movies': results['search_result'] })		
			return True

	def onInit(self):
		if self._init_data():
			items = []
			for item in self.data['movies']:
				text = '%s [COLOR=gray](%s)[/COLOR]' % (item['name'], item.get('year', '?'))

				if item.get('type') == 'episode':
					text = 'S%sE%s - ' % (item.get('season_number', '??'), item.get('episode_number', '??')) + text

				li = xbmcgui.ListItem(text, iconImage=item['cover_medium'])
				li.setProperty('id', str(item['id']))
				li.setProperty('director', ', '.join(item.get('directors')) if item.has_key('directors') else t_unavail)
				cast = ', '.join([i['name'] for i in item['cast']]) if item.has_key('cast') else t_unavail			
				li.setProperty('cast', cast)
				items.append(li)

				self.getControl(59).addItems(items)

	def onClick(self, controlId):
		log('onClick: ' + str(controlId))
		if self.controlId == 59:
			sel_index = self.getControl(59).getSelectedPosition()
			self.result = self.data['movies'][sel_index]
			self.close()


	def onFocus(self, controlId):
		self.controlId = controlId

	def onAction(self, action):
		#~ log('action: %s focused id: %s' % (str(action.getId()), str(self.controlId)))
		if (action.getId() in CANCEL_DIALOG):
			self.close()


def open_select_movie_dialog(tpl_data):
	return open_dialog(SelectMovieDialog, "SelectMovie.xml", tpl_data)

def show_video_dialog_byId(stv_id, close=False):
	show_video_dialog({'id': stv_id}, close)	

def show_video_dialog(json_data, close=False):	
	open_video_dialog(json_data, close)


def video_dialog_template_fill(stv_details, json_data={}):

	log('show video:' + dump(json_data))
	log('stv_details video:' + dump(stv_details))

	# update empty stv_details with only nonempty values from xbmc
	for k, v in json_data.iteritems():
		if v and not stv_details.get(k):
			stv_details[k] = v

	tpl_data=stv_details

	# store file in tpl
	if tpl_data.has_key('xbmc_movie_detail'):
		if d.get('file'):
			tpl_data['file'] = d.get('file')

	# store labels
	labels = []	

	# append tuple to labels, translated by trfn, or the N/A string
	def append_tuple(stv_label, tpl_label, trfn):
		if tpl_data.get(tpl_label):
			val = trfn(tpl_data[tpl_label])
		else:
			val = t_unavail
				
		labels.append((stv_label, val))
	
	# translate functions
	def tr_genre(data): return ', '.join(data)
	def tr_cast(data): return ', '.join(map(lambda x:x['name'], data))
	def tr_runtime(data): return '%d min' % data

	append_tuple('Genre', 'genres', tr_genre)
	append_tuple('Cast', 'cast', tr_cast)
	append_tuple('Director', 'directors', tr_cast)		# reuse tr_cast here	
	append_tuple('Runtime', 'runtime', tr_runtime)
		
	if tpl_data.get('date'):
		tpl_data['release_date'] = datetime.fromtimestamp(tpl_data['date'])
		labels.append(('Release date', tpl_data['release_date'].strftime('%x')))
		
	tpl_data['labels'] = labels
	tpl_data['BottomListingLabel'] = type2listinglabel.get(tpl_data['type'], '')

	return tpl_data


def open_video_dialog(tpl_data, close=False):
	open_dialog(VideoDialog, "VideoInfo.xml", tpl_data, close)


def get_submenu_item_list(action_code, **kwargs):
	try:
		item_list = top.apiClient.get_item_list(action_code=action_code, **kwargs)

		# hack HACK_SHOW_ALL_LOCAL_MOVIES
		if action_code==ActionCode.LocalMovieRecco:
			item_list.append(item_show_all_movies_hack)

		if not item_list:
			raise ListEmptyException()

	except AuthenticationError as e:
		if dialog_check_login_correct():
			show_submenu(action_code, **kwargs)

		raise

	except ListEmptyException:
		dialog_ok(exc_text_by_mode(action_code))
		raise
		
	except:
		log(traceback.format_exc())
		dialog_ok(t_listing_failed)
		raise
			
	return item_list


def show_submenu(action_code, **kwargs):
	def init_data(result, **kwargs):
		result['result'] = {'items': get_submenu_item_list(**kwargs)}
	
	categoryName = submenu_categories_dict[action_code]
	kwargs['action_code'] = action_code
	tpl_data = { '_categoryName': categoryName, '_async_init': { 'method': init_data, 'kwargs': kwargs }}
	open_list_dialog(tpl_data)


# settings create account dialog
class CreateAccountDialog(MyDialog):
	ctl_create_account_id = 110
	ctl_realname = 4
	ctl_email = 5
	
	
	""" Dialog for choosing movie corrections """
	def __init__(self, *args, **kwargs):
		super(CreateAccountDialog, self).__init__()
		self.data = kwargs['data']
		self.real_name = ''
		self.email = __addon__.getSetting('USER')

	def onInit(self):
		self.getControl(self.ctl_email).setLabel(self.email)
		
	def onAction(self, action):
		if action in CANCEL_DIALOG:
			self.close()
		# click on 'real name' button/input
		elif action in ACTIONS_CLICK and (self.getFocusId() == self.ctl_realname):
			act_value = self.getControl(self.ctl_realname).getLabel()
			self.real_name = common.getUserInput('Enter Real Name', act_value)
			self.getControl(self.ctl_realname).setLabel(self.real_name)

		# click on 'email' button/input
		elif action in ACTIONS_CLICK and (self.getFocusId() == self.ctl_email):
			act_value = self.getControl(self.ctl_email).getLabel()
			self.email = common.getUserInput('Enter Email', act_value)
			self.getControl(self.ctl_email).setLabel(self.email)

		# click on 'create account' button
		elif action in ACTIONS_CLICK and (self.getFocusId() == self.ctl_create_account_id):
			result = top.apiClient.profileCreate(self.real_name, self.email)
			if result.get('status') == 'created':
				dialog_ok('Thank You for Signing Up! Check your inbox for an email from us to complete the process. We are happy to have you.')
				self.close()
			elif result.get('status') == 'failed':
				if result.get('message') is str:
					message = result['message']
				else:
					message = ' '.join([' '.join(i) for i in result['message'].values()])

				dialog_ok(message)
			else:
				log('Failed to create account.' + str(result))

			return True

def open_create_account_dialog(tpl_data):
	dlg_result = open_dialog(CreateAccountDialog, "AccountCreate.xml", tpl_data)
	
