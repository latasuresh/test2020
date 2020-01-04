from nose.plugins.attrib import attr
  
#from automations import spec
from automations.browsers import Browsers, browsers
from automations.driver_support import drivers
from automations.test_case import TestCase
from automations.utils.log import Log


@browsers(Browsers.primary)
class DashboardLoginTests(TestCase):
        """Tests dashboard sign in.
        """

        #def before_run(self):
        #       self.account_prep.reset.all().run()

        ###################################################################################################################

        @drivers('Agent')
        def test_login_invalid(self):
                """Logging in with invalid credentials fails and presents expected error message
                """

                self.evpn, self.dashboard = self.login_dashboard(
                        self.Agent, self.account.owner_email,
                        self.account.password + 'invalid',
                        expect_failure=True
                )

                if self.evpn != None:
                        self.evpn.signin.credentials_error_visible()

        ##################################################################################################################

        @drivers('Agent')
        def test_forgot_password(self):
                """
                   verify forgot password
                """

                self.evpn = self.forgot_password(self.Agent, self.account.owner_email)
                print "h4"
                if self.evpn != None:
                        self.evpn.signin.reset_accout_alert_visible()
