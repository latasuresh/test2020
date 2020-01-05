import random
import string

from automations.config_support import Config
from automations.random_support import RandomSupport

SUBDOMAIN_PREFIX = "z3n" 
EMAIL_PREFIX = "evpn-qa+"
DEFAULT_DOMAIN = "gmaiL.com"
AGENT_NAME_PREFIX = "agent"
AGENT_NAME_SUFFIX = "test"


class Account(RandomSupport):
	"""Account config dto and random generator.
	"""

	def __init__(self, email_domain=DEFAULT_DOMAIN, pod=None, suite_trial=None):
		"""New account instance with randomised data.

		Args:
			email_domain (str): email domain of the owner and agents, defaults
				to zendesk.com
			pod (str): pod for the account
			suite_trial (bool): whether to create the account as Suite Trial
		"""
		super(Account, self).__init__()
		self.config = Config.instance()
		self.regenerate(email_domain, pod=pod, suite_trial=suite_trial)

	def regenerate(self, email_domain=DEFAULT_DOMAIN, pod=None, suite_trial=None):
		"""Generate a new set of random details.

		Args:
			email_domain (str): domain to use for the owner
			pod (str): pod for the account
			suite_trial (bool): whether to create the account as Suite Trial
		"""
		tag = "c{}{}".format(
			self.config['chat_phase'], self.config.env["environment"][0].lower()
		)

		self.email_domain = email_domain
		self.pod = pod
		self.suite_trial = suite_trial
		self.subdomain = "{}{}{}".format(
			SUBDOMAIN_PREFIX, tag, self.generate_alphanumeric_lower(length=20))
		self.email_prefix = EMAIL_PREFIX + "{}{}{}".format(
			SUBDOMAIN_PREFIX, tag, self.generate_alphanumeric_lower(length=20))
		self.owner_first_name = self.generate_string(length=10)
		self.owner_last_name = self.generate_string(length=10)
		self.password = self.generate_alphanumeric(length=20)
		self.company = self.subdomain
		self.phone = self.generate_numeric(10)
		self.verification_link = None
		self.one_time_link = None
		self.widget_key = None
		self.account_id = None
		self.plan = "trial"
		self.phase = None
		self.pandora_env = None
		self.pandora_id = None
		self.migrated = None
		self.shard_id = "0"
		self.postal = "123456"
		self.oauth_token = ""
		return self

	@property
	def owner_email(self):
		"""Get the owner email forced to lower case for compatibility.

		Returns:
			str: the owner email
		"""
		return self.email_prefix.lower() + "@" + self.email_domain

	def support_login_url(self):
		"""Get the account URL for login.

		Returns:
			str: the URL
		"""
		return self._inject_subdomain(self.config['url_evpn_login'])

	def _inject_subdomain(self, into):
		"""Inject the current account subdomain into the provided URL

		Args:
			the URL with the subdomain placeholder

		Returns:
			str: the completed URL
		"""
		return into.format(self.subdomain)
