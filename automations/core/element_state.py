import re

import requests
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By

from automations.core.base_element import TIMEOUT
from automations.utils.log import Log


class ElementStateMixin(object):
	"""Element state/content.
	"""

	def setup(self):
		pass

	def is_displayed(self, timeout=TIMEOUT):
		"""Check if this element is displayed (note that selenium 'displayed'
		is not guaranteed to mean visible or clickable).

		Args:
			timeout (int): desired timeout, default to TIMEOUT

		Returns:
			bool: True if this element exists and is displayed, otherwise False
		"""
		return self.exists(timeout=timeout) and self.web_element.is_displayed()

	def is_displayed_now(self):
		"""Check if this element is displayed right now(note that selenium
		'displayed' is not guaranteed to mean visible or clickable).

		Returns:
			bool: True if this element exists and is displayed, otherwise False
		"""
		return self.exists(timeout=0) and self.web_element.is_displayed()

	def not_displayed(self, timeout=TIMEOUT):
		"""Verify that an element is either not present or not visible.

		Args:
			timeout (int): desired timeout, default to TIMEOUT

		Returns:
			bool: True if this element is absent or invisible
		"""
		return self.wait_until(lambda _: not self.exists(0)
			or not self.web_element.is_displayed(), timeout=timeout,
			desc="Element has disappeared: {}".format(self.name))

	def is_enabled(self, timeout=TIMEOUT):
		"""Check if this element is enabled.

		Args:
			timeout (int): desired timeout, default to TIMEOUT

		Returns:
			bool: True if this element is enabled, otherwise False
		"""
		return self.exists(timeout=timeout) and self.web_element.is_enabled()

	def is_selected(self, timeout=TIMEOUT):
		"""Check if this element is selected.

		Args:
			timeout (int): desired timeout, default to TIMEOUT

		Returns:
			bool: True if this element is selected, otherwise False
		"""
		return self.exists(timeout=timeout) and self.web_element.is_selected()

	def is_clickable(self, timeout=TIMEOUT):
		"""Check if this element is clickable.

		Args:
			timeout (int): desired timeout, default to TIMEOUT

		Returns:
			bool: True if this element is clickable (visible and enabled),
				otherwise False
		"""
		return self.exists(timeout=timeout) and self.web_element.is_enabled() \
			and self.web_element.is_displayed()

	###########################################################################

	def verify_visible(self, timeout=TIMEOUT):
		"""Verify element is visible.

		Args:
			timeout (int): desired timeout, default to TIMEOUT

		Returns:
			self: For use with wait_until
		"""
		return self.extend().visible().verify(timeout)

	def verify_invisible(self, timeout=TIMEOUT):
		"""Verify element is invisible.

		Args:
			timeout (int): desired timeout, default to TIMEOUT

		Returns:
			self: For use with wait_until
		"""
		return self.extend().invisible().verify(timeout)


	def verify_enabled(self, timeout=TIMEOUT):
		"""Verify element is enabled.

		Args:
			timeout (int): desired timeout, default to TIMEOUT

		Returns:
			self: For use with wait_until
		"""
		return self.extend().enabled().verify(timeout)

	def verify_disabled(self, timeout=TIMEOUT):
		"""Verify element is disabled.

		Args:
			timeout (int): desired timeout, default to TIMEOUT

		Returns:
			self: For use with wait_until
		"""
		return self.extend().disabled().verify(timeout)

	def verify_clickable(self, timeout=TIMEOUT):
		"""Verify element is clickable.

		Args:
			timeout (int): desired timeout, default to TIMEOUT

		Returns:
			self: For use with wait_until
		"""
		return self.extend().clickable().verify(timeout)

	def verify_selected(self, timeout=TIMEOUT):
		"""Verify element is selected.

		Args:
			timeout (int): desired timeout, default to TIMEOUT

		Returns:
			self: For use with wait_until
		"""
		return self.extend().selected().verify(timeout)

	def verify_not_selected(self, timeout=TIMEOUT):
		"""Verify element is not selected.

		Args:
			timeout (int): desired timeout, default to TIMEOUT

		Returns:
			self: For use with wait_until
		"""
		return self.extend().not_selected().verify(timeout)

	###########################################################################

	def has_attribute_value(self, attribute, value, timeout=TIMEOUT):
		"""Wait until an element is found which has the specified attribute and value.

		Args:
			attribute (str): the attribute name
			value (str): the value that must be present
			timeout (int): max time to wait
		"""
		self.verify()
		try:
			self.wait_until(
				lambda _: self._try(lambda _: value ==
					self.web_element.get_attribute(attribute)),
				timeout=timeout)
		except TimeoutException:
			raise TimeoutException(u"{}Timeout waiting for element attr '{}' "
				"to be '{}'".format(self._log_prefix(), attribute, value))

	def value_is(self, value, timeout=TIMEOUT):
		"""Wait until an element is found which has the specified attribute value.
		Normally used for input type=text

		Args:
			value (str): the value that must be present
			timeout (int): max time to wait
		"""
		self.has_attribute_value("value", value, timeout)

	def text(self):
		"""Get the current element text if the element has been located.

		Returns:
			str: the element text
		"""
		element_text = ''
		if self.web_element:
			element_text = self.web_element.text
			if not element_text:
				attributes = ['value', 'textContent', 'innerText', 'innerHtml']
				for attribute in attributes:
					element_text = self.attribute(attribute)
					if element_text:
						break
		return element_text

	def attribute(self, attribute):
		"""Get the current element attribute value if the element has been located.

		Arags:
			attribute (str): the attribute name

		Returns:
			str: the attribute text
		"""
		if self.web_element:
			return self.web_element.get_attribute(attribute)
		return ''

	def text_is(self, text, ignore_case=True, timeout=TIMEOUT):
		"""Wait until this elements text fully matches the provided text.

		Args:
			text (str): the text to match
			ignore_case (bool): True to compare ignoring case (default True)
			timeout (int): the timeout, defaults to TIMEOUT
		"""
		self.verify()

		if ignore_case:
			text = text.lower()

		def _text_is():
			_text_is._text = "(ELEMENT_TEXT_IS_EMPTY)"
			element_text = self._try(lambda _: self.text())
			if not element_text:
				return False
			if ignore_case:
				element_text = element_text.lower()
			_text_is._text = element_text
			return element_text == text

		try:
			self.wait_until(lambda _: _text_is(), timeout=timeout)
		except TimeoutException:
			raise TimeoutException(u"{}Timeout waiting for element {}"
				"with text {} to be '{}'".format(self._log_prefix(), self.description, _text_is._text, text))

	def text_contains(self, text, ignore_case=True, timeout=TIMEOUT):
		"""Wait until this elements text contains the provided text.

		Args:
			text (str): the regex to match
			ignore_case (bool): True to compare ignoring case (default True)
			timeout (int): the timeout, defaults to TIMEOUT
		"""
		self.verify()

		if ignore_case:
			text = text.lower()

		def _text_contains():
			_text_contains._text = "(ELEMENT_TEXT_IS_EMPTY)"
			element_text = self._try(lambda _: self.text())
			if not element_text:
				return False
			if ignore_case:
				element_text = element_text.lower()
			_text_contains._text = element_text
			return text in element_text

		try:
			self.wait_until(lambda _: _text_contains(), timeout=timeout)
		except TimeoutException:
			raise TimeoutException(u"{}Timeout waiting for element {} with text {}"
				"to contain '{}'".format(self._log_prefix(), self.description, _text_contains._text, text))

	def text_matches(self, regex, timeout=TIMEOUT):
		"""Wait until this elements text matches the provided regex.

		Args:
			regex (str): the regex to match
			timeout (int): the timeout, defaults to TIMEOUT
		"""
		self.verify()

		def _text_matches():
			_text_matches._text = "(ELEMENT_TEXT_IS_EMPTY)"
			element_text = self._try(lambda _: self.text())
			if not element_text:
				return False
			_text_matches._text = element_text
			return re.compile(regex).match(element_text)

		try:
			self.wait_until(lambda _: self._try(lambda _: _text_matches()), timeout=timeout)
		except TimeoutException:
			raise TimeoutException(u"{}Timeout waiting for element {} with text {}"
				"to match '{}'".format(self._log_prefix(), self.description, _text_matches._text, regex))

	def url_ends_with(self, urls, timeout=TIMEOUT):
		""" Wait for a URL match ending with the any of the specified strings.

		Args:
			urls ([str]): list of URL string suffixes
			timeout (int): for this search
		"""
		self.wait_until(
			lambda _: any(
				self.driver.current_url.endswith(p)
				for p in urls
			),
			timeout=timeout, desc="Url ends with one of: {}".format(urls)
		)

	def verify_all_links(self, whitelist, verify_ssl):
		"""Check that all links contained below this element result in a valid
		page.

		Args:
			whitelist (str): space separated list of URLs to be ignored
			verify_ssl (bool): whether to verify SSL
		"""
		session = requests.session()

		try:
			link_elements = self._list(By.TAG_NAME, "a", "Page links") \
				._find(timeout=1).web_elements
			links_array = []

			for element in link_elements:
				href = element.get_attribute('href')
				if href and not href.startswith(tuple(whitelist.split(' '))):
					links_array.append(href)

			links = set(links_array)
			broken = {}

			for link in links:
				self._try_link(link, verify_ssl, session, 1, broken)

			if len(broken) > 0:
				err = "Broken links:"
				for link in broken:
					Log.logger.error("{}Broken link [{}]: {}".format(
						self._log_prefix(), broken[link], link))
				err = "{}Broken links found: [{}]" \
					.format(self._log_prefix(), broken)
				raise Exception(err)
		except TimeoutException:
			# none found
			pass

	def _try_link(self, link, verify_ssl, session, remaining, broken):
		"""Helper for exception handled link verifications.

		Args:
			link (str): link to be checked
			verify_ssl (bool): whether to verify SSL
			session (Session): the requests.Session to be used
			remaining (int): number of attempts remaining after this one
			broken (map): link to error map for links identified as broken
		"""
		status_code = 0
		try:
			status_code = session.get(link, verify=verify_ssl).status_code
		except Exception as ex:
			status_code = ex.message

		if status_code >= 400:
			if remaining > 0:
				self._try_link(link, verify_ssl, session, remaining - 1, broken)
			else:
				broken[link] = status_code
