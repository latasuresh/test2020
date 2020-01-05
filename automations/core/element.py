import re
import sys
import traceback
from time import sleep, time

import requests
from selenium.common.exceptions import (
	NoSuchElementException,
	StaleElementReferenceException,
	TimeoutException,
	WebDriverException
)
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait

from automations.core.base_element import DEBUG, DEFAULT_ATTR_ID, TIMEOUT, BaseElement
from automations.core.element_actions import ElementActionsMixin
from automations.core.list_element_absence import ElementsAbsenceMixin
from automations.core.list_element_presence import ElementsPresenceMixin
from automations.core.window import WindowMixin
from automations.utils.log import Log

###############################################################################

class Elements(ElementsPresenceMixin, ElementsAbsenceMixin, BaseElement):
	"""Represents any list of elements that match the query/condition.
	"""

	def __init__(self, driver, by=None, value=None, parent=None, name=None):
		super(Elements, self).__init__(driver, by=by, value=value,
			parent=parent, name=name)
		self.web_elements = None

	def detach(self, detach_to_ancestor=False):
		"""Detach from parent.
		Depending on argument, will also search for and reattach
		the element to the root element or the first Iframe it encounters.

		Args:
			detach_to_ancestor (bool): Reattach to root element or iframe
		"""
		ancestor = None
		if detach_to_ancestor:
			ancestor = self
			while ancestor.parent != None:
				ancestor = ancestor.parent
				if isinstance(ancestor, Iframe):
					break
			if ancestor == self:
				ancestor = None
		self.parent = ancestor
		return self

	def extend(self):
		"""Makes a copy that can have conditions added.

		Returns:
			Elements: the copy
		"""
		elements = Elements(self.driver, by=self.by, value=self.value,
			parent=self.parent, name=self.name)
		elements.conditions = self.conditions.copy()
		elements.web_elements = list(self.web_elements)
		return elements

	def size(self):
		"""Check the number of elements currently matching the list selector.

		Returns:
			int: number of elements located
		"""
		try:
			self._find(0)
			return len(self.web_elements)
		except:
			return 0

	def all(self):
		"""Get the list of all currently matching elements.

		Returns:
			[Element]: all matching elements
		"""
		temp = []
		try:
			self._find(0)
			for web_element in self.web_elements:
				element = Element(self.driver, parent=None,
					name=self.name + ": list item")
				element.web_element = web_element
				temp.append(element)
		except:
			pass
		return temp

	def _find_now(self):
		"""Attempt to find this element within it's validated parent hierarchy.

		Returns:
			bool: True if found, False if this list or any of it's parent
				elements are not found
		"""
		try:
			root = self._find_root()
			if not root or self.parent and isinstance(self.parent, Iframe):
				# if no root or parent is iFrame search the whole page
				self.web_elements = self.driver.find_elements(self.by,
					self.value)
			else:
				# otherwise search the root/parent element
				self.web_elements = root.find_elements(self.by, self.value)

			# if conditions then verify
			if self.conditions._count() > 0:

				self.web_elements = self.conditions._evaluate_for_list(
					self.web_elements)

				if len(self.web_elements) == 0:
					self.web_elements = None
					raise NoSuchElementException("{}Could not find any "
						"element {} satisfying conditions {}"
						.format(self._log_prefix(), self.description,
							self.conditions.description))

			# no conditions
			if len(self.web_elements) == 0:
				raise NoSuchElementException("{}Could not find any element {}"
					.format(self._log_prefix(), self.description))
			return True

		except NoSuchElementException as nse:
			raise
		except:
			raise NoSuchElementException("{}Could not find any element {} "
				"satisfying conditions {}"
				.format(self._log_prefix(), self.description,
					self.conditions.description))

###############################################################################

