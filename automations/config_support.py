import imp
import inspect
import json
import os
import sys

import jinja2

import automations
from automations.utils.class_utils import Singleton
from automations.utils.log import Log


@Singleton
class Config(dict):
    """Dictionary like helper class for maintaining configuration data.
    """

    def __init__(self):
        """New initialised config instance.
        """
        env = os.environ.get("CHAT_ENV", os.environ.get("HO_ENV", "staging"))
        self.env = {"environment": env}

        module_path = os.path.dirname(automations.__file__)
        config_path = os.path.join(module_path, "config")

        config = None
        if os.path.isfile(config_path + ".json"):
            config = json.loads(open(config_path + ".json").read())
        elif os.path.isfile(config_path + ".py"):
            config = imp.load_source("config", config_path + ".py").config

        if not config:
            raise Exception("Config file not found in root of module")

        dict.__init__(self, config)

    def __getitem__(self, key):
        """Override to evaluate the values through the template.

        Args:
            key (string): dict key

        Returns:
            the value if found else None
        """

        def __render(item, context):
            """Renders the string given the context using the jinja template.
            """

            def _check_string_type(_item):
                """Python2/3 stuff.
                """

                if isinstance(_item, str):
                    return True
                elif sys.version_info < (3, 0, 0):
                    if isinstance(_item, eval("unicode")):
                        return True
                return False

            if _check_string_type(item):
                template = jinja2.Template(item)
                rendered = template.render(context)
                if rendered != item:
                    return __render(rendered, context)
                else:
                    return rendered
            else:
                return item

        env_ctx = dict.setdefault(self, self.env["environment"], {})
        default_ctx = dict.setdefault(self, "default", {})
        try:
            item = env_ctx[key]
        except KeyError:
            item = default_ctx[key]

        context = dict(self)
        context.update(os.environ)
        context.update(self.env)
        context.update(default_ctx)
        context.update(env_ctx)
        return __render(item, context)

    def __setitem__(self, key, value):
        """Override to put the value in the right environment bucket.

        Args:
            key (string): dict key
            value (object) dict value
        """
        sub_dict = dict.setdefault(self, self.env["environment"], {})
        sub_dict[key] = value


    ###########################################################################
    # Helpers
    ###########################################################################

    def is_staging(self):
        """Check if on staging.

        Returns:
            bool: True if the current environment is staging
        """
        return self['pandora_account_type'] == "staging"

    def is_dev(self):
        """Check if environment is dev environment

        Returns:
            bool: True if the current environment is dev
        """
        return self.env["environment"] in {"docker", "dev_kubernetes", }

    def use_zdi_extended_timing(self):
        """Try with extended timeouts

        It is particurlary used in ZDI dev environment.

        Returns:
            bool: True if the USE_ZDI_EXTENDED_TIMING environment variable is truthy
        """
        try_longer_enabled = bool(self["use_zdi_extended_timing"])
        if try_longer_enabled:
            Log.logger.warn("USE_ZDI_EXTENDED_TIMING is enabled.")
        return try_longer_enabled
