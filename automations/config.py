import os
  
config = {

        "default": {
                "ssl_verify": True,
                "evpn_domain": "com",
                "subdomain": "",
                "pod": "{{POD}}",

                "use_sauce": bool(int(os.environ.get('USE_SAUCE', 0))),
                "use_pandora": bool(int(os.environ.get('USE_PANDORA', 0))),
                "pandora_account_type": os.environ.get('PANDORA_ACCOUNT_TYPE', os.environ.get('HO_ENV')),
                "url_evpn_login": "{{url_evpn}}/sign-in",

                "email_domain": os.environ.get('EMAIL_DOMAIN', "gmail.com"),
                "owner_email": "{{ZOPIM_ADMIN_EMAIL_PREFIX}}@{{email_domain}}",
                "password": "{{ZOPIM_ADMIN_PASSWORD}}",
                "chat_plan": os.environ.get('CHAT_PLAN', 'trial'),
                "chat_phase": int(os.environ.get('CHAT_PHASE', 0)),
        },

        "staging": {
                "base_domain": ".com",
                "evpn_domain": "expressvpn.com",
                "url_evpn": "https://{{evpn_domain}}",
        }
}
