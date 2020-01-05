try:
	import unittest2 as unittest
except ImportError:
	import unittest
import functools
import logging
import os
import traceback
import unittest
from datetime import datetime as dt
from random import randint

from sauceclient import SauceClient

from automations import Automation
from automations.account_support import AccountSupport
from automations.config_support import Config
from automations.core.element import Element
#from automations.core.garden import Garden
from automations.driver_support import DriverSupport
from automations.pages.dashboard import DashboardPage
#from automations.pages.widget import Widget
from automations.pages.evpn import EvpnPage
from automations.random_support import RandomSupport
from automations.utils.log import Log

logger = logging.getLogger("LOG") # outputs to main console during Jenkins runs

###############################################################################

class TestCase(unittest.TestCase, Automation, DriverSupport,
	RandomSupport, AccountSupport):
	"""Base test case."""

	_skip_test = False
	_multiprocess_can_split_ = True
	test_dir = "browser_tests"

	@property
	def current_test_name(self):
		"""Get the current test name from the class and method being run.

		Returns:
			str: the test name
		"""
		return '{}.{}'.format(
			self.__class__.__name__,
			self._testMethodName
		)

	@property
	def test_file_name(self):
		"""Get the full name of the test file.

		Returns:
			the name of the test file being executed
		"""
		return "{}.py".format(self.__module__.split('.')[-1])

	@property
	def test_file_path(self):
		"""Get the relative path of test file.

		Returns:
			the path of test file
		"""
		return "{}.py".format(self.__module__.replace('.', '/'))

	###########################################################################
	### Class setup/teardown
	###########################################################################

	@classmethod
	def setUpClass(cls):
		"""Class setup.
		"""
		super(TestCase, cls).setUpClass()
		cls.setUpAutomationClass()

	@classmethod
	def tearDownClass(cls):
		"""Class teardown.
		"""
		cls.tearDownAutomationClass()
		super(TestCase, cls).tearDownClass()

	###########################################################################
	### Run setup/teardown
	###########################################################################

	def setUp(self):
		"""Test setup.
		"""
		super(TestCase, self).setUp()
		self.error_count = len(self.current_result.errors) \
			+ len(self.current_result.failures)

	def run(self, result=None):
		"""Supplements the super class `run()`.
		"""
		self.current_result = result
		super(TestCase, self).run(result)

	def cleanup(self):
		"""Test cleaup (teardown).
		"""
		self.sauce_status = len(self.current_result.errors) + \
			len(self.current_result.failures) == self.error_count
		super(TestCase, self).cleanup()

	###########################################################################
	### Utils
	###########################################################################

	def assertEmpty(self, val):
		"""Assert the the value is none or empty as appropriate for it's type.

		Args:
			val (obj): any primitive or object
		"""
		if type(val) in (list, tuple, dict, unicode, str):
			self.assertEqual(len(val), 0)
		else:
			self.assertIsNone(val)
