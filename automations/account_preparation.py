from automations.config_support import Config
from automations.utils.log import Log
from automations.utils.parallel import Concurrent


class Reset(object):
	"""Account reset helper.
	"""

	def __init__(self, automation):
		super(Reset, self).__init__()
		self.account = automation.account
		self.automation = automation
		self.tasks = Concurrent()
		# first disconnecting any remaining agents
		self.automation.scribe.disconnect_account()

	def routing(self):
		"""Add a routing reset task.
		"""
		self.tasks.add(self.automation.scribe.accounts.reset_chat_distribution)
		return self

	def landing(self):
		"""Add a landing reset task (owner only for the moment).
		"""
		scribe = self.automation.scribe
		self.tasks.add(scribe.agents.mark_landing_pages_seen, scribe.owner_id)
		return self

	def goals(self):
		"""Add a goals reset task.
		"""
		self.tasks.add(self.automation.scribe.goals.delete_all)
		return self

	def agents(self):
		"""Add an agents reset task that removes all non-standard agents.
		"""
		if self.account.plan != "lite":
			# ensure all spare agents are deleted and any missing
			# default agents are created, lite plans can only have the owner
			self.tasks.add(self.automation.tidy_account_agents, True)
		return self

	def triggers(self):
		"""Delete all triggers in the account.
		"""
		self.tasks.add(self.automation.scribe.triggers.delete_all)
		return self

	def skills(self):
		"""Delete all skills in the account.
		"""
		self.tasks.add(self.automation.scribe.skills.delete_all)
		return self

	def redaction(self):
		"""Turn off redaction.
		"""
		self.tasks.add(self.automation.scribe.accounts.switch_redaction)
		return self

	def widget_settings(self):
		"""Reset basics widget options
		"""
		self.tasks.add(self.automation.scribe.widgets.configure_widget_settings)
		return self

	def pre_chat_form(self):
		"""Turn off pre-chat-form.
		"""
		self.tasks.add(self.automation.scribe.widgets.configure_pre_chat_form)
		return self

	def bans(self):
		"""Delete all visitor and ip bans in the account."""
		self.tasks.add(self.automation.scribe.bans.delete_all)
		return self

	def roles(self):
		"""Delete all custom roles in the account."""
		self.tasks.add(self.automation.scribe.roles.delete_all)
		return self

	def departments(self):
		"""Delete all departments in the account."""
		self.tasks.add(self.automation.scribe.departments.delete_all)
		return self

	def shortcuts(self):
		"""Delete all shortcuts in the account."""
		self.tasks.add(self.automation.scribe.shortcuts.delete_all)
		return self

	def tags(self):
		"""Delete all predefined tags."""
		self.tasks.add(self.automation.scribe.tags.delete_all)
		return self

	def file_sending(self):
		"""Reset file sending to default"""
		self.tasks.add(self.automation.scribe.accounts.update_file_sending)
		return self

	def operating_hours(self):
		"""Reset operating hours to default"""
		self.tasks.add(self.automation.scribe.accounts.reset_operating_hours)
		return self

	def mobile_sdk_apps(self):
		"""Reset Mobile SDK Apps to default"""
		self.tasks.add(self.automation.scribe.mobile_sdk_apps.delete_all)
		return self

	def all(self):
		"""Add all reset tasks.
		"""
		return self.routing().landing().goals().agents().triggers() \
			.redaction().bans().roles().departments().shortcuts() \
			.widget_settings().pre_chat_form().skills().tags().file_sending() \
			.operating_hours().mobile_sdk_apps()

	def run(self):
		"""Run all queued tasks.
		"""
		self.tasks.run(threads=3)
		return self

##############################################################

class Prepare(object):
	"""Account preparation helper.
	"""

	def __init__(self, automation):
		super(Prepare, self).__init__()
		self.account = automation.account
		self.automation = automation
		self.tasks = Concurrent()

##############################################################

class AccountPrep(object):
	"""Account preparation helper.
	"""

	def __init__(self, automation):
		super(AccountPrep, self).__init__()
		self.account = automation.account
		self.automation = automation
		self.reset = Reset(automation)
		self.prepare = Prepare(automation)
