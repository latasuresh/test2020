from automations.core.element import Page
  
from .sections.dashboard_signin import SignIn


class Account(Page):
        """The chat account page"""

        def setup(self):
                self.signin = self.section_by_xpath(SignIn(self.driver), "//body", "Login section")

                # upper header links
                self.dashboard_link = self.element_by_selector("owner_dashboard", "Dashboard link").visible()
                self.signout_link = self.element_by_selector("a#logout_link", "Signout link").visible()
                self.zendesk_account_link = self.element_by_selector("li#acct_btn > a:nth-of-type(2)", "Account link").visible()
                self.language_button = self.element_by_selector("a#lang_chosen", "Language button").visible()
                self.help_link = self.element_by_selector("div#header_upper > li:nth-of-type(2) > a", "Help link").visible()

                # lower header links
                self.product_link = self.element_by_selector("div[id='header_lower'] li:nth-of-type(2) a", "Product link").visible()
                self.pricing_link = self.element_by_selector("div[id='header_lower'] li:nth-of-type(3) a", "Pricing link").visible()
                self.contact_link = self.element_by_selector("div[id='header_lower'] li:nth-of-type(4) a", "Contact link").visible()
                self.signup_link = self.element_by_selector("div[id='header_lower'] li:nth-of-type(5) a", "Signup link").visible()

                # tabs
                self.overview_tab = self.element_by_selector("ul.pagination_top > li#page_overview > a", "Overview tab").visible()
                self.integrations_tab = self.element_by_selector("ul.pagination_top > li#page_integrations > a", "Integrations tab").visible()

                # overview tab
                self.adjust_plan = self.element_by_selector("a[href*='/account/change_plan']", "Adjust/Purchase plan button").visible()
                self.info_list = self.list_by_selector("div#overview td.i", "Account info elements").visible()

                # owner
                self.change_owner_select = self.element_by_selector("form#change_owner select#new_owner", "Change owner select").visible()
                self.change_owner_button = self.element_by_selector("form#change_owner button", "CHange owner button").visible()

                # cancel
                self.cancel_account_btn = self.element_by_selector("button#cancel_account_show", "Cancel account button").enabled()

                # integrations
                self.support_integration = self.element_by_selector("div#integrations_menu a[href='#zendesk']", "Support integration").visible()
                self.other_integrations = self.list_by_selector("div#all_logos > a", "Other integrations elements").visible()
