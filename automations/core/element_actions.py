from selenium.webdriver.common.keys import Keys

from automations.core.base_element import TIMEOUT
from automations.core.element_state import ElementStateMixin
from automations.utils.log import Log


class ActionException(Exception):
	"""Thrown when an action fails.
	"""
	pass

class ElementActionsMixin(ElementStateMixin):
	"""Element actions.
	"""

	click_fail_js = []

	def setup(self):
		pass

	def click(self, timeout=TIMEOUT):
		"""Click this element.

		First verifies element state and will perform one click retry on error.
		"""
		self.verify(timeout=timeout)
		Log.logger.info("{}Click: [{}]".format(self._log_prefix(),
			self._name()))
		self._perform_action(lambda _: self.web_element.click())

	def clear(self, timeout=TIMEOUT):
		"""Clear this element (text input).
		"""
		self.verify(timeout=timeout)
		Log.logger.info("{}Clear field: [{}]".format(self._log_prefix(),
			self._name()))
		self._perform_action(lambda _: self.web_element.clear())

	def send_keys(self, *value):
		"""Send keys to this web element.

		Args:
			value (str): string to be sent
		"""
		self.verify()
		valString = None
		for val in value:
			if valString is None:
				valString = val
			else:
				valString = valString + " " + val

		Log.logger.info(u"{}Send keys '{}' to [{}]".format(self._log_prefix(),
			valString, self._name()))
		self._perform_action(lambda _: self.web_element.send_keys(value))

	def page_bottom(self):
		"""Scrolling to the bottom of element (container) height.
		"""
		scrollable = self.verify().web_element
		self.driver.execute_script("arguments[0].scrollTo(0, arguments[0].scrollHeight);", scrollable)

	def page_down(self):
		"""Send a page down keyboard event to the element.
		"""
		self._perform_action(
			lambda _: self.web_element.send_keys(Keys.PAGE_DOWN))

	def page_up(self):
		"""Send a page up keyboard event to the element.
		"""
		self._perform_action(
			lambda _: self.web_element.send_keys(Keys.PAGE_UP))

	def set_text_and_return(self, text, timeout=TIMEOUT):
		"""Replace text in an input field by selecting it all then replacing.

		Performs 3 attempts at setting the text, verifying that the field ends
		up with the correct result. On completion of text entry, send a RETURN
		key event.

		Args:
			text (str): the text to set
		"""
		self.set_text(text, timeout=timeout)
		self._perform_action(lambda _: self.web_element.send_keys(Keys.RETURN))

	def set_text(self, text, timeout=TIMEOUT):
		"""Replace text in an input field by selecting it all then replacing.

		Performs 3 attempts at setting the text, verifying that the field ends
		up with the correct result.

		Args:
			text (str): the text to set
		"""
		self.verify(timeout=timeout)
		Log.logger.info(u"{}Set text '{}' on [{}]".format(
			self._log_prefix(), text, self._name()))

		count = 0
		while count < 3 and \
			not (self.web_element.get_attribute("value") == text):

			if self._windows_env():
				self._perform_action(
					lambda _: self.web_element.send_keys(Keys.HOME))
				self._perform_action(
					lambda _: self.web_element.send_keys(Keys.CONTROL, 'a'))
			else:
				self._perform_action(
					lambda _: self.web_element.send_keys(Keys.HOME))
				self._perform_action(
					lambda _: self.web_element.send_keys(Keys.SHIFT, Keys.END))

			self._perform_action(lambda _: self.web_element.send_keys(text))
			count += 1

		if self.web_element.get_attribute("value") != text:
			raise Exception("Failed to set field text")

	def set_checkbox(self, is_checked, ignore_fail=False, timeout=TIMEOUT):
		"""If the checkbox is not at the desired value, toggle it.

		Args:
			is_checked (bool): desired checkbox state
		"""
		if self.is_selected(timeout=timeout) != is_checked:
			self.click()
		if not ignore_fail:
			if self.is_selected(timeout=timeout) != is_checked:
				raise ActionException(u"Checkbox set on {} failed"
					.format(self.description))

	def submit(self, timeout=TIMEOUT):
		"""Submit this element.
		"""
		self.verify(timeout=timeout)
		self._perform_action(lambda _: self.web_element.submit())

	@classmethod
	def register_click_fail_js(cls, fail_js):
		"""Register JS actions to try clearing modals or debug windows if a
		click fails.

		Args:
			fail_js (itr): iterable of JS invocation strings to directly clear
				any debug/modals
		"""
		cls.click_fail_js.extend(fail_js)

	def _run_click_fail_js(self):
		"""Run any registered click fail JS executions
		"""
		if len(self.click_fail_js) > 0:
			parent_frame = self._find_parent_frame()
			# always run from page level
			if parent_frame:
				self.switch_to_default()
			for js in self.click_fail_js:
				try:
					self.driver.execute_script(js)
				except:
					pass
			if parent_frame:
				# re-locate the element (becomes stale after switching)
				self._find_now()

	def _perform_action(self, action, alt_action=None):
		"""Generic action handler that makes 3 attempts to perform the action
		1 second apart before failing.

		Args:
			action (lambda): a lambda for the action
		"""
		for i in range(3):
			try:
				action(self)
				return
			except:
				if i == 0:
					# attempt to clear any known blocking elements
					self._run_click_fail_js()
					self.verify(timeout=0)
				if i == 2:
					# check obvious failures first, then throw the exception
					assert self.web_element, \
						'{} >> Element {} is not currently present'.format(
							self._log_prefix(), self.description)
					assert self.web_element.is_displayed(), \
						'{} >> Element {} is not currently displayed'.format(
							self._log_prefix(), self.description)
					assert self.web_element.is_enabled(), \
						'{} >> Element {} is not currently enabled'.format(
							self._log_prefix(), self.description)
					raise
				self.wait(1)
