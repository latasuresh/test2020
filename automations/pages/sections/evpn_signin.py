from automations.core.element import Section
  

class EvpnSignIn(Section):
        """Evpn sign in page.
        """

        def setup(self):
                print "i am in setup"
                self.email = self.element_by_selector("input[id=email]", "Email field").visible()
                self.password = self.element_by_selector("input[id=password]", "Password field").visible()
                self.signin_button = self.element_by_selector("input[name=commit]", "Signin button").visible()
                self.error_message = self.element_by_selector(".alert.alert-danger", "evpn invalid credentials message").visible()
                self.success_message = self.element_by_selector(".alert.alert-success","evpn email alert message").visible()
                self.fotgot_button = self.element_by_selector("a.link-email", "Forgot password link").visible()

        ###########################################################################################################################################

        def login(self, email, password):
                """Aurthenticate via provided email and password.

                Args:
                        email (str): the user email
                        password (str): the agent password
                """
                self.email.clear(timeout=120) # allow for a long load period
                self.email.set_text(email)
                self.password.set_text(password)
                self.signin_button.click()

        def forgot_password(self,email):
                """reset the password
                 Args:
                        email (str): the user email
                """
                self.fotgot_button.click()
                self.email.set_text(email)
                self.signin_button.click()


        def credentials_error_visible(self):
                """Check if the credentials error message is being presented.
                """
                self.error_message.text_contains('Invalid email or password.')

        def reset_accout_alert_visible(self):
                """Check if the valid alert message is being presented.
                """
                self.success_message.text_contains('password reset link or try another email')
