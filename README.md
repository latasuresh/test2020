# evpn automations and end-to-end tests
  
## Getting started ##

### Core flow


### Checkout repo and setup tools ###
```
# repo
git clone git@github.com:latasuresh/test2020.git
cd automation

# tool setup (if not already complete)
# make sure the python version is 2.7.X
brew install python2
pip install virtualenv
```

### Config control

config file

### Running tests ###

### ChromeDriver

You should have locally a version of chromedrivers that matches your local chrome version. To do that, open your chrome, and check the major version (Chrome > About Google Chrome)

Visit https://sites.google.com/a/chromium.org/chromedriver/home and download the chromedriver for you

Extract the chromedriver executable in your path. `~/bin/` if you have set that up, or `/usr/local/bin` if you're using brew and want it installed globaly.


### Running The Tests

If you want to save the virtual env setup every run then you can just do:

```
source scripts/start_virtualenv.sh
```

```
./scripts/run_tests.sh HO_ENV=staging USE_PANDORA=0 automations/browser_tests/test_evpn_login.py
```

Example of running a particular test in staging:


### Running The Tests

If you want to save the virtual env setup every run then you can just do:

```
source scripts/start_virtualenv.sh
```

```
./scripts/run_tests.sh HO_ENV=staging USE_PANDORA=0 automations/browser_tests/test_evpn_login.py
```


To view [Allure report](https://docs.qameta.io/allure/#_report_generation) locally.
```
brew install allure
allure serve ./allure-results