class Element(ElementActionsMixin, WindowMixin, BaseElement):

	def __init__(self, driver, by=None, value=None, parent=None, name=None):
		"""Element represemtation shared by page, iframe, section and element.

		Args:
			driver (WebDriver): the web driver for this element
			by (BY): the selenium BY
			value (str): query string
			parent(Element): the parent element
			name (str): descriptive name for this element
		"""
		super(Element, self).__init__(driver, by=by, value=value,
			parent=parent, name=name)
		self.web_element = None


	def extend(self):
		"""Makes a copy that can have conditions added.

		Returns:
			Element: the copy
		"""
		element = Element(self.driver, by=self.by, value=self.value,
			parent=self.parent, name=self.name)
		element.conditions = self.conditions.copy()
		element.web_element = self.web_element
		return element

	def detach(self, detach_to_ancestor=False):
		"""Detach from parent.
		Depending on argument, will also search for and reattach
		the element to the root element or the first Iframe it encounters.

		Args:
			detach_to_ancestor (bool): Reattach to root element or iframe
		"""
		ancestor = None
		if detach_to_ancestor:
			ancestor = self
			while ancestor.parent != None:
				ancestor = ancestor.parent
				if isinstance(ancestor, Iframe):
					break
			if ancestor == self:
				ancestor = None
		self.parent = ancestor
		return self

	@classmethod
	def add_extension(cls, ext):
		"""Add an extension to the Element class.

		Must implement the 'bind' method.

		Args:
			ext (class): the extension class
		"""
		ext.bind(cls)

	def verify(self, timeout=TIMEOUT):
		"""Check that this element is present and passes it's conditions.

		Verify that this object exists in the DOM.

		Args:
			timeout (int): desired timeout, default to TIMEOUT

		Raises:
			TimeoutException: if the element is not located
		"""
		# have not located or must re-verify conditions
		self._find(timeout=timeout)
		return self

	def gone(self, timeout=TIMEOUT):
		"""Check if this element exists, opposite of verify.

		Args:
			timeout (int): desired timeout, default to TIMEOUT

		Raises:
			TimeoutException: if the element remains past timeout
		"""
		try:
			self.wait_until(lambda _: not self.exists(timeout=0),
				timeout=timeout)
		except TimeoutException:
			raise TimeoutException("{}Timeout waiting for element to be gone "
				"'{}'".format(self._log_prefix(), self.description))

	def exists(self, timeout=TIMEOUT):
		"""Check if this element exists.

		Args:
			timeout (int): desired timeout, default to TIMEOUT

		Returns:
			bool: True if this element exists, otherwise False
		"""
		try:
			self.verify(timeout=timeout)
			return True
		except:
			return False

	################################
	### element
	################################

	def element(self, value, name):
		"""Create an element as a sub element of this element.

		Args:
			value (str): the element test id
			name (str): a descriptive name of the element

		Returns:
			Element: the initialised Element
		"""
		return self._element(By.CSS_SELECTOR, "[{}='{}']"
			.format(DEFAULT_ATTR_ID, value), name)

	def element_by_selector(self, value, name):
		"""Create an element as a sub element of this element by css selector.

		Args:
			value (str): the element query string
			name (str): a descriptive name of the element

		Returns:
			Element: the initialised Element
		"""
		return self._element(By.CSS_SELECTOR, value, name)

	def element_by_xpath(self, value, name):
		"""Create an element as a sub element of this element by xpath.

		Args:
			value (str): the element query string
			name (str): a descriptive name of the element

		Returns:
			Element: the initialised Element
		"""
		return self._element(By.XPATH, value, name)

	def element_by_class(self, value, name):
		"""Create an element as a sub element of this element by class.

		Args:
			value (str): the element query string
			name (str): a descriptive name of the element

		Returns:
			Element: the initialised Element
		"""
		return self._element(By.CLASS_NAME, value, name)

	def _element(self, by, value, name):
		"""Create an element as a sub element of this element.

		Args:
			by (BY): Selenium BY
			value (str): the element query string
			name (str): a descriptive name of the element

		Returns:
			Element: the initialised Element
		"""
		e = Element(self.driver, by=by, value=value, parent=self, name=name)
		e.combine_selectors()
		return e

	################################
	### elements
	################################

	def list(self, value, name):
		"""Create a list as a sub element of this element by DEFAULT_ATTR_ID.

		Args:
			value (str): the list test id
			name (str): a descriptive name of the list

		Returns:
			Elements: the initialised Elements list
		"""
		return self._list(By.CSS_SELECTOR, "[{}='{}']"
			.format(DEFAULT_ATTR_ID, value), name)

	def list_by_selector(self, value, name):
		"""Create a list as a sub element of this element by css selector.

		Args:
			value (str): the list query string
			name (str): a descriptive name of the list

		Returns:
			Elements: the initialised Elements list
		"""
		return self._list(By.CSS_SELECTOR, value, name)

	def list_by_xpath(self, value, name):
		"""Create a list as a sub element of this element by xpath.

		Args:
			value (str): the list query string
			name (str): a descriptive name of the list

		Returns:
			Elements: the initialised Elements list
		"""
		return self._list(By.XPATH, value, name)

	def list_by_class(self, value, name):
		"""Create a list as a sub element of this element by class.

		Args:
			value (str): the list query string
			name (str): a descriptive name of the list

		Returns:
			Elements: the initialised Elements list
		"""
		return self._list(By.CLASS_NAME, value, name)

	def _list(self, by, value, name):
		"""Create a list as a sub element of this element.

		Args:
			by (BY): Selenium BY
			value (str): the list query string
			name (str): a descriptive name of the list

		Returns:
			Elements: the initialised Elements list
		"""
		e = Elements(self.driver, by=by, value=value, parent=self, name=name)
		e.combine_selectors()
		return e

	################################
	### iframe
	################################

	def iframe(self, iframe, value, name):
		"""Initialise an iFrame as a sub element of this element.

		Args:
			iframe (Iframe): the iFrame to be initialised
			value (str): the iFrame test id
			name (str): a descriptive name of the iFrame

		Returns:
			Iframe: the initialised Iframe
		"""
		return self._iframe_by(iframe, By.CSS_SELECTOR, "[{}='{}']"
			.format(DEFAULT_ATTR_ID, value), name)

	def iframe_by_selector(self, iframe, value, name):
		"""Initialise an iFrame as sub element of this element by CSS selector.

		Args:
			iframe (Iframe): the iFrame to be initialised
			value (str): the iFrame query string
			name (str): a descriptive name of the iFrame

		Returns:
			Iframe: the initialised Iframe
		"""
		return self._iframe_by(iframe, By.CSS_SELECTOR, value, name)

	def iframe_by_xpath(self, iframe, value, name):
		"""Initialise an iFrame as a sub element of this element by xpath.

		Args:
			iframe (Iframe): the iFrame to be initialised
			value (str): the iFrame query string
			name (str): a descriptive name of the iFrame

		Returns:
			Iframe: the initialised Iframe
		"""
		return self._iframe_by(iframe, By.XPATH, value, name)

	def _iframe_by(self, iframe, by, value, name):
		"""Initialise an iFrame as a sub element of this element.

		Args:
			by (BY): Selenium BY
			iframe (Iframe): the iFrame to be initialised
			value (str): the iFrame query string
			name (str): a descriptive name of the iFrame

		Returns:
			Iframe: the initialised Iframe
		"""
		iframe.parent = self
		iframe.by = by
		iframe.value = value
		iframe.name = name
		return iframe

	################################
	### section
	################################

	def section(self, section, value, name):
		"""Initialise a section as a sub-element of this element.

		Args:
			section (Section): the section to be initialised
			value (str): the section test id
			name (str): a descriptive name of the section

		Returns:
			Section: the initialised section
		"""
		return self._section_by(By.CSS_SELECTOR, section, "[{}='{}']"
			.format(DEFAULT_ATTR_ID, value), name)

	def section_by_selector(self, section, value, name):
		"""Initialise a section as sub-element of this element by CSS selector.

		Args:
			section (Section): the section to be initialised
			value (str): the section query string
			name (str): a descriptive name of the section

		Returns:
			Section: the initialised section
		"""
		return self._section_by(By.CSS_SELECTOR, section, value, name)

	def section_by_xpath(self, section, value, name):
		"""Initialise a section as a sub-element of this element by xpath.

		Args:
			section (Section): the section to be initialised
			value (str): the section query string
			name (str): a descriptive name of the section

		Returns:
			Section: the initialised section
		"""
		return self._section_by(By.XPATH, section, value, name)

	def _section_by(self, by, section, value, name):
		"""Initialise a section as a sub element of this element.

		Args:
			by (BY): Sekenium BY
			section (Section): the section to be initialised
			value (str): the section query string
			name (str): a descriptive name of the section

		Returns:
			Section: the initialised section
		"""
		section.parent = self
		section.by = by
		section.value = value
		section.name = name
		section.combine_selectors()
		return section

	################################
	### internal
	################################

	def switch_to_default(self):
		"""Convenience method to switch to page context.
		"""
		self.driver.switch_to.default_content()

	def _find_now(self, indent=''):
		"""Attempt to find this element within it's validated parent hierarchy.

		Returns:
			bool: True if found, False if this list or any of it's parent
				elements are not found
		"""
		if self._web_element_valid():
			return True

		try:
			self.web_element = None
			root = self._find_root(indent=indent + '  ')
			elements = self._apply_conditions(self._find_web_elements(root))

			if len(elements) == 1:
				self.web_element = elements[0]
				return True

			if len(elements) == 0:
				raise NoSuchElementException("{}Could not find element {} "
					"satisfying conditions {}".format(self._log_prefix(),
						self.description, self.conditions.description))

			if len(elements) > 1:
				raise NoSuchElementException("{}Multiple matches found for "
					"[{}] >> [{}]".format(self._log_prefix(), self.description,
						elements))
			return True

		except NoSuchElementException as nse:
			raise
		except:
			raise NoSuchElementException("{}Could not find element {} "
				"satisfying conditions {}".format(self._log_prefix(),
					self.description, self.conditions.description))

	def _web_element_valid(self):
		"""Simple check of validity of any previously located Selenium element.

		Verifies that the element is not stale and that is passes any defined
		conditions.
		"""
		if self.web_element:
			try:
				if self.conditions._count() > 0:
					return self.conditions._evaluate_for(self.web_element)
				else:
					self.web_element.is_displayed()
					return True
			except:
				return False
		return False

	def _find_web_elements(self, root):
		"""Perform the Selenium query to find this element from it's root.

		Args:
			root (element): the element from which to perform ths query, if any

		Returns:
			elements: a list of located selenium web elements
		"""
		if not root or self.parent and isinstance(self.parent, Iframe):
			# if no root search the whole page
			return self.driver.find_elements(self.by, self.value)
		else:
			# otherwise search the root/parent element
			return root.find_elements(self.by, self.value)

	def _apply_conditions(self, elements):
		"""Check the Selenium element results, filtering for conditions.

		Args:
			elements ([element]): list of located Selenium web elements

		Returns:
			[element]: list of elements that pass specified conditions
		"""
		if self.by and len(elements) > 0:
			return self.conditions._evaluate_for_list(elements)
		return elements

