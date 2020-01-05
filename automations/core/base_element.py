import logging
import re
import time
import traceback

import requests
from selenium.common.exceptions import (
	InvalidElementStateException,
	NoSuchElementException,
	StaleElementReferenceException,
	TimeoutException
)
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait

from automations.utils.log import Log

TIMEOUT = 30
DEBUG = False

"""This is the standard attribute name used by your pages to identify elements
"""
DEFAULT_ATTR_ID = "data-test-id"

logger = logging.getLogger("LOG") # outputs to main console during Jenkins runs

def debug(msg):
	if DEBUG:
		Log.logger.info(msg)

##################################################################################################################

class EC():
	"""Builder-pattern element conditions.
	"""

	def __init__(self):
		self.conditions = []
		self._description = []

	def copy(self):
		ec = EC()
		ec.conditions = list(self.conditions)
		ec._description = list(self._description)
		return ec

	def visible(self):
		"""Add a condition requiring an element is visible.
		"""
		self.conditions.append(lambda element: element.is_displayed())
		self._description.append("VISIBLE")
		return self

	def invisible(self):
		"""Add a condition requiring an element is invisible.
		"""
		self.conditions.append(lambda element: not element.is_displayed())
		self._description.append("INVISIBLE")
		return self

	def enabled(self):
		"""Add a condition requiring an element is invisible.
		"""
		self.conditions.append(lambda element: element.is_enabled())
		self._description.append("ENABLED")
		return self

	def disabled(self):
		"""Add a condition requiring an element is invisible.
		"""
		self.conditions.append(lambda element: not element.is_enabled())
		self._description.append("DISABLED")
		return self

	def clickable(self):
		"""Add a condition requiring an element is clickable.
		"""
		self.conditions.append(lambda element: element.is_displayed() and element.is_enabled())
		self._description.append("CLICKABLE")
		return self

	def selected(self):
		"""Add a condition requiring an element is selected.
		"""
		self.conditions.append(lambda element: element.is_selected())
		self._description.append("SELECTED")
		return self

	def not_selected(self):
		"""Add a condition requiring an element is not selected.
		"""
		self.conditions.append(lambda element: not element.is_selected())
		self._description.append("NOT SELECTED")
		return self

	def text(self, text):
		"""Add a condition requiring an element text contains the supplied string.

		Args:
			text (str): the text that the element text must contain
		"""
		self.conditions.append(lambda element: element.is_displayed() and text in element.text)
		self._description.append("TEXT:'{}'".format(text))
		return self

	def _count(self):
		"""Check the number of conditions active.

		Returns:
			int: the condition count
		"""
		return len(self.conditions)

	def _evaluate_for(self, element):
		"""Evaluate the list of elements for all conditions, returning an array of all elements that pass all conditions.

		Args:
			elements ([WebElement]): array of elements to check

		Returns:
			[WebElement]: array of passing elements
		"""
		for condition in self.conditions:
			if not condition(element):
				return False
		return True

	def _evaluate_for_list(self, elements):
		"""Evaluate the list of elements for all conditions, returning an array of all elements that pass all conditions.

		Args:
			elements ([WebElement]): array of elements to check

		Returns:
			[WebElement]: array of passing elements
		"""
		passing = []
		for element in elements:
			element_passing = True
			for condition in self.conditions:
				if not condition(element):
					element_passing = False
					break
			if element_passing:
				passing.append(element)
		return passing

	@property
	def description(self):
		return "[{}]".format(" ".join(self._description))

##################################################################################################################

class Text():
	"""Text match types.
	"""

	EXACT = 1
	SUBSTRING = 2
	REGEX = 3

	@classmethod
	def element_condition(cls, text, match):
		condition = None
		if match == cls.REGEX:
			return lambda element: re.compile(text).match(element.text)
		elif match == cls.SUBSTRING:
			return lambda element: text in element.text
		else:
			return lambda element: text == element.text

##################################################################################################################

