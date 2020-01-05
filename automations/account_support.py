import functools
import os

from automations.clients.account import Account
from automations.config_support import Config
from automations.utils.log import Log


class AccountSupport(object):
	"""Account setup support.
	"""

	def configure_and_lock_account(self):
		"""If flagged for Pandora checkout and account and update the config.
		"""
		if not self.config:
			self.config = Config.instance()

		config = self.config
		self.release_account(quietly=True)

		if not config['use_pandora']:
			#self.account.pod = self.config['pod']
			#self.account.subdomain = self.config['subdomain']
			self.account.owner_email = self.config['owner_email']
			self.account.owner_first_name = self.config['owner_firstname']
			self.account.owner_last_name = self.config['owner_lastname']
			self.account.password = self.config['password']
			#self.account.widget_key = self.config['widget_key']
			#self.account.account_id = self.config['account_id']
			#self.account.plan = self.config['chat_plan']
			#self.account.phase = self.config['chat_phase']
			#self.account.oauth_token = self.config['owner_oauth_token']
			return
		self.checkout_pandora_account(self.account)

	def checkout_pandora_account(self, account=None, environment=None, chat_plan=None, chat_phase=None):
		"""Lock account from pandora.

		If query parameters are not specified, it will lock according to the config file parameters.

		Args:
			account(Account): account to be updated
			environment(string): pandora environment to query
			chat_plan(string): chat plan to query in pandora
			chat_phase(string): chat plan to query in pandora

		Returns:
			Account: Account object locked from Pandora
		"""

		pandora_query = {
				'environment': environment if environment else self.config['pandora_account_type'],
				'chat_plan': chat_plan if chat_plan else self.account.plan,
				'chat_phase': chat_phase if chat_phase else self.account.phase
			}

		if self.config['pod']:
			pandora_query['pod'] = self.config['pod']

		resource_id, account_data = self.pandora.lock_account(
			self.config['pandora_lock_timeout'], pandora_query
		)
		if not account:
			account = Account()

		owner_name = account_data.get('owner_name', '')

		account.pod = account_data.get('pod', '')
		account.subdomain = account_data.get('subdomain', None)
		account.owner_email = account_data.get('owner_email', '')
		account.owner_first_name = owner_name.split(' ')[0]
		account.owner_last_name = owner_name.split(' ')[1]
		account.password = account_data.get('password', '')
		account.widget_key = account_data.get('widget_key', '')
		account.account_id = account_data.get('account_id', '')
		account.pandora_id = resource_id
		account.plan = account_data.get('chat_plan', '')
		account.phase = int(account_data.get('chat_phase', '0'))
		account.oauth_token = account_data.get('chat_oauth_token', '')
		return account

	def _log_account_details(self, config, scribe):
		"""Log the account detaills for this run.

		Args:
			config (dict): the current config dict
		"""
		self.log_separator()
		self.log_info("Account details:")
		self.log_newline()
		self.log_info("Account Id: {}".format(self.account.account_id))
		self.log_info("Owner email: {}".format(self.account.owner_email))
		self.log_info("Password: {}".format(self.account.password))
		self.log_info("LC ID: {}".format(scribe.accounts.get_lc_server_id()))
		if self.account.subdomain:
			self.log_info("Subdomain: {}".format(self.account.subdomain))
		if self.account.pod:
			self.log_info("Pod: {}".format(self.account.pod))
		if config['use_pandora']:
			self.log_info("Pandora link: {}/"
				"resource_types/chat_test_accounts/resources/{}"
				.format(self.config['url_pandora'], self.account.pandora_id))
		if self.account.phase < 3:
			self.log_info("Admin: {}/admin/account/account/{}/"
				.format(config['logging_admin_url'], self.account.account_id))
		else:
			self.log_info("Monitor: "
				"{}/accounts/{}/overview"
				.format(config['logging_monitor_url'], self.account.account_id))
		self.log_newline()

	def is_staging(self):
		"""Check if on staging.

		Returns:
			bool: True if the current environment is staging
		"""
		return self.config['pandora_account_type'] == "staging"

	def release_account(self, account=None, quietly=False):
		"""Release the locked account (if specified), otherwise,
		release all the accounts.

		Args:
			account(Account): account object to be released in Pandora.
		"""
		resource_ids = []
		if account:
			resource_ids.append(account.pandora_id)
		else:
			if self.account.pandora_id:
				resource_ids.append(self.account.pandora_id)
			if self.secondary_accounts:
				for _ in self.secondary_accounts:
					if _.pandora_id:
						resource_ids.append(_.pandora_id)
		if resource_ids:
			for resource_id in resource_ids:
				try:
					self.pandora.release_account(resource_id)
					Log.logger.info("Release Pandora account: {}".format(resource_id))
				except:
					Log.logger.warn("Error releasing Pandora account")
		else:
			if not quietly:
				Log.logger.info("No Pandora accounts to release, skipping")
