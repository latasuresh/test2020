import sys
import time

from selenium.common.exceptions import NoSuchFrameException

from automations.core.base_element import TIMEOUT
from automations.utils.log import Log


class WindowMixin(object):
	"""Window handling.
	"""

	def setup(self):
		pass

	@property
	def current_url(self):
		"""The current page URL.
		"""
		return self.driver.current_url

	def has_title(self, title, timeout=TIMEOUT):
		"""Wait until the page title matches the expected value.

		Args:
			title (str): the expected page title
		"""
		self.wait_until(lambda _: title == self.driver.title, timeout=timeout)

	def initial_window(self):
		"""Get the first window in the driver.

		Returns:
			Window: the drivers initial selenium window
		"""
		return self.driver.window_handles[0]

	def current_window(self):
		"""Get the currrently shown window in the driver.

		Returns:
			Window: the drivers current selenium window
		"""
		return self.driver.current_window_handle

	def open_url_in_new_window(self, url):
		"""Open a new window, switch to it and load the requested URL.

		Args:
			url (str): the new window URL

		Returns:
			window: the new window
		"""
		new_window_index = len(set(self.driver.window_handles))
		self.driver.execute_script('''window.open("about:blank", "_blank");''')
		self.wait_until(lambda _: len(self.driver.window_handles) > new_window_index)
		self.driver.switch_to_window(self.driver.window_handles[new_window_index])
		self.driver.get(url)
		return self.driver.window_handles[new_window_index]

	def open_window(self, action):
		"""Open a new window using provided action, returning a handle to that window.

		Args:
			action (lambda): a lambda that triggers the new window

		Returns:
			window: the new window
		"""
		window_handles = set(self.driver.window_handles)
		action(self)
		self.wait_until(lambda _: len(self.driver.window_handles) > len(window_handles))
		new_window_handle = (set(self.driver.window_handles) - window_handles).pop()
		self.driver.switch_to.window(new_window_handle)
		return new_window_handle

	def switch_to_window(self, window=None, index=0):
		"""Switch to the requested window or index, using the window reference if provided.

		Args:
			window (Window): the window reference
			index (int): the window index
		"""
		if window:
			self.driver.switch_to.window(window)
		else:
			self.driver.switch_to.window(self.driver.window_handles[index])

	def refresh(self, timeout=TIMEOUT):
		"""Refresh the current page.

		Args:
			timeout (int): timeout for page load
		"""
		# first try the refresh with 1 retry on exception
		try:
			self.driver.refresh()
		except:
			try:
				self.wait(1)
				self.driver.refresh()
			except Exception as ex:
				# finally log and raise the last exception
				msg = "Error refreshing page [{} >> {}]".format(self.name, self.url)
				raise Exception, msg, sys.exc_info()[2]

		# accept the alert if present
		try:
			self.wait(1)
			self.driver.switch_to_alert().accept()
		except:
			pass

		# wait for load to complete
		self.wait_until(lambda _:
					self.execute_script('''return document.readyState == "complete"''', log=False)
					and
					self.driver.find_element_by_tag_name("html") != None,
					timeout=timeout, desc="Page completely loaded")
		Log.logger.info("{}Reloaded tab".format(self._log_prefix()))


	def close_tab(self):
		"""Close the current tab.
		"""
		try:
			self.driver.close()
		except:
			try:
				time.sleep(1)
				self.driver.close()
			except Exception as ex:
				# finally log and raise the last exception
				msg = "Error closing tab [{} >> {}]".format(self.name, self.url)
				raise Exception, msg, sys.exc_info()[2]

		# accept the alert if present
		try:
			self.driver.switch_to_alert().accept()
		except:
			pass

	def get_page_sources(self):
		"""Get source HTML for the entire page content.

		Returns
			(str, [str]): the base page source and an array of frame sources
		"""
		self.driver.switch_to.default_content()
		page_source = self.driver.page_source.encode("UTF-8")
		frame_sources = []
		iframes = self.list_by_selector("iframe", "Page iFrames")
		for iframe in iframes.all():
			self.driver.switch_to.default_content()
			try:
				iframe.driver.switch_to.frame(iframe.web_element)
				frame_sources.append(self.driver.page_source.encode("UTF-8"))
			except NoSuchFrameException:
				# an iframe element existing does not guarantee it
				# has content
				msg = "<html><body>Frame did not exist</body></html>"
				frame_sources.append(msg.encode("UTF-8"))

		return (page_source, frame_sources)
