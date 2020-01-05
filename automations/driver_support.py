import functools
import hmac
import logging
import os
import time
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed, wait
from hashlib import md5

from sauceclient import SauceClient
from selenium import webdriver
from selenium.common.exceptions import TimeoutException

from automations.browsers import Browsers
from automations.config_support import Config
from automations.utils.log import Log
from automations.utils.parallel import Concurrent

logger = logging.getLogger("LOG") # outputs to main console during Jenkins runs


def drivers(*names):
	"""Decorator to add per-test drivers to the base driver set.

	Args:
		names ((str)): driver names tuple
	"""
	def drivers_decorator(fn):

		@functools.wraps(fn)
		def wrapper(self, *args, **kwargs):
			self.load_drivers(names)
			if hasattr(self, 'prepare'):
				self.prepare()
			return fn(self, *args, **kwargs)
		return wrapper
	return drivers_decorator

###############################################################################

class DriverSupport(object):
	"""WebDriver support/mixin for convenient access to WebDriver setup and
	teardown.
	"""

	sauce_status = True
	requested_drivers = set()

	def __init__(self):
		"""New DriverSupport instance.

		Not invoked if started from a test run.
		"""
		self.__class__.init_driver_support()

	@classmethod
	def init_driver_support(cls):
		"""Initialise the basic config (and sauce client if requested).
		"""
		cls.config = Config.instance()
		if cls.config['use_sauce']:
			if not hasattr(cls, 'sauce'):
				cls.sauce = SauceClient(
					cls.config['sauce_username'],
					cls.config['sauce_access_key']
				)

	def get_cookie(self, driver, name):
		"""Get a cookie from the browser session.

		Args:
			driver (WebDriver): the driver to interogate
			name (str): the cookie name to be found

		Returns:
			the cookie value if found else None
		"""
		cookies = driver.get_cookies()
		for cookie in cookies:
			if cookie['name'] == name:
				return cookie['value']
		return None

	@property
	def sauce_test_metadata(self):
		"""Generate the Sauce metadata map.

		Returns:
			{str,str}: the Sauce metadata
		"""
		if not hasattr(self, "shortDescription") \
			or self.shortDescription() == None:
			raise Exception("Executions must have a valid description")

		return {
			'build': os.environ.get('BUILD_NUMBER', None),
			'name': "[CHAT] {}".format(self.shortDescription()),
			'custom_data': {
				'build-url': os.environ.get('BUILD_URL', None),
			},
		}

	def get_desired_capabilities(self, driver_name):
		"""Get desired_capabilities dict for driver_name

		Args:
			driver_name (string): name of the driver

		Returns:
			desired_capabilities (dict): requested capabilities
		"""
		capabilities = self.desired_capabilities.copy()

		if self.config['use_sauce']:
			capabilities['tunnelIdentifier'] = self.config['sauce_tunnel']
			capabilities['chromeOptions'] = {
				'prefs': {
					"profile.default_content_setting_values.notifications": 2,
					'credentials_enable_service': False
				}
			}

			# Sauce Labs only accepts location names of timezones and not their paths.
			# Underscores also need to be replaced with spaces.
			# E.g. 'America/New_York' -> 'New York'
			# https://wiki.saucelabs.com/display/DOCS/Test+Configuration+Options#TestConfigurationOptions-CustomTimeZones

			if not self.config['detect_timezone']:
				timezone = self.config['timezone'].split('/')[-1].replace('_', ' ')
				capabilities['timeZone'] = timezone

			if hasattr(self, "_testMethodName"):
				Browsers.apply_extended_debug(self._testMethodName,
					capabilities)
		return capabilities

	def load_drivers(self, drivers):
		"""Load additional drivers to the defined request_drivers.

		Args:
			drivers ((str)): driver names tuple
		"""
		self.requested_drivers = set()
		self.driver_logged = False
		driver_launcher = Concurrent()

		concurrent_launch = self.is_chrome()

		for driver_name in drivers:
			if concurrent_launch:
				driver_launcher.add(self.load_and_prepare_driver, driver_name)
			else:
				self.load_and_prepare_driver(driver_name)
		if concurrent_launch:
			driver_launcher.run()

	def load_and_prepare_driver(self, driver_name):
		"""Load the requested driver and invoke it's prepare method if any.

		Args:
			driver_name (str): the name assigned to the driver to be created
		"""
		self._get_driver(driver_name)

		# now prepare
		attr_name = "prepare_" + driver_name.lower()
		if hasattr(self, attr_name):
			getattr(self, attr_name)()

	def _browser_version(self, driver, desired_capabilities):
		"""Get the best availabe browser version.

		Args:
			driver (WebDriver): driver in use
			desired_capabilities (dict): requested capabilities

		Returns:
			str: browser version string
		"""
		browser_version = None
		if 'version' in driver.desired_capabilities:
			return driver.desired_capabilities['version']
		elif 'browserVersion' in driver.desired_capabilities:
			return driver.desired_capabilities['browserVersion']
		else:
			return desired_capabilities['version']

	def _get_driver(self, driver_name):
		"""Configure and start a webdriver.

		Setting it as an attribute of the test class using the provided name.

		Args:
			driver_name (str): the driver name
		"""
		desired_capabilities = self.get_desired_capabilities(driver_name)

		if self.config['use_sauce']:
			driver = self.launch_remote(desired_capabilities)
			token = hmac.new(str(self.config['sauce_auth_string']),
				driver.session_id, md5).hexdigest()

			if not self.driver_logged:
				Log.logger.info("Running on [OS:{} Browser:{} Version:{} "
				.format(desired_capabilities['platform'],
					desired_capabilities['browserName'],
					self._browser_version(driver, desired_capabilities)))
				self.driver_logged = True

			Log.logger.info("%s >> Sauce URL: "
				"https://app.saucelabs.com/tests/%s/watch?auth=%s ",
				driver_name, driver.session_id, token)

			self.requested_drivers.add(driver_name)
			setattr(self, driver_name, driver)
			setattr(driver, 'driver_name', driver_name)

			try:
				self.sauce.jobs.update_job(driver.session_id,
					**self.sauce_test_metadata)
			except:
				self.sauce.jobs.update_job(driver.session_id,
					**self.sauce_test_metadata)
		else:
			chrome_options = webdriver.ChromeOptions()
			chrome_options.add_argument('--disable-gpu')
			prefs = {"profile.default_content_setting_values.notifications": 2,
				'credentials_enable_service': False}
			chrome_options.add_experimental_option("prefs", prefs)
			driver = self.launch_chrome(desired_capabilities, chrome_options)

			self.requested_drivers.add(driver_name)
			setattr(self, driver_name, driver)
			setattr(driver, 'driver_name', driver_name)

	def launch_remote(self, capabilities):
		"""Create a remote webdriver with one retry.

		Args:
			desired_capabilities ({str, str}):browser capabilities map

		Returns:
			WebDriver: the created driver
		"""
		try:
			return webdriver.Remote(desired_capabilities=capabilities,
				command_executor=self.config['sauce_url'])
		except:
			time.sleep(2)
			return webdriver.Remote(desired_capabilities=capabilities,
				command_executor=self.config['sauce_url'])

	def launch_chrome(self, capabilities, options):
		"""Create a local Chrome webdriver with one retry.

		Args:
			desired_capabilities ({str, str}): browser capabilities map
			chrome_options ({str, str}): chrome options map

		Returns:
			WebDriver: the created driver
		"""
		try:
			return webdriver.Chrome('chromedriver',
				desired_capabilities=capabilities, chrome_options=options)
		except:
			time.sleep(2)
			return webdriver.Chrome('chromedriver',
				desired_capabilities=capabilities, chrome_options=options)

	def is_chrome(self):
		"""Check if the current browser being lanuched is Chrome.

		Returns:
			bool: True if Chrome
		"""
		return self.desired_capabilities['browserName'] == 'chrome'

