# xbmc
import xbmc

# python standart lib
import logging
import logging.handlers
import os

class Loggable(object):
	lognames = []

	def __init__(self):
		super(Loggable, self).__init__()
		self.name = self.get_log_name()
		self._log = logging.Logger(self.name)
		self._log.setLevel(logging.DEBUG)

		# assure that log dir exists
		logdir = self.get_log_dir()

		if not os.path.exists(logdir):
			os.mkdir(logdir)

		fh = logging.handlers.RotatingFileHandler(os.path.join('log', self.name + '.log'), mode='w', backupCount=2)
		self._log.addHandler(fh)

		# try to add handlers from default log
		def_log = logging.getLogger()
		self._log.debug('Starting logger')
		self._log.handlers += def_log.handlers

	def get_log_dir(self):
		return os.path.join(xbmc.translatePath('special://temp'), 'log')

	def get_log_name(self):
		new_log_name = self.__class__.__name__
		if new_log_name in self.lognames:
			new_log_name += '_' + str(id(self))
		else:
			self.lognames.append(new_log_name)

		return new_log_name

