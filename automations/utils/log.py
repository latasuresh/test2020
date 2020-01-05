import datetime
import logging
import os
import sys


class LogWrapper(object):
	"""Simple log wrapper for injecting the timestamp inline at the start of
	the log message.
	"""

	def __init__(self, logger):
		self.logger = logger

	def info(self, msg, *args, **kwargs):
		"""Log info message with injected timestamp.

		Args:
			msg (str): thr log message
		"""
		self.logger.info(self.prefix(msg, "I"), *args, **kwargs)

	def warn(self, msg, *args, **kwargs):
		"""Log warn message with injected timestamp.

		Args:
			msg (str): the log message
		"""
		self.logger.warn(self.prefix(msg, "W"), *args, **kwargs)

	def error(self, msg, *args, **kwargs):
		"""Log error message with injected timestamp.

		Args:
			msg (str): the log message
		"""
		self.logger.info(self.prefix(msg, "E"), *args, **kwargs)

	def execption(self, msg, *args, **kwargs):
		"""Log exception with injected timestamp.

		Args:
			msg (str): the log message
		"""
		self.logger.execption(self.prefix(msg, "E"), *args, **kwargs)

	def debug(self, msg, *args, **kwargs):
		"""Log debug message with injected timestamp.

		Args:
			msg (str): the log message
		"""
		self.logger.debug(self.prefix(msg, "D"), *args, **kwargs)

	def critical(self, msg, *args, **kwargs):
		"""Log critical message with injected timestamp.

		Args:
			msg (str): the log message
		"""
		self.logger.critical(self.prefix(msg, "C"), *args, **kwargs)

	def prefix(self, msg, level):
		"""Log info message with injected timestamp.

		Args:
			msg (str): the log message
			level (str): the log level string to be injected
		"""
		now = datetime.datetime.now()
		time = now.strftime("%H:%M:%S.")
		time_milliseconds = time + "{0:03.0f}".format(now.microsecond / 1000)
		return u"{} {}: {}".format(time_milliseconds, level, msg)

class Log(object):
	"""Basic logger management.
	"""

	initialised = False
	header = logging.getLogger(">") # output pure log messages
	default = LogWrapper(header) # adds timestamp and level as prefix
	logger = default # default to the header logger for test/run start

	@classmethod
	def header_mode(cls):
		"""Switch standard logging to use the header logger.
		"""
		cls.logger = cls.header

	@classmethod
	def default_mode(cls):
		"""Switch standard logging to use the timestamped logger.
		"""
		cls.logger = cls.default

	@classmethod
	def initialise(cls, is_test=True, level=logging.INFO):
		"""Init the logger.

		Args:
			is_test (bool): True if runnning via a test
			level (level): logger logging level
		"""
		if not cls.initialised:
			logging.basicConfig(format='%(message)s', level=level)

			if os.environ.get("JENKINS_HOME", None) != None:
				ch = logging.StreamHandler()
				ch.setLevel(level)
				formatter = logging.Formatter('%(message)s')
				ch.setFormatter(formatter)
				cls.header.addHandler(ch)

			cls.initialised = True
		return cls
