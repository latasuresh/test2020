#!/bin/bash

##############################################################################
# Setup required environment variables (starts vritualenv if not running):
#
# - USE_SAUCE, USE_PANDORA, HO_ENV
#
# Defaults are:
#
# - USE_SAUCE=0
# - USE_PANDORA=1
# - HO_ENV=production
#
# e.g. ./scripts/setup_env.sh USE_SAUCE=0 USE_PANDORA=1 HO_ENV=production
#
# Run as 'source ./scripts/setup_env.sh "$@"' when used from another script
##############################################################################

source ./scripts/start_virtualenv.sh

##########################################################################
# Setup defaults if not defined
##########################################################################

if [ -z "$USE_SAUCE" ]; then
	echo "Pre-config default: USE_SAUCE=0"
	export USE_SAUCE=0
fi

if [ -z "$USE_PANDORA" ]; then
	echo "Pre-config default: USE_PANDORA=1"
	export USE_PANDORA=1
fi

if [ -z "$HO_ENV" ]; then
	echo "Pre-config default: HO_ENV=production"
	export HO_ENV="production"
fi

##########################################################################
# Extract params
##########################################################################

if [ $# -gt 0 ]; then
	for ARG in "$@"; do
		if [[ $ARG = *=* ]] && [[ $ARG != *--* ]]; then
			KEY=$(echo $ARG | cut -f1 -d=)
			VAL=$(echo $ARG | cut -f2 -d=)
			echo "Exporting: $KEY=$VAL"
			export "$KEY"="${VAL}"
		fi
	done
fi

##########################################################################
# Validation
##########################################################################

if [ $USE_SAUCE -ne 0 ] && [ $USE_SAUCE -ne 1 ]; then
	echo "----------------------------------------------------------"
	echo "Invalid USE_SAUCE param: [$USE_SAUCE]"
	echo "  - '1' to use Sauce"
	echo "  - '0' to run on local browser (default)"
	echo "----------------------------------------------------------"
	exit 1
elif [ $USE_SAUCE -eq 1 ]; then
	: ${SAUCE_USERNAME:?"Env parameter SAUCE_USERNAME is required"}
	: ${SAUCE_ACCESS_KEY:?"Env parameter SAUCE_ACCESS_KEY is required"}
fi

if [ $USE_PANDORA -ne 0 ] && [ $USE_PANDORA -ne 1 ]; then
	echo "----------------------------------------------------------"
	echo "Invalid USE_PANDORA param: [$USE_PANDORA]"
	echo "  - '1' to use a Pandora account (default)"
	echo "  - '0' to use local environment vars"
	echo "----------------------------------------------------------"
	exit 1
fi

if [ $HO_ENV != "production" ] && [ $HO_ENV != "beta" ] \
	&& [ $HO_ENV != "staging" ] && [ $HO_ENV != "staging998" ] \
	&& [ $HO_ENV != "staging999" ] && [ $HO_ENV != "devstage" ] \
	&& [ $HO_ENV != "docker" ] && [ $HO_ENV != "euc1" ] \
	&& [ $HO_ENV != "dev_kubernetes" ]; then
	echo "----------------------------------------------------------"
	echo "Invalid HO_ENV param: [$HO_ENV]"
	echo "Valid params + dashboard URL examples:"
	echo "  - 'production' dashboard.zopim.com (default)"
	echo "  - 'beta' beta.zopim.com"
	echo "  - 'staging' dashboard.zopim.org"
	echo "  - 'staging998' chat.chat998.zdch.at"
	echo "  - 'staging999' chat.chat999.zdch.at"
	echo "  - 'devstage' dashboard.chat.[DEV_TEAM].zdch.at"
	echo "  - 'docker' docker.zopim.com:8000/dashboard"
	echo "  - 'dr' dashboard-dr.zopim.com"
	echo "  - 'dev_kubernetes' <BASE_DOMAIN>"
	echo "----------------------------------------------------------"
	exit 1
fi
