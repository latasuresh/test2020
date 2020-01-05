import re

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By

from automations.core.base_element import TIMEOUT, Text, debug


class ElementsPresenceMixin(object):
	"""Methods for checking that an element is present in a list.
	"""

	def setup(self):
		pass

	################################
	### Any attribute
	################################

	def element_with_attr(self, attribute, value, timeout=TIMEOUT):
		"""Wait until an element is found in this list which has the provided attribute and value.

		Args:
			attribute (str): the attribute name
			value (str): the value that must be present
			timeout (int): max time to wait
		"""
		return self._elements_for(lambda element: value == element.get_attribute(attribute), timeout,
			u"has value [{}] for attribute [{}]".format(attribute, value))[0]

	################################
	### Element text
	################################

	def element_with_text(self, text, timeout=TIMEOUT):
		"""Wait until an element is found in this list which has the provided text.

		Args:
			text (str): the text that must be present
			timeout (int): max time to wait
		"""
		return self._elements_for(Text.element_condition(text, Text.EXACT), timeout,
			u"has text [{}]".format(text))[0]

	def element_with_text_containing(self, text, timeout=TIMEOUT):
		"""Wait until an element is found in this list which contains the provided text.

		Args:
			text (str): the substring to be matched as present
			timeout (int): max time to wait
		"""
		return self._elements_for(Text.element_condition(text, Text.SUBSTRING), timeout,
			u"has text containing [{}]".format(text))[0]

	def element_with_text_matching(self, regex, timeout=TIMEOUT):
		"""Wait until an element is found in this list which matches the provided regex.

		Args:
			regex (str): regex for the element text that must be present
			timeout (int): max time to wait
		"""
		return self._elements_for(Text.element_condition(regex, Text.REGEX), timeout,
			u"has text matching [{}]".format(regex))[0]

	################################
	### Elements text
	################################

	def elements_with_text(self, text, timeout=TIMEOUT):
		"""Wait until an element is found in this list which has the provided text.

		Args:
			text (str): the text that must be present
			timeout (int): max time to wait
		"""
		return self._elements_for(Text.element_condition(text, Text.EXACT), timeout,
			u"has text [{}]".format(text), multiple=True)

	def elements_with_text_containing(self, text, timeout=TIMEOUT):
		"""Wait until an element is found in this list which contains the provided text.

		Args:
			text (str): the substring to be matched as present
			timeout (int): max time to wait
		"""
		return self._elements_for(Text.element_condition(text, Text.SUBSTRING), timeout,
			u"has text containing [{}]".format(text), multiple=True)

	def elements_with_text_matching(self, regex, timeout=TIMEOUT):
		"""Wait until an element is found in this list which matches the provided regex.

		Args:
			regex (str): regex for the element text that must be present
			timeout (int): max time to wait
		"""
		return self._elements_for(Text.element_condition(regex, Text.REGEX), timeout,
			u"has text matching [{}]".format(regex), multiple=True)

	################################
	### Element pairs
	################################

	def element_with_attr_and_relative(self, attribute, value, relative_xpath, timeout=TIMEOUT):
		"""Wait until an element is found in this list which has the provided attribute, value and relative element.

		Args:
			attribute (str): the attribute name
			value (str): the value that must be present
			timeout (int): max time to wait
		"""
		return self._elements_for(lambda element: value == element.get_attribute(attribute), timeout,
			u"has value [{}] for attribute [{}] relative [{}]".format(attribute, value, relative_xpath))[0]

	def element_with_text_and_relative(self, text, relative_xpath, timeout=TIMEOUT):
		"""Wait until an element is found in this list which has the provided text and relative element.

		Args:
			text (str): the text that must be present
			timeout (int): max time to wait
		"""
		return self._elements_with_condition_and_relative(Text.element_condition(text, Text.EXACT), relative_xpath, timeout,
			u"has text [{}] and relative [{}]".format(text, relative_xpath))[0]

	def element_with_text_containing_and_relative(self, text, relative_xpath, timeout=TIMEOUT):
		"""Wait until an element is found in this list which contains the provided text and relative element.

		Args:
			text (str): the substring to be matched as present
			timeout (int): max time to wait
		"""
		return self._elements_with_condition_and_relative(Text.element_condition(text, Text.SUBSTRING), relative_xpath, timeout,
			u"has text containing [{}] and relative [{}]".format(text, relative_xpath))[0]

	def element_with_text_matching_and_relative(self, text, relative_xpath, timeout=TIMEOUT):
		"""Wait until an element is found in this list which matches the provided regex and relative element.

		Args:
			regex (str): regex for the element text that must be present
			timeout (int): max time to wait
		"""
		return self._elements_with_condition_and_relative(Text.element_condition(text, Text.REGEX), relative_xpath, timeout,
			u"has text matching [{}] and relative [{}]".format(text, relative_xpath))[0]

	################################
	### Internal util
	################################

	def _elements_for(self, element_condition, timeout, description, multiple=False):
		"""Wait until an element exists in this list matching the provided condition at this time.

		This requires that there be only one matching element, more than one match will also fail.

		Args:
			element_condition (lambda): condition to be checked for each element
			timeout (int): max time to wait
			description (str): description of the condition
			multiple (bool): defaults to false which requires that only one element matches, if true one or more elements may match

		Returns:
			[Element]: array of element results if found
		"""
		results = []
		try:
			self.wait_until(lambda _: self._find_in_list(element_condition,
				results, multiple=multiple), timeout=timeout)
		except TimeoutException:
			raise TimeoutException(u"{}Timeout waiting for '{}' on {}"
				.format(self._log_prefix(), description, self.description))
		except Exception as ex:
			raise Exception(u"{}Failed to locate element '{}' on {} with error: {}"
				.format(self._log_prefix(), description, self.description, ex))
		from .element import Element
		element_results = []
		for element in results:
			result = Element(self.driver, parent=self, name=u"{}:list_item"
				.format(self.name))
			result.web_element = element
			element_results.append(result)
		return element_results

	def _elements_with_condition_and_relative(self, element_condition, relative_xpath, timeout, description, multiple=False):
		"""Wait until we locate an element with the specified text that also has relative element matching the xpath.

		Some elements lack sufficient content/context in isolation and require matching a pair of elements.

		Args:
			text (str): the element text to be matched
			relative_xpath (str): relative xpath to another element that must exist
			timeout (int): max time to wait
			multiple (bool): defaults to false which requires that only one element matches, if true one or more elements may match
		"""
		def find_it(element):
			try:
				return element_condition(element) and element.find_element(By.XPATH, relative_xpath) != None
			except:
				return False
		return self._elements_for(find_it, timeout, description, multiple=multiple)

	def _find_in_list(self, element_condition, results, multiple=False):
		"""Check that an element exists in this list matching the provided condition at this time.

		Args:
			element_condition (lambda): condition to be checked for each element
			results (array<Element>): array of matching elements
			multiple (bool): defaults to false which requires that only one element matches, if true one or more elements may match

		Returns:
			bool: True if there are no matching element(s)
		"""
		found = 0
		del results[:]
		if self._find_now():
			for element in self.web_elements:
				if element_condition(element):
					results.append(element)
					found += 1
		if found == 1 or (found > 1 and multiple):
			return True
		else:
			return False
