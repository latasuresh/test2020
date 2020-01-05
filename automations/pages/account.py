from automations.core.element import Page
  
from .sections.dashboard_signin import SignIn


class Account(Page):
        """The chat account page"""

        def setup(self):
                self.signin = self.section_by_xpath(SignIn(self.driver), "//body", "Login section")

                # upper header links
                self.dashboard_link = self.element_by_selector("owner_dashboard", "Dashboard link").visible()
                self.signout_link = self.element_by_selector("a#logout_link", "Signout link").visible()
           

             
