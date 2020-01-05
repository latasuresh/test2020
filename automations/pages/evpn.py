import re
  
from automations.core.element import Page
from .sections.evpn_signin import EvpnSignIn

class EvpnPage(Page):
        """Base evpn page.
        """

        def setup(self):
                self.signin = self.section_by_selector(EvpnSignIn(self.driver), "body", "evpn Signin")
