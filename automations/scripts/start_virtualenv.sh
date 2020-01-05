#!/bin/bash
  
##############################################################################
# - start virtualenv if it is not running
# - if starting virtualenv then also upgrade the automation dependencies
#
# Run as 'source ./scripts/start_virtualenv.sh' when used from another script
##############################################################################

INVENV=$(python -c 'import sys; print ("1" if hasattr(sys, "real_prefix") else "0")')

if [ $INVENV -eq 0 ]
then
        echo "Starting virtualenv"
        if [[ ! -d .virtualenv ]]; then
                virtualenv .virtualenv
        fi
        . .virtualenv/bin/activate
        pip install -r automations/requirements.txt --upgrade
        ret=$?

        if [ $ret -ne 0 ]
        then
                # handle pip install failure
                echo "Failed to install packages from PIP"
                exit 1
        fi

        echo "Successfully installed packages from PIP"

else
        echo "virtualenv already running"
fi

export DBUS_SESSION_BUS_ADDRESS=/dev/null
