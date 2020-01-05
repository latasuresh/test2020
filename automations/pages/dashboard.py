import json

from automations.config_support import Config
from automations.core.base_element import TIMEOUT
from automations.core.element import Page, Section
from automations.utils.log import Log

from .account import Account
from .sections.dashboard_account_management import AccountManagement

class BaseDashboard(object):

        primary = False

        def setup(self):
                self.signin = self.section_by_selector(SignIn(self.driver), "body", "Login section")

        def teardown(self):
                """Tear down the dashboard resetting critical settings and logging out.
                """
                self.safe_try(self.nav.logout_now)


class DashboardPage(BaseDashboard, Page):
        """Base dashboard as page.
        """
        pass
