import json
import os
import sys

from automations.utils.log import Log

# Sauce OS strings
WINDOWS_10 = "Windows 10"
WINDOWS_7 = "Windows 7"
OSX_HIGH_SIERRA = "macOS 10.13"
OSX_SIERRA = "macOS 10.12"
OSX_EL_CAPITAN = "OS X 10.11"
OSX_YOSIMITE = "OS X 10.10"
OSX_MAVERICKS = "OS X 10.9"
OSX_MOUNTAIN_LION = "OS X 10.8"

DEFAULT_WINDOWS = WINDOWS_10

def browsers(browsers, direct=False):
	"""Decorator for browser confoguration of tests.

	Generates a test class in the form '{class_name}_N' for each browser required.

	Additional flags:

	Set env var BROWSERS_LOG_ALL=1 if you would like complete JS console
	logging. Be aware this can produce a fair amount of output so it's best to
	reserve use of thjis for explicit debnugging.

	Set env var EXTENDED_DEBUG=1 to request extended debugging from Sauce Labs:
	https://wiki.saucelabs.com/pages/viewpage.action?pageId=70072943

	Args:
		browsers ([]): array of platform definitions to be used
	"""
	def decorator(base_class):
		module = sys.modules[base_class.__module__]
		base_class.__test__ = False
		test_browsers = browsers

		# handle browser config override from the command line
		browser_override = os.environ.get('BROWSERS')
		if browser_override:
			try:
				if browser_override.startswith("{"):
					test_browsers = Browsers.from_json_string(browser_override)
				else:
					test_browsers = getattr(Browsers, browser_override)
			except:
				Log.logger.info("Error in browser override!!")
				raise

		if direct:
			base_class.desired_capabilities = test_browsers[0].copy()
			base_class.__test__ = True
			base_class.__module__ = module
			return base_class

		# generate a test class per browser
		for i, browser in enumerate(test_browsers):
			name = "%s_%s" % (base_class.__name__, i + 1)
			d = {
				'desired_capabilities': browser.copy(),
				'__test__': True,
				'__module__': module,
				'_testClassName': name
			}
			setattr(module, name, type(name, (base_class,), d))

		return base_class
	return decorator

##################################################################################################################