###############################################################################

class Page(Element):
	"""A top level element which loads the provided URL on init.

	Args:
		driver (WebDriver): the seleniun WebDriver
		url (): the URL to be loaded
		name (): descriptive name for this page
	"""

	def __init__(self, driver, url, name, new_tab=False):
		super(Page, self).__init__(driver, name=name)
		self.url = url
		if url:
			if new_tab:
				self.open_url_in_new_window(url)
			else:
				self.load_url(url)

	def load_url(self, url):
		"""Loads the given url and retries once on failure
		"""
		print "i am here "
		Log.logger.info("{}Loading URL: {}".format(self._log_prefix(), url))
		self.url = url
		try:
			self.driver.get(url)
			print "2"
		except:
			# make one retry after short pause
			try:
				sleep(1)
				self.driver.get(url)
			except Exception as ex:
				# finally log and raise the last exception
				msg = "{}Error loading page [{} >> {}]".format(
					self._log_prefix(), self.name, url)
				Log.logger.info(msg)
				raise Exception, msg, sys.exc_info()[2]

		# accept the alert if present
		try:
			self.driver.switch_to_alert().accept()
		except:
			print "3"
			pass

	def _find_now(self, indent=''):
		"""Attempt to find this element within it's validated parent hierarchy.
		"""
		self.driver.switch_to.default_content()
		return True

###############################################################################

class Iframe(Element):
	"""An iframe, all iframe references should be explicit Iframe objects.
	"""

	def _init(self, driver):
		super(Iframe, self).__init__(driver)
		return self

	def _find_now(self, indent=''):
		"""Attempt to find this element within it's validated parent hierarchy.
		"""
		self.driver.switch_to.default_content()
		if super(Iframe, self)._find_now():
			self.driver.switch_to.frame(self.web_element)
			return True
		return False

###############################################################################

class Section(Element):
	""" An element container defining a portion of a page.
	"""

	def __init__(self, driver):
		super(Section, self).__init__(driver)