class BaseElement(object):
	"""	Core element represemtation shared by page, iframe, section and element.
	"""

	def __init__(self, driver, by=None, value=None, parent=None, name=None):
		super(BaseElement, self).__init__()
		self.driver = driver
		self.by = by
		self.value = value
		self.parent = parent
		self.name = name
		self.conditions = EC()
		self.setup()

	def combine_selectors(self):
		"""Check parent to see if the selector can be combined with this
		element to reduce queries
		"""

		# bad circular reference but going with the quick solution for now
		# ideally sort this out so we don't need this

		from automations.core.element import Iframe

		if self.parent != None and self.parent.by == By.CSS_SELECTOR and \
			self.by == By.CSS_SELECTOR and not isinstance(self.parent, Iframe):
			self.value = self.parent.value + " " + self.value
			self.parent = self.parent.parent

	def setup(self):
		"""Override this method in page/section/iframe implementations and initialise elements here.
		"""
		return True

	@property
	def description(self):
		"""Element description.

		Returns:
			str: the maximum detail ofr name and value that is available
		"""
		if self.value:
			if self.name:
				return "[" + self.name + ": " + self.value + "]"
			else:
				return "[" + self.value + "]"
		else:
			if self.name:
				return "[" + self.name + "]"
			else:
				return "[Unknown]"

	def execute_script(self, script_string, once_only=False, retry=0, log=True,
		description=None):
		"""Execute a JS script with some resilience/retries.

		Args:
			script_string (str): the JS script to be executed
			once_only (bool): don't retry this request if it fails
			retry (int): current retry number
			log (bool): log script details in console
			description (str): optional string describing js script function
		"""
		if log:
			if not description:
				description = (script_string[:50] + '..') if len(script_string) > 50 else script_string
			Log.logger.info("{}execute_script: {}".format(self._log_prefix(), description))
		try:
			self.driver.switch_to.default_content()
			return self.driver.execute_script(script_string)
		except:
			if once_only or retry >= 5:
				raise
			self.wait(2)
			return self.execute_script(script_string, retry=retry + 1, log=log,
				description=description)

	###################################################################################################################
	### conditions
	###################################################################################################################

	def visible(self):
		"""Add a 'visible' condition/requirement for matching this element on the page.

		Returns:
			BaseElement: this element for chaining
		"""
		self.conditions.visible()
		return self

	def invisible(self):
		"""Add a 'invisible' condition/requirement for matching this element on the page.

		Returns:
			BaseElement: this element for chaining
		"""
		self.conditions.invisible()
		return self

	def enabled(self):
		"""Add a 'enabled' condition/requirement for matching this element on the page.

		Returns:
			BaseElement: this element for chaining
		"""
		self.conditions.enabled()
		return self

	def disabled(self):
		"""Add a 'disabled' condition/requirement for matching this element on the page.

		Returns:
			BaseElement: this element for chaining
		"""
		self.conditions.disabled()
		return self

	def clickable(self):
		"""Add a 'clickable' condition/requirement for matching this element on the page.

		Returns:
			BaseElement: this element for chaining
		"""
		self.conditions.clickable()
		return self

	def selected(self):
		"""Add a condition requiring an element is selected.
		"""
		self.conditions.selected()
		return self

	def not_selected(self):
		"""Add a condition requiring an element is not selected.
		"""
		self.conditions.not_selected()
		return self

	def has_text(self, text):
		"""Add a 'text' condition/requirement for matching this element on the page.

		Returns:
			BaseElement: this element for chaining
		"""
		self.conditions.text(text)
		return self

	###################################################################################################################
	### waits
	###################################################################################################################

	def wait(self, seconds):
		"""Wait for the specified time.

		Args:
			seconds (int): time in seconds to wait
		"""
		target = time.time() + seconds
		self.wait_until(lambda _: target < time.time(), timeout=seconds + 2)

	def wait_until(self, condition, desc=None, tick=0.5, timeout=TIMEOUT):
		"""Wait until a condition passes.

		Args:
			condition (lambda): the condition to verify
			desc (str): description of the expectation
			tick (float): interval between retries (seconds)
			timeout (int): maximum time to wait (seconds)

		Returns:
			the result of the condition
		"""
		exc = None
		# include buffer to allow at least 1 regular tick
		end = time.time() + timeout + 0.9
		while(time.time() <= end):
			try:
				result = condition(self)
				if result != False:
					return result
			except Exception as iter_exc:
				exc = iter_exc
			time.sleep(tick)
		if exc:
			raise exc
		if desc:
			desc = "{}Timeout waiting for: {}".format(self._log_prefix(), desc)
		else:
			desc = "{}Timeout waiting for condition.".format(self._log_prefix())
		raise TimeoutException(desc)

	def _try(self, condition, debug=DEBUG):
		"""Safely run the provided lambda.

		Args:
			condition (lambda): the lambda to be run
			debug (bool): true to print exceptions

		Returns:
			bool: the result of the condition if it completes, otherwise False
		"""
		try:
			return condition(self)
		except:
			if debug:
				traceback.print_exc()
			return False

	def safe_try(self, fn, *args, **kwargs):
		"""Safely run the referenced function ignoring exceptions.

		Args:
			fn (fn): the function ref
			args (args): funtion params
			kwargs (kwargs): funtion keyword params

		Returns:
			value: the result of the condition if it completes, otherwise False
		"""
		try:
			# function + args
			return fn(*args, **kwargs)
		except Exception as e:
			if debug:
				logger.exception("Condition failed with exception")
			return False

	###################################################################################################################
	### internal
	###################################################################################################################

	def _windows_env(self):
		"""Check the driver capabilities to see if we are running on Windows.

		Returns:
			bool: True if windows platform detected
		"""
		caps = self.driver.desired_capabilities
		return 'platformName' in caps and 'windows' in caps['platformName']

	def _find(self, timeout=TIMEOUT):
		"""Locate this element on the page waiting for a max time of 'timeout'.

		Args:
			timeout (int): the max time to wait for the element

		Raises:
			TimeoutException: if the element is not located
		"""
		self.wait_until(lambda _: self._find_now(), timeout=timeout)
		return self

	def _find_parent_frame(self):
		"""Locate the parent frame if there is one.

		Returns:
			element: the parent frame or None if parent context is a page
		"""
		from .element import Page, Iframe
		if not self.parent:
			return None
		if isinstance(self.parent, Page):
			return None
		if isinstance(self.parent, Iframe):
			return self.parent
		return self.parent._find_parent_frame()

	def _find_root(self, indent=''):
		"""Find the root/parent of this element'.

		Returns:
			WebElement: the parent selenium WebElement if one exists on the
				page at this time
		"""
		if self.by is None and self.value is None:
			# detatched list element
			if not self.web_element:
				raise Exception("{}Element [{}] is a list element but "
					"is missing it's web element reference".format(
						self._log_prefix(), self.name))
			return self.web_element
		if self.parent:
			try:
				self.parent._find_now(indent=indent)
				return self.parent.web_element
			except:
				raise NoSuchElementException(
					"{}Could not locate parent: {} for element: [{}]"
					.format(self._log_prefix(), self.parent.description,
						self.name))
		else:
			self.driver.switch_to.default_content()
			return None

	def _name(self):
		"""Element name, returning the query string if not named.

		Returns:
			str: The name if available, otherwise the query string/value
		"""
		if self.name is None:
			return self.value
		else:
			return self.name

	def _log_prefix(self):
		"""Driver name log helper.

		Returns:
			str: logging prefix string with the driver name
		"""
		return self.driver.driver_name + " >> "