class Browsers(object):
	"""Browser specification for test runs, principally for running on Saucelabs.

	Each test class should declare an appropriate default browser set, e.g. @browsers(Browsers.primary)

	Config may be overridden on the command line when running the test (see from_json_string()) e.g.

	./scripts/smoke_tests_prod.sh BROWSERS='all_dashboard_except_primary' ...
	./scripts/run_tests.sh BROWSERS='{"chrome":[57,59],"firefox":["latest-2", "latest"]}' ...
	"""

	@classmethod
	def setup(cls):
		""" Setup the core browser configs, manage the default browser versions here.
		"""
		cls.dashboard_chrome_versions = ['latest-2', 'latest']
		cls.dashboard_firefox_versions = ['latest-2', 'latest']
		cls.dashboard_safari_versions = ['latest-2', 'latest']
		cls.dashboard_edge_versions = ['latest-2', 'latest']
		cls.dashboard_ie_versions = ['latest']

		cls.widget_chrome_versions = [26, 'latest-2', 'latest']
		cls.widget_firefox_versions = [21, 'latest-2', 'latest']
		cls.widget_safari_versions = [6, 'latest-2', 'latest']
		cls.widget_edge_versions = ['latest-2', 'latest']
		cls.widget_ie_versions = ['latest']
		cls.widget_iphone_versions = ['latest-1', 'latest']
		cls.widget_android_versions = [4.4, 5.1, 6.0, 7.0]

		cls.primary = cls.chrome(DEFAULT_WINDOWS, 'latest')
		cls.primary_iphone = cls.iphone(cls.widget_iphone_versions[-1])
		cls.primary_android = cls.android(cls.widget_android_versions[-1])

		cls.all_dashboard_except_primary = cls.chrome(DEFAULT_WINDOWS, cls.dashboard_chrome_versions[:-1]) + \
											cls.firefox(DEFAULT_WINDOWS, cls.dashboard_firefox_versions) + \
											cls.safari(cls.dashboard_safari_versions) + \
											cls.edge(cls.dashboard_edge_versions) + \
											cls.ie(DEFAULT_WINDOWS, cls.dashboard_ie_versions)

		cls.all_widget_except_primary = cls.chrome(DEFAULT_WINDOWS, cls.widget_chrome_versions[:-1]) + \
											cls.firefox(DEFAULT_WINDOWS, cls.dashboard_firefox_versions) + \
											cls.safari(cls.dashboard_safari_versions) + \
											cls.edge(cls.dashboard_edge_versions) + \
											cls.ie(DEFAULT_WINDOWS, cls.dashboard_ie_versions)

		cls.all_mobile_except_primary = cls.iphone(cls.widget_iphone_versions[:-1]) + \
										cls.android(cls.widget_android_versions[:-1])

		cls.all_dashboard = cls.chrome(DEFAULT_WINDOWS, cls.dashboard_chrome_versions) + \
							cls.firefox(DEFAULT_WINDOWS, cls.dashboard_firefox_versions) + \
							cls.safari(cls.dashboard_safari_versions) + \
							cls.edge(cls.dashboard_edge_versions) + \
							cls.ie(DEFAULT_WINDOWS, cls.dashboard_ie_versions)

		cls.all_widget = cls.chrome(DEFAULT_WINDOWS, cls.widget_chrome_versions) + \
							cls.firefox(DEFAULT_WINDOWS, cls.dashboard_firefox_versions) + \
							cls.safari(cls.dashboard_safari_versions) + \
							cls.edge(cls.dashboard_edge_versions) + \
							cls.ie(DEFAULT_WINDOWS, cls.dashboard_ie_versions)

		cls.all_mobile = cls.iphone(cls.widget_iphone_versions) + \
						cls.android(cls.widget_android_versions)

		cls.latest_chrome = cls.chrome(DEFAULT_WINDOWS, ['latest'])
		cls.latest_firefox = cls.firefox(DEFAULT_WINDOWS, ['latest'])
		cls.latest_safari = cls.safari(['latest'])
		cls.latest_edge = cls.edge(['latest'])
		cls.latest_ie = cls.ie(DEFAULT_WINDOWS, ['latest'])

		cls.dashboard_latest = cls.latest_chrome + \
									cls.latest_firefox + \
									cls.latest_safari + \
									cls.latest_edge + \
									cls.latest_ie

	##################################################################################################################

	@classmethod
	def chrome(cls, platform, versions):
		"""Generate a Chrome definition for each provided version.

		Args:
			platform (str): OS name/version
			versions ([]): single or list of browser versions to create definitions for

		Returns:
			[]: array of Chrome browser definitions
		"""
		return cls.desktop(platform, "chrome", versions)

	@classmethod
	def firefox(cls, platform, versions):
		"""Generate a Firefox definition for each provided version.

		Args:
			platform (str): OS name/version
			versions ([]): single or list of browser versions to create definitions for

		Returns:
			[]: array of Firefox browser definitions
		"""
		return cls.desktop(platform, "firefox", versions)

	@classmethod
	def safari(cls, versions):
		"""Generate a Safari definition for each provided version.

		Auto matches the required OS as available on Sauce.

		Args:
			versions ([]): single or list of browser versions to create definitions for

		Returns:
			[]: array of Safari browser definitions
		"""
		browsers = []

		# safari versions are hard linked to OSX versions
		for version in versions:
			if version == 11:
				browsers = browsers + cls.desktop(OSX_HIGH_SIERRA, "safari", version)
			elif version == 10:
				browsers = browsers + cls.desktop(OSX_SIERRA, "safari", version)
			elif version == 9:
				browsers = browsers + cls.desktop(OSX_EL_CAPITAN, "safari", version)
			elif version == 8:
				browsers = browsers + cls.desktop(OSX_YOSIMITE, "safari", version)
			elif version == 7:
				browsers = browsers + cls.desktop(OSX_MAVERICKS, "safari", version)
			elif version == 6:
				browsers = browsers + cls.desktop(OSX_MOUNTAIN_LION, "safari", version)
			else:
				browsers = browsers + cls.desktop(OSX_HIGH_SIERRA, "safari", version)

		return browsers

	@classmethod
	def edge(cls, versions):
		"""Generate an Edge definition for each provided version.

		Always uses Windows 10.

		Args:
			platform (str): OS name/version
			versions ([]): single or list of browser versions to create definitions for

		Returns:
			[]: array of Edge browser definitions
		"""
		return cls.desktop(WINDOWS_10, "MicrosoftEdge", versions)

	@classmethod
	def ie(cls, platform, versions):
		"""Generate an Internet Explorer definition for each provided version.

		Version 9 will always use Windows 7 (Sauce restriction).

		Args:
			platform (str): OS name/version
			versions ([]): single or list of browser versions to create definitions for

		Returns:
			[]: array of IE browser definitions
		"""
		browsers = []

		# v9 only available on Windows 7
		for version in versions:
			if version == 9:
				browsers = browsers + cls.desktop(WINDOWS_7, "internet explorer", version)
			else:
				browsers = browsers + cls.desktop(platform, "internet explorer", version)

		return browsers

	##################################################################################################################

	@classmethod
	def from_json_string(cls, config):
		"""Create a browser list from a JSON string, e.g. {"chrome":[57,59],"firefox":[53,55]}.

		Args:
			config (str): JSON string of the desired browsers

		Returns:
			[]: array of browser definitions
		"""
		requested = json.loads(config)

		browsers = []

		for browser, versions in requested.iteritems():
			if browser == 'chrome':
				browsers = browsers + cls.chrome(WINDOWS_10, versions)
			elif browser == 'firefox':
				browsers = browsers + cls.firefox(WINDOWS_10, versions)
			elif browser == 'safari':
				browsers = browsers + cls.safari(versions)
			elif browser == 'edge':
				browsers = browsers + cls.edge(versions)
			elif browser == 'ie':
				browsers = browsers + cls.ie(WINDOWS_10, versions)
			elif browser == 'iphone':
				browsers = browsers + cls.iphone(versions)
			elif browser == 'android':
				browsers = browsers + cls.android(versions)

		if len(browsers) == 0:
			Log.logger.warn("No valid browser config found, reverting to primary")
			browsers = cls.primary

		return browsers

	@classmethod
	def apply_extended_debug(cls, current_test_name, desired_capabilities):
		"""Extended debug setting check for this test.

		Adds the extended debug flag to the desired capabilites is requested.
		e.g.
		export EXTENDED_DEBUG=all # all tests
		export EXTENDED_DEBUG='{"tests":["test_send_file"]}' # named tests

		Args:
			current_test_name (string): current test method being run
			desired_capabilities (dict): the desired capabilities for this test
		"""
		if cls.use_extended_debug(current_test_name, desired_capabilities):
			desired_capabilities['extendedDebugging'] = True

	@classmethod
	def use_extended_debug(cls, current_test_name, desired_capabilities):
		"""See extended_debug()
		"""
		extended_debug = os.environ.get('EXTENDED_DEBUG', None)
		if extended_debug != None:
			if extended_debug.lower() == 'all':
				return True
			root = json.loads(extended_debug)
			return current_test_name in root['tests']
		return False

	##################################################################################################################

	@classmethod
	def desktop(cls, platform, browser, versions):
		"""
		Create a browser sauce definition.

		Args:
			platform (str): OS name/version
			browser (str): browsers to be used
			versions ([]): single or list of browser versions to create definitions for

		Returns:
			[]: array of browser definitions
		"""
		if type(versions) is not list:
			versions = [versions]

		browsers = []
		for version in versions:

			capabilities = {
				"platform": platform,
				"browserName": browser,
				"version": "{}".format(version),
				"idleTimeout": 1500,
				"disablePopupHandler": True,
				"screenResolution": "1600x1200",
				"autoAcceptAlerts": True,
				"acceptSslCerts": True,
				"recordVideo": True,
				"recordMp4": True
			}

			log_all = browser_override = bool(int(
				os.environ.get('BROWSERS_LOG_ALL', 0)))
			if log_all:
				capabilities['loggingPrefs'] = {'browser': 'ALL'}

			browsers.append(capabilities)
		return browsers

	@classmethod
	def iphone(cls, versions):
		"""
		Create an iOS sauce definition.

		Args:
			versions ([]): signle or list of iOS (OS) versions to create definitions for

		Returns:
			[]: array of browser definitions
		"""
		if type(versions) is not list:
			versions = [versions]

		devices = []
		for version in versions:
			devices.append({
			"platform": "OS X 10.10",
			"browserName": "iphone",
			"version": "{}".format(version),
			"deviceName": "iPhone 6",
			"browser": "safari",
			"deviceOrientation": "portrait",
			"disablePopupHandler": True,
			"idleTimeout": 300
		})
		return devices

	@classmethod
	def android(cls, versions):
		"""
		Create an Android sauce definition.

		Args:
			versions ([]): signle or list of Android (OS) versions to create definitions for

		Returns:
			[]: array of browser definitions
		"""
		if type(versions) is not list:
			versions = [versions]

		devices = []
		for version in versions:
			devices.append({
			"platform": "Linux",
			"browserName": "Android",
			"version": "{}".format(version),
			"deviceName": "Samsung Galaxy S5 Emulator",
			"deviceOrientation": "portrait",
			"screenResolution": "800x1280",
			"disablePopupHandler": True,
			"idleTimeout": 300
		})
		return devices


# run setup on module load
Browsers.setup()
