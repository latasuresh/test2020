import re

from selenium.common.exceptions import TimeoutException

from automations.core.base_element import TIMEOUT, debug


class ElementsAbsenceMixin(object):
	"""Methods for verifying that list elements are not present.
	"""

	def setup(self):
		pass

	def no_element_with_attr(self, attribute, value, timeout=TIMEOUT):
		"""Wait until an element is not found in this list which has the provided attribute and value.

		Args:
			attribute (str): the attribute name
			value (str): the value that must be absent
			timeout (int): max time to wait
		"""
		self._no_element_for(lambda element: value == element.get_attribute(attribute), timeout,
			u"has value [{}] for attribute [{}]".format(attribute, value))

	def no_element_with_text(self, text, timeout=TIMEOUT):
		"""Wait until an element is not found in this list which has the provided text.

		Args:
			text (str): the text that must be absent
			timeout (int): max time to wait
		"""
		self._no_element_for(lambda element: text == element.text, timeout,
			u"has text [{}]".format(text))

	def no_element_with_text_containing(self, text, timeout=TIMEOUT):
		"""Wait until an element is not found in this list which contains the provided text.

		Args:
			text (str): the substring to be matched as absent
			timeout (int): max time to wait
		"""
		self._no_element_for(lambda element: text in element.text, timeout,
			u"has text containing [{}]".format(text))

	def no_element_with_text_matching(self, regex, timeout=TIMEOUT):
		"""Wait until an element is not found in this list which matches the provided regex.

		Args:
			regex (str): regex for the element text that must be absent
			timeout (int): max time to wait
		"""
		self._no_element_for(lambda element: re.compile(regex).match(element.text), timeout,
			u"has text matching [{}]".format(regex))

	def _no_element_for(self, element_condition, timeout, description):
		"""Wait until an element is not found in this list which matches the provided condition.

		Args:
			element_condition (lambda): condition to be checked for each element
			timeout (int): max time to wait
			description (str): description of the condition

		Returns:
			bool: True if there is no matching element
		"""
		try:
			self.wait_until(lambda _: self._not_found_in_list(element_condition), timeout=timeout)
		except TimeoutException:
			raise TimeoutException("{}Timeout waiting for absence of element matching '{}' on {}"
				.format(self._log_prefix(), description, self.description))

	def _not_found_in_list(self, element_condition):
		"""Check that an element is not found in this list matching the provided condition at this time.

		Args:
			element_condition (lambda): condition to be checked for each element

		Returns:
			bool: True if there is no matching element
		"""
		try:
			self._find_now()
			for element in self.web_elements:
				if element_condition(element):
					return False
			return True
		except:
			return True