###############################################################################

	def cleanup_drivers(self):
		"""Test cleaup (teardown).
		"""
		self.quit_all_drivers()
		self.notify_sauce()

		if self.requested_drivers:
			for driver_name in self.requested_drivers:
				if hasattr(self, driver_name):
					delattr(self, driver_name)

	def all_drivers(self):
		"""Get all active drivers.

		Returns:
			array: list of name/driver of active drivers (driver_name, driver)
		"""
		drivers = []
		if self.requested_drivers:
			for driver_name in self.requested_drivers:
				if hasattr(self, driver_name):
					drivers.append((driver_name, getattr(self, driver_name)))
		return drivers

	def quit_all_drivers(self):
		"""Send a quit command to all active drivers.
		"""
		if self.requested_drivers:
			for driver_name in self.requested_drivers:
				try:
					if hasattr(self, driver_name):
						driver = getattr(self, driver_name)
						if driver:
							driver.quit()
				except:
					Log.logger.warn("Exception quiting driver")
					pass
		self.requested_drivers = set()

	def log_all_consoles(self):
		"""Executed on completion of a test but still withing the test and
		before cleanup.

		Defaults to logging the driver/browser consoles.
		"""
		if self.requested_drivers:
			self.log_info("JS CONSOLE LOGS")
			self.log_separator()
			for driver_name in self.requested_drivers:
				try:
					if hasattr(self, driver_name):
						driver = getattr(self, driver_name)
						if driver:
							self.log_browser_console(driver, driver_name)
				except:
					pass
			self.log_info_end()

	def log_browser_console(self, driver, driver_name):
		"""Output all web driver JS console events to the log.

		Args:
			driver (WebDriver): the driver to log
			driver_name (str): the driver name
		"""
		try:
			for error in driver.get_log("browser"):
				Log.logger.info("{} >> {}".
					format(driver_name, error))
		except:
			Log.logger.info("[[Error dumping JS console for '{}'']]"
				.format(driver_name))
			pass

	def notify_sauce(self, failed=False):
		"""When finishing a test case notify SauceLabs of test completion.

		Args:
			failed (bool): set as True to directly report a fail
		"""

		if not self.config['use_sauce']:
			return

		if self.requested_drivers:
			for driver_name in self.requested_drivers:
				try:
					if hasattr(self, driver_name):
						driver = getattr(self, driver_name)
						if driver:
							try:
								self.notify_sauce_job(driver, failed)
							except:
								self.notify_sauce_job(driver, failed)
				except:
					Log.logger.warn("Exception finishing Sauce job")
					pass

	def notify_sauce_job(self, driver, failed=False):
		"""Notify a sauce job of completion.

		Args:
			driver (WebDriver): the driver for which to notify
			failed (bool): set as True to directly report a fail
		"""
		status = not failed and self.sauce_status
		self.sauce.jobs.update_job(driver.session_id, passed=status)
