#!/usr/bin/python2.4
#
# (C) 2001 and onward Google, Inc.
#
# simple service that lets customers configure basic network parameters
# of an enterprise appliance, and also validate the network setting (trying
# to connect to all specified servers, checking test URLs, etc).
#
# unfortunately, this simple functionality still requires about 2K worth of
# python/HTML code :(
#
# Author: Max Ibel

# TODOS:
#  - maybe include version number on page templates
#  - remove secure_script_wrapper and instead do everything that needs root
#    through the Adminrunner ?
#    Pro: nice and modular
#    Con: doesn't work if adminrunner is not up.
#

import base64
import commands
import md5
import os
import random
import string
import sys
import time
import traceback

# file generated at build time
from google3.enterprise import languages

from google3.enterprise.legacy.adminrunner import adminrunner_client
from google3.enterprise.legacy.adminrunner import entconfig
from google3.enterprise.legacy.checks import network_diag
from google3.enterprise.legacy.production.babysitter import validatorlib
from google3.enterprise.legacy.scripts import webserver_config_template
from google3.enterprise.legacy.web import webserver_base

# eulas defines the list of countries to display, and the eula agreement
# associated with the country
# Note: the country "Other": NA is appended in stepdisplaycountry.
eulas = {
  "UNITED_STATES": "NA",
  "CANADA": "NA",
  "AUSTRIA": "UK",
  "BELGIUM": "UK",
  "BULGARIA": "UK",
  "CZECH_REPUBLIC": "UK",
  "DENMARK": "UK",
  "EGYPT": "UK",
  "FINLAND": "UK",
  "FRANCE": "UK",
  "GERMANY": "UK",
  "GREECE": "UK",
  "HUNGARY": "UK",
  "ICELAND": "UK",
  "IRELAND": "UK",
  "ISRAEL": "UK",
  "ITALY": "UK",
  "LUXEMBOURG": "UK",
  "MALTA": "UK",
  "MONACO": "UK",
  "NETHERLANDS": "UK",
  "NORWAY": "UK",
  "POLAND": "UK",
  "PORTUGAL": "UK",
  "RUSSIA": "UK",
  "SLOVAKIA": "UK",
  "SLOVENIA": "UK",
  "SOUTH_AFRICA": "UK",
  "SPAIN": "UK",
  "SWEDEN": "UK",
  "SWITZERLAND": "UK",
  "TURKEY": "UK",
  "UK": "UK",
  "UKRAINE": "UK",
  "ANGUILLA": "NA",
  "ARGENTINA": "NA",
  "ARUBA": "NA",
  "ANTIGUA_AND_BARBUDA": "NA",
  "BRAZIL": "NA",
  "BERMUDA": "NA",
  "BRITISH_VIRGIN_ISLANDS": "NA",
  "CAYMAN_ISLANDS": "NA",
  "CHILE": "NA",
  "COLOMBIA": "NA",
  "COSTA_RICA": "NA",
  "ECUADOR": "NA",
  "EL_SALVADOR": "NA",
  "FRENCH_GUIANA": "NA",
  "GUADELOUPE": "NA",
  "GUATEMALA": "NA",
  "HONDURAS": "NA",
  "MARTINIQUE": "NA",
  "MEXICO": "NA",
  "MONTSERRAT": "NA",
  "NETHERLANDS_ANTILLES": "NA",
  "NICARAGUA": "NA",
  "PANAMA": "NA",
  "PARAGUAY": "NA",
  "PERU": "NA",
  "PUERTO_RICO": "NA",
  "TURKS_AND_CAICOS_ISLANDS": "NA",
  "URUGUAY": "NA",
  "US_VIRGIN_ISLANDS": "NA",
  "VENEZUELA": "NA",
  "AUSTRALIA": "NA",
  "BANGLADESH": "NA",
  "CHINA": "NA",
  "INDIA": "NA",
  "INDONESIA": "NA",
  "HONG_KONG": "NA",
  "JAPAN": "NA",
  "MALAYSIA": "NA",
  "NEW_ZEALAND": "NA",
  "PHILIPPINES": "NA",
  "SINGAPORE": "NA",
  "SOUTH_KOREA": "NA",
  "SRI_LANKA": "NA",
  "THAILAND": "NA",
  "TAIWAN": "NA",
  "VIETNAM": "NA",
  "ALGERIA": "UK",
  "BAHRAIN": "UK",
  "EGYPT": "UK",
  "IRAQ": "UK",
  "JORDAN": "UK",
  "KUWAIT": "UK",
  "LEBANON": "UK",
  "LIBYA": "UK",
  "MOROCCO": "UK",
  "OMAN": "UK",
  "QATAR": "UK",
  "SAUDI_ARABIA": "UK",
  "SYRIA": "UK",
  "TUNISIA": "UK",
  "U.A.E.": "UK",
  "YEMEN": "UK",
}

#############################################################################
# H E L P   P A G E
#
#############################################################################
def cgi_help_page(**_):
  print webserver_config_template.HELP_PAGE  % {'ID' : applianceID}

#############################################################################
# R E S E T   T O   W I Z A R D   P A G E
#
# this will just reset the status of the wizard toggle and return to the main
# screen
#############################################################################
def cgi_resetwizard(**_):
  writeGlobalConfig({
    'IS_PAST_CONFIGURATION_WIZARD' : 0,
    })
  home_page()

#############################################################################
# R E S T A R T  M A C H I N E
#
# Restart cron, serving, web and crawling
# This may be useful for customers to 'unhang' a machine, for instance
# if the time has moved backward and crond does hang
#
# TODO: this does not work right. /bin/ps compains about the
# setgid flag, and refuses to restart root owned processes. Need to investigate
#
# However, this restarts serving, web and crond, so better than nothing
#
#############################################################################
def cgi_restartappliance(**args):
  # if response is given, we check
  # whether response is OK, and challenge is authentic
  if 'response' in args.keys():
    if CheckChallenge(args.get('challenge', ''), args['response']):
      print webserver_config_template.RESTARTING_PAGE % {
        'ID'             : applianceID,
        }
      log('RestartAppliance')
      os.system("cd %s/local/google/bin/ && " % ent_home
                + "./secure_script_wrapper -e /etc/rc.d/init.d/serve_%s restart </dev/null" % ent_version)
      os.system("cd %s/local/google/bin/ && " % ent_home
                + "./secure_script_wrapper -e /etc/rc.d/init.d/log_control_%s restart </dev/null" % ent_version)
      os.system("cd %s/local/google/bin/ && " % ent_home
                + "./secure_script_wrapper -e /etc/rc.d/init.d/web_%s restart </dev/null" % ent_version)
      os.system("cd %s/local/google/bin/ && " % ent_home
                + "./secure_script_wrapper -e /etc/rc.d/init.d/crond restart </dev/null")
      # note: this will restart myself!
      os.system("cd %s/local/google/bin/ && " % ent_home
                + "./secure_script_wrapper -e /etc/rc.d/init.d/crawl_%s restart </dev/null" % ent_version)
      return

  # OK, when we reach this point either the response was wrong or the challenge
  # was manipulated or we enter the page for the first time.
  # So, we pick a challenge and display it to the user.
  print webserver_config_template.RESTART_CHALLENGE_PAGE % {
    'ID'             : applianceID,
    'challenge'      : CreateChallenge(),
    }

#############################################################################
# H A L T   A P P L I A N C E
#
# we want to give people the ability to cleanly halt the appliance when going
# through adminrunner is not an option (such as manufacturing, when network is
# not configured.
#############################################################################
def cgi_haltappliance(**args):
  # if response is given, we check
  # whether response is OK, and challenge is authentic
  if 'response' in args.keys():
    if CheckChallenge(args.get('challenge', ''), args['response']):
      DoHaltAppliance()
      return

  # OK, when we reach this point either the response was wrong or the challenge
  # was manipulated or we enter the page for the first time.
  # So, we pick a challenge and display it to the user.
  print webserver_config_template.HALT_CHALLENGE_PAGE % {
    'ID'             : applianceID,
    'challenge'      : CreateChallenge(),
    }

def DoHaltAppliance():

  print webserver_config_template.HALT_DONE_PAGE % {
    'ID'             : applianceID,
    }
  log('DoHaltAppliance')
  ar_client.HaltCluster()
  time.sleep(120) # Give the shutdown time to take effect
  log('DoHaltAppliance failed')
  print 'Halt failed'

#############################################################################
# E N A B L E   /   D I S A B L E    S S H D   P O R T
#
# in cases where customers will not allow us to ppp into the box via modem,
# we will need to enable SSH access to the box.
#
#############################################################################
def cgi_enablesshd(**args):
  # if response is given, we check
  # whether response is OK, and challenge is authentic
  if 'response' in args.keys():
    if CheckChallenge(args.get('challenge', ''), args['response']):
      DoConfigSSHD(1)
      return

  # OK, when we reach this point either the response was wrong or the challenge
  # was manipulated or we enter the page for the first time.
  # So, we pick a challenge and display it to the user.
  print webserver_config_template.ENABLESSHD_CHALLENGE_PAGE % {
    'ID'             : applianceID,
    'challenge'      : CreateChallenge(),
    }

def cgi_disablesshd(**args):
  if 'response' in args.keys():
    if CheckChallenge(args.get('challenge', ''), args['response']):
      DoConfigSSHD(0)
      return

  # OK, when we reach this point either the response was wrong or the challenge
  # was manipulated or we enter the page for the first time.
  # So, we pick a challenge and display it to the user.
  print webserver_config_template.DISABLESSHD_CHALLENGE_PAGE % {
    'ID'             : applianceID,
    'challenge'      : CreateChallenge(),
    }

def DoConfigSSHD(enable):
  log('DoConfigSSHD: %s' % enable)
  if (enable):
    print webserver_config_template.ENABLESSHD_DONE_PAGE % {
      'ID'             : applianceID,
      }
  else:
    print webserver_config_template.DISABLESSHD_DONE_PAGE % {
      'ID'             : applianceID,
      }

  writeGlobalConfig({
    'ENT_ENABLE_EXTERNAL_SSH' : enable,
    })
  ar_client.ReconfigureNet()


#############################################################################
# S E L F D E S T R U C T
#
# In case a customer want to return the machine, we want to be able to
# delete all data from the machine. In order to prevent
# unauthorized/unintended access, we present a challenge to the user,
# which has to be answered. It's a simple transformation, that our
# support crew can easily do.
#
#############################################################################

def cgi_selfdestruct(**args):
  # if response is given, we check
  # whether response is OK, and challenge is authentic
  if 'response' in args.keys():
    if CheckChallenge(args.get('challenge', ''), args['response']):
      DoSelfDestruct() # never returns

  # OK, when we reach this point either the response was wrong or the challenge
  # was manipulated or we enter the page for the first time.
  # So, we pick a challenge and display it to the user.
  print webserver_config_template.SELFDESTRUCT_CHALLENGE_PAGE % {
    'ID'             : applianceID,
    'challenge'      : CreateChallenge(),
    }

def CreateChallenge():
  # apparently, every thread starts with the same initial seed :((
  random.seed(0,0,0)
  challenge = string.join(map(lambda _: random.choice(
    'abcefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ-123456789_'),
                              range(6)), '')
  challenge = challenge + base64.encodestring(md5.new(
    challenge + "GOOGLE").digest())
  return challenge

def CheckChallenge(challenge, response):
  if len(challenge) == 30:
    digest = challenge[6:]
    challenge = challenge[:6]
    if digest == string.rstrip(base64.encodestring(md5.new(
      challenge + "GOOGLE").digest())):
      # challenge is authentic
      if response == string.swapcase(challenge): # response is valid
        return 1
  return 0

def DoSelfDestruct():

  print webserver_config_template.SELFDESTRUCT_DONE_PAGE % {
    'ID'             : applianceID,
    }
  # Do magic here

  machine_list = ','.join(params['ENT_ALL_MACHINES'])

  cmd = ("cd %s/local/google/bin/ && "
         "./secure_script_wrapper -p2 "
         "%s/local/google3/enterprise/legacy/install/clean_machines.py "
         "--force --machines=\"%s\" </dev/null" %
         (ent_home, ent_home, machine_list))
  log(repr(cmd))
  os.system(cmd)
  if os.access('/export/hda3/logs', os.F_OK):
    print '*** Operation failed'
    log('selfdestruct failed: /export/hda3/logs still exists')
  else:
    print '*** Operation terminated unexpectedly'
    log('selfdestruct failed: clean_machines.py returned')



# TODO: add a non-wizard-version of the homepage that is displayed after
# the initial install.

# TODO: add a small HOWTO for adding fields to the setup

# TODO: add a page that kicks the machine (restart vmmanager, adminrunner, servnig, etc)

#############################################################################
#
# W I Z A R D
#
#############################################################################


# print a summary and ask for confirmation. This will set the state to
# IS_PAST_CONFIGURATION_WIZARD, and then start over (this time in the overview page)
def step6(**args):
  args['step'] = 6
  err_table = ErrorTable(args['errors'])

  if err_table == '':
    args['errors'] = CheckURLParms(args['testurls'])
    args['errors'].extend(CheckDnsParms(args['dns_servers'],
                                        args['dns_search_path']))
    if args['errors'] != []:
      apply(step5, (), args)
      return

  diags = ShowURLDiags(args['testurls'], args['dns_servers'])

  form_params = {
    'ID'             : applianceID,
    'Errors'         : err_table,
    'Diags'          : diags,
    }

  form_params.update(args)
  form_params.update({'timezone_screen':
                      ConvertOSTimeZoneToUserSpeak(args['timezone'])})
  form_params.update(webserver_config_template.WHATIS_HELP)
  form_params.update(webserver_config_template.MISC_HELPER_HELP)


  # Note: pressing Continue will activate these changes and disable the wizard.
  # the user is now getting back to step 1, this time w/ overview page
  if (applianceType == "CLUSTER"):
    print webserver_config_template.CONGRATULATIONS_PAGE_8WAY % form_params
  else:
    print webserver_config_template.CONGRATULATIONS_PAGE % form_params


# now optionally test some test URLs
def step5(**args):
  args['step'] = 5
  err_table = ErrorTable(args['errors'])

  if err_table == '':
    args['errors'] = CheckMiscParms(args['admin_email'],
                                    args['admin_pass'],
                                    args['admin_pass2'],
                                    emptyPasswordIsOK = args.has_key('back'))
    if args['errors'] != []:
      apply(step4, (), args)
      return

  # set admin email / ...
  writeGlobalConfig({
    'PROBLEM_EMAIL'      : args['admin_email'],
    'NOTIFICATION_EMAIL' : args['admin_email'],
    })
  if args['admin_pass'] != '':
    ar_client.SetUserPasswd('admin', args['admin_pass'])
  if args['admin_email'] != '':
    ar_client.SetUserEmail('admin', args['admin_email'])

  # diagnose  the same
  diags = ShowMiscDiagnostics()

  form_params = {
    'ID'             : applianceID,
    'Errors'         : err_table,
    'Diags'          : diags,
    }
  form_params.update(args)
  form_params.update(webserver_config_template.WHATIS_HELP)
  form_params.update(webserver_config_template.MISC_HELPER_HELP)

  # misc settings
  print webserver_config_template.TESTURL_SETTINGS_PAGE % form_params

# step 4 of the wizard: show successful step 1,2,3 data and ask for
# syslog server information, as well as admin passwords/email
def step4(**args):
  args['step'] = 4
  err_table = ErrorTable(args['errors'])

  # 1. check parameters. If invalid redirect back to step2
  if err_table == '':
    args['errors'] = CheckTimeParms(args['ntp_servers'],
                                    args['timezone'])
    if args['errors'] != []:
      apply(step3, (), args)
      return

  # Set timezone/ ntp servers
  writeGlobalConfig({
    'NTP_SERVERS' : string.split(args['ntp_servers'], ','),
    'TIMEZONE' : args['timezone'],
    })
  ar_client.ReconfigureNet()

  ar_client.RestartServer('supergsa_main')

  diags = ShowNTPDiagnostics(args['ntp_servers'])

  # fill out form if possible
  if err_table == '':   # fill out form if possible
    args['admin_email'] = normalize(params['NOTIFICATION_EMAIL'])

  form_params = {
    'ID'             : applianceID,
    'Errors'         : err_table,
    'Diags'          : diags,
    }
  form_params.update(args)
  form_params.update(webserver_config_template.WHATIS_HELP)
  form_params.update(webserver_config_template.MISC_HELPER_HELP)

  # misc settings
  print webserver_config_template.MISC_SETTINGS_PAGE % form_params

# step 3 of the wizard: show successful step 1,2 data and ask for
# time information
def step3(**args):
  args['step'] = 3
  err_table = ErrorTable(args['errors'])

  # 1. check parameters. If invalid redirect back to step2
  if err_table == '':
    args['errors'] = CheckDnsParms(args['dns_servers'],
                                   args['dns_search_path'])
    args['errors'] = args['errors']  + CheckMailParms(args['smtp_servers'],
                                             args['outgoing_email_sender'])
    if args['errors'] != []:
      apply(step2, (), args)
      return

  # set DNS and Mail values
  writeGlobalConfig({
    'BOT_DNS_SERVERS'       : args['dns_servers'],
    'DNS_SEARCH_PATH'       : args['dns_search_path'],
    'SMTP_SERVER'           : args['smtp_servers'],
    'OUTGOING_EMAIL_SENDER' : args['outgoing_email_sender'],
    })
  ar_client.ReconfigureNet()

  # 2 diagnose dns
  diags = ShowDNSMailDiagnostics(args['dns_servers'],
                                 args['smtp_servers'],
                                 args['serve_ip'])


  if err_table == '':   # fill out form if possible
    args['timezone'] = normalize(params['TIMEZONE'])
    args['ntp_servers'] = ""
    if params['NTP_SERVERS'] != None:
      args['ntp_servers'] = normalize(string.join(params['NTP_SERVERS'], ','))

  args['timezone'] = GetTimeZone(args['timezone'])

  form_params = {
    'ID'             : applianceID,
    'Errors'         : err_table,
    'Diags'          : diags,
    }
  form_params.update(args)
  form_params.update(webserver_config_template.WHATIS_HELP)
  form_params.update(webserver_config_template.MISC_HELPER_HELP)

  print webserver_config_template.TIME_SETTINGS_PAGE % form_params

# step 2 of the wizard: show successful step 1 data and ask for
# DNS settings, as well as the mail server
def step2(**args):
  args['step'] = 2
  err_table = ErrorTable(args['errors'])

  # 1. check parameters. If not step1 is not legal, redirect back to homepage
  if err_table == '':
    args['errors'] = CheckIPParms(args['serve_ip'],
                                  args['switch_ip'],
                                  args['crawl_ip'],
                                  args['netmask'],
                                  args['gateway'],
                                  args['autonegotiation'],
                                  args['network_speed'])
    if args['errors'] != []:
      apply(step1, (), args)
      return

  autonegotiation = 1
  if args['autonegotiation'] == '':
    autonegotiation = 0

  network_speed = 0;
  if args['network_speed'] != '':
    network_speed = int(args['network_speed']);

  # set IP values
  writeGlobalConfig({
    'EXTERNAL_WEB_IP' : args['serve_ip'],
    'EXTERNAL_SWITCH_IP' : args['switch_ip'],
    'EXTERNAL_CRAWL_IP' : args['crawl_ip'],
    'EXTERNAL_NETMASK' : args['netmask'],
    'EXTERNAL_DEFAULT_ROUTE' : args['gateway'],
    'SERVERIRON_AUTONEGOTIATION' : autonegotiation,
    'ONEBOX_NETCARD_SETTINGS' : network_speed,
    })
  ar_client.ReconfigureNet()

  # restart admin console
  # why: because it needs to pick up the new IP address so it can prevent
  # accesses to internal URLs.
  # on clusters internal IPs never change but, EXTERNAL_WEB_IP is one of the
  # commandline argument to AdminConsole, so it should be restarted even on 
  # clusters too.
  os.system( ("cd %s/local/google/bin/ && ./secure_script_wrapper -e "
              "/etc/rc.d/init.d/web_%s restart >&/dev/null </dev/null" 
              % (ent_home, ent_version)))

  # restart version manager
  # why: because the webserver base for some reason does not like it if
  # the IP adress changes under its nose. It basically does not see incoming
  # connections anymore. TODO: investigate why and fix this for good. This is
  # only a temporary hack
  if (applianceType != "CLUSTER"):
    # on clusters internal IPs never change
    os.system("cd %s/local/google/bin/ && " % ent_home
              + "./secure_script_wrapper -e /etc/rc.d/init.d/vmanager restart >&/dev/null </dev/null&")

  # restart file system gateway. It needs EXTERNAL_WEB_IP to crawl
  ar_client.RestartServer('fsgw')
  # restart enterprise_onebox server with new EXTERNAL_WEB_IP
  ar_client.RestartServer('oneboxenterprise')

  # show diagnostics
  # (if DNS is illegal display explanation)
  diags = ShowIPDiagnostics(args['gateway'])

  dhcp_data = GetDHCPInfo()
  do_dhcp = ""
  do_dhcp_message = ""

  # fill out form when possible:
  # if this is the first time values are set,
  # try to use DHCP discovered values:
  args['outgoing_email_sender'] = normalize(params['OUTGOING_EMAIL_SENDER'])
  if (args['dns_servers'] == '' and args['dns_search_path'] == '' and
      args['smtp_servers'] == ''):
    do_dhcp = "*"
    do_dhcp_message = (
      webserver_base.GetMsg('WE_HAVE_ACQUIRED_YOUR_NETWORK_SETTINGS'))
    args['dns_servers'] = dhcp_data.get('DNS_SERVERS', '')
    args['dns_search_path'] = dhcp_data.get('DOMAIN_NAME', '')
    args['smtp_servers'] = string.split(
      dhcp_data.get('SMTP_SERVERS', ''), ',')[0]
    if (applianceType != "CLUSTER"):
      args['switch_ip'] = ''
      args['crawl_ip'] = ''
  elif err_table == '':
    # otherwise, we use the args when valid
    args['dns_servers'] =  normalize(params['BOT_DNS_SERVERS'])
    args['dns_search_path'] =  normalize(params['DNS_SEARCH_PATH'])
    args['smtp_servers'] =  normalize(params['SMTP_SERVER'])
  form_params = {
    'ID'             : applianceID,
    'Errors'         : err_table,
    'Diags'          : diags,
    'do_dhcp'        : do_dhcp,
    'do_dhcp_message': do_dhcp_message,
  }

  form_params.update(args)
  form_params.update(webserver_config_template.WHATIS_HELP)
  form_params.update(webserver_config_template.MISC_HELPER_HELP)


  # DNS settings
  print webserver_config_template.DNS_SETTINGS_PAGE %  form_params

# Display country choice
def stepdisplaycountry(**args):
  err_table = ErrorTable(args['errors'])

  # Generate country selector for this language
  countries = []
  for country in eulas.keys():
    localized_country = webserver_base.GetMsg(country)
    eula = eulas[country]
    countries.append([localized_country, country, eula])
  countries.sort()
  # Add Other at end, with contract of NA
  countries.append([webserver_base.GetMsg('OTHER'), "Other", "NA"])
  selector = ['<select name="eula">']
  for localized_country, country, eula in countries:
    selector.append('<option value="%s">%s</option>' % (eula,
      localized_country))
  selector.append('</select>')
  form_params = {
    'ID'             : applianceID,
    'Errors'         : err_table,
    'Diags'          : '',
    'Selector'       : ''.join(selector),
  }

  form_params.update(args)
  form_params.update(webserver_config_template.WHATIS_HELP)
  form_params.update(webserver_config_template.MISC_HELPER_HELP)
  print webserver_config_template.COUNTRY_SETTINGS_PAGE % form_params

def GetLicenseLink(eula, lang):
  """ Get link to the license if exists.

  Returns URL.
  Returns None if unable to load."""

  file = 'licenses/license_%s_%s.htm' % (eula, lang)
  if os.access(file, os.R_OK):
    return '/' + file
  else:
    return None

# Display license
def stepdisplaylicense(**args):
  err_table = ErrorTable(args['errors'])
  # Get the appropriate license, defined by the eula variable and the language.
  lang = webserver_base.GetLanguage()
  license_link = GetLicenseLink(args['eula'], lang)
  if not license_link:
    license_link = GetLicenseLink(args['eula'], lang[:2]) # Drop region
  if not license_link:
    license_link = GetLicenseLink(args['eula'], 'en') # Default to English
  if not license_link:
    # Entirely failed to read license.
    #  This should never happen, so direct to Google support.
    license_link = "/licenses/license_err.htm"
    log('Failed to read license for ' + repr(args['eula']) + ' ' + lang)

  form_params = {
    'ID'             : applianceID,
    'Errors'         : err_table,
    'Diags'          : '',
    'License'        : license_link,
  }

  form_params.update(args)
  form_params.update(webserver_config_template.WHATIS_HELP)
  form_params.update(webserver_config_template.MISC_HELPER_HELP)
  print webserver_config_template.LICENSE_SETTINGS_PAGE % form_params


# Radio buttons need a 'checked' attribute on the selected option.
# This function translates from button value to a 'checked' in the
# right position in a map. Converts integer values to strings, but
# it won't work with multiple digits ints.
def ButtonCheckedMap(checkedValue, values, root=''):
  checkedMap = {}
  for value in values:
    if str(checkedValue) == str(value):
      checkedMap[root + str(value)] = 'checked'
    else:
      checkedMap[root + str(value)] = ''
  return checkedMap

# First step: IP addresses and such
def step1(**args):
  args['step'] = 1
  err_table = ErrorTable(args['errors'])

  do_dhcp_message = ""

  # fill out form when possible:
  # if this is the first time values are set,
  # try to use DHCP discovered values:
  if (args['serve_ip'] == '' and args['netmask'] == '' and
      args['crawl_ip'] == '' and args['gateway'] == ''):
    do_dhcp_message = (
      webserver_base.GetMsg('WE_HAVE_ACQUIRED_YOUR_NETWORK_SETTINGS'))
    dhcp_data = GetDHCPInfo()
    args['netmask'] = dhcp_data.get('NETMASK', '')
    args['gateway'] = string.split(dhcp_data.get('ROUTERS', ''), ',')[0]
    args['serve_ip'] = ''
    args['crawl_ip'] = ''
    args['switch_ip'] = ''
  elif err_table == '':
    # otherwise, we use the args when valid
    args['netmask'] = normalize(params['EXTERNAL_NETMASK'])
    args['gateway'] = normalize(params['EXTERNAL_DEFAULT_ROUTE'])
    args['serve_ip'] = normalize(params['EXTERNAL_WEB_IP'])
    args['switch_ip'] = normalize(params['EXTERNAL_SWITCH_IP'])
    args['crawl_ip'] = normalize(params['EXTERNAL_CRAWL_IP'])
  args['network_speed'] = normalize(params['ONEBOX_NETCARD_SETTINGS'])

  form_params = {
      'ID'             :  applianceID,
      'Errors'         :  err_table,
      'do_dhcp_message': do_dhcp_message,
      }
  form_params.update(args)
  form_params.update(ButtonCheckedMap(args['network_speed'], range(6),
                                      'network_speed_'))
  form_params.update(webserver_config_template.WHATIS_HELP)
  form_params.update(webserver_config_template.MISC_HELPER_HELP)

  if (applianceType == "CLUSTER"):
    print webserver_config_template.IP_SETTINGS_PAGE_8WAY % form_params
  else:
    print webserver_config_template.IP_SETTINGS_PAGE % form_params

def step0(**args):
  args['step'] = 0
  err_table = ''
  # did we press "commit" button (and no errors present)
  if args.has_key('commit'):
    # validate all parameters - if we entered some
    errors = CheckIPParms(args['serve_ip'],
                          args['switch_ip'],
                          args['crawl_ip'],
                          args['netmask'],
                          args['gateway'],
                          args['autonegotiation'],
                          args['network_speed'])
    errors = errors + CheckDnsParms(args['dns_servers'],
                                    args['dns_search_path'])
    errors = errors + CheckURLParms(args['testurls'])
    errors = errors + CheckMiscParms(args['admin_email'],
                                     args['admin_pass'],
                                     args['admin_pass2'],
                                     emptyPasswordIsOK = 1)
    errors = errors + CheckTimeParms(args['ntp_servers'],
                                     args['timezone'])
    errors = errors + CheckMailParms(args['smtp_servers'],
                                     args['outgoing_email_sender'])

    err_table = ErrorTable(errors)

    # then save the values if necessary

    if err_table == '':
      items = {
        'EXTERNAL_WEB_IP'            : args['serve_ip'],
        'EXTERNAL_NETMASK'           : args['netmask'],
        'EXTERNAL_DEFAULT_ROUTE'     : args['gateway'],
        'BOT_DNS_SERVERS'            : args['dns_servers'],
        'DNS_SEARCH_PATH'            : args['dns_search_path'],
        'SMTP_SERVER'                : args['smtp_servers'],
        'OUTGOING_EMAIL_SENDER'      : args['outgoing_email_sender'],
        'PROBLEM_EMAIL'              : args['admin_email'],
        'NOTIFICATION_EMAIL'         : args['admin_email'],
        'NTP_SERVERS'                : string.split(args['ntp_servers'], ','),
        'TIMEZONE'                   : args['timezone'],
        }
      if applianceType == "ONEBOX" or applianceType == "MINI" or applianceType == "SUPER":
        items.update({
          'ONEBOX_NETCARD_SETTINGS'    : args['network_speed'],
          })
      if (applianceType == "CLUSTER"):
        items.update({
          'EXTERNAL_SWITCH_IP'         : args['switch_ip'],
          'EXTERNAL_CRAWL_IP'          : args['crawl_ip'],
          'SERVERIRON_AUTONEGOTIATION' : args['autonegotiation'],
          })

      writeGlobalConfig(items)
      if args['admin_pass'] != '':
        ar_client.SetUserPasswd('admin', args['admin_pass'])
      ar_client.SetUserEmail('admin', args['admin_email'])
      log(repr(ar_client.ReconfigureNet()))

      # restart version manager (see comment in step2)
      if (applianceType != "CLUSTER"):
        # on clusters internal IPs never change
        os.system("cd %s/local/google/bin/ && " % ent_home
                  + "./secure_script_wrapper -e /etc/rc.d/init.d/vmanager restart >&/dev/null </dev/null")
  else:
    # get parameters
    args['netmask'] =  normalize(params['EXTERNAL_NETMASK'])
    args['gateway'] =  normalize(params['EXTERNAL_DEFAULT_ROUTE'])
    args['serve_ip'] =  normalize(params['EXTERNAL_WEB_IP'])
    args['switch_ip'] =  normalize(params['EXTERNAL_SWITCH_IP'])
    args['crawl_ip'] =  normalize(params['EXTERNAL_CRAWL_IP'])
    args['dns_servers'] =  normalize(params['BOT_DNS_SERVERS'])
    args['dns_search_path'] =  normalize(params['DNS_SEARCH_PATH'])
    args['smtp_servers'] =  normalize(params['SMTP_SERVER'])
    args['outgoing_email_sender'] = normalize(params['OUTGOING_EMAIL_SENDER'])
    args['admin_email'] = normalize(params['NOTIFICATION_EMAIL'])
    args['timezone'] = normalize(params['TIMEZONE'])
    args['ntp_servers'] = ""
    if params['NTP_SERVERS'] != None:
      args['ntp_servers'] = normalize(string.join(params['NTP_SERVERS'], ','))


  args['timezone'] = GetTimeZone(args['timezone'])
  args['network_speed'] = normalize(params['ONEBOX_NETCARD_SETTINGS'])


  # DIAGNOSE SETTINGS:
  diags = ShowAllDiagnostics(args['serve_ip'], args['gateway'],
                             args['dns_servers'], args['smtp_servers'],
                             args['ntp_servers'], args['testurls'])

  form_params = {
      'ID'             :  applianceID,
      'Errors'         :  err_table,
      'Diags'          : diags,
      'do_dhcp'        : '',
      'do_dhcp_message': '',
      }
  form_params.update(args)
  form_params.update(ButtonCheckedMap(args['network_speed'], range(6),
                                      'network_speed_'))
  form_params.update(webserver_config_template.NO_WHATIS_HELP)
  form_params.update(webserver_config_template.MISC_HELPER_NOHELP)

  if (applianceType == "CLUSTER"):
    print webserver_config_template.ALL_SETTINGS_PAGE_8WAY % form_params
  else:
    print webserver_config_template.ALL_SETTINGS_PAGE % form_params

# redirect to main config page
# (home page can't accept cgi args
def home_page(**_):
  localize_messages()
  body = (webserver_base.GetMsg('REDIRECT').
           replace('PLACEHOLDER_LINK', '<a href="/main_config">').
           replace('PLACEHOLDER_ENDLINK', '</a>'))
  print webserver_config_template.REDIRECT_PAGE % body

# body of main wizard page
def cgi_main_config(**args):
  localize_messages()
  global params
  args = apply(AllArgsQualifier, (), args)

  # re-read params (might have changed)
  params = readGlobalConfig()
  if params == None:
    print webserver_base.GetMsg('ERROR_LOADING_CONFIG_FILE')
    return

  # calculate the step number we're in. It's the old step number +- 1,
  # depending whether we came here using back or next button.
  # Note that if the step number is out of bounds, we jump back to the
  # home page, this should only happen if the user is fuzzing around with
  # the arguments
  try:
    this_step = int(args['step'])
    if args.has_key('back'):
      this_step = int(this_step) - 1
    elif args.has_key('next'):
      this_step = int(this_step) + 1
    elif args.has_key('commit'):
      this_step = 1
  except:
    this_step = 0

  # if we have OK'ed the Wizard, mark this in the parameters
  if this_step == 7 and args.has_key('next'):
    writeGlobalConfig({
      'IS_PAST_CONFIGURATION_WIZARD'      : 1,
      })
    params['IS_PAST_CONFIGURATION_WIZARD'] = 1

  # figure out the first screen for the customer
  if params['IS_PAST_CONFIGURATION_WIZARD'] == 1:
    start_step = 0
  else:
    start_step = 1

  # Check license
  if params.get('LICENSE_ACCEPTED', 0) == 0:
    if args.has_key('accept'):
      # License has just been accepted
      writeGlobalConfig({
        'LICENSE_ACCEPTED'      : int(time.time()),
        })
      need_license = 0
      this_step = 0
    else:
      need_license = 1
  else:
    need_license = 0

  if this_step < start_step or this_step > 6:
    this_step = start_step
  args['step'] = str(this_step)

  if need_license:
    if not args.get('eula', ''):
      apply(stepdisplaycountry, (), args)
    else:
      apply(stepdisplaylicense, (), args)
  elif args['step'] == '0':
    apply(step0, (), args)
  elif args['step'] == '1':
    apply(step1, (), args)
  elif args['step'] == '2':
    apply(step2, (), args)
  elif args['step'] == '3':
    apply(step3, (), args)
  elif args['step'] == '4':
    apply(step4, (), args)
  elif args['step'] == '5':
    apply(step5, (), args)
  elif args['step'] == '6':
    apply(step6, (), args)
  else: # must be step 1, or user attempt to fuzz around
    if params['IS_PAST_CONFIGURATION_WIZARD'] == 1:
      apply(step0, (), args)
    else:
      if start_step == 1:
        apply(step1, (), args)
      else:
        apply(step0, (), args)


#############################################################################
#
# C H E C K I N G   /   V A L I D A T I O N
#
#############################################################################

# The following functions do different levels of argument/value checking:
#
# * qualifiers "clean up" arguments (i.e. remove white space from a comma
#   separated list)
# * CheckFooParms check parameters for validity occording to crawler.common
#   crawler.enterprise and so on.
# * ShowFooDiags try to see if parameters "work", for instance if gateways
#   are pingable and such
#

def GetTimeZone(timezone):
  timezone_string = webserver_config_template.TIMEZONE_START
  for t in webserver_config_template.TIMEZONES:
    if t[0] == timezone:
      timezone_string = (timezone_string +
                         webserver_config_template.TIMEZONE_ITEM % (
        "selected", t[0], t[1]))
    else:
      timezone_string = (timezone_string +
                            webserver_config_template.TIMEZONE_ITEM % (
      "", t[0], t[1]))
  timezone_string = timezone_string + webserver_config_template.TIMEZONE_END
  return timezone_string

# convert the timezone used by OS (e.g. America/Los_Angeles) to the
# representation to be shown to user
def ConvertOSTimeZoneToUserSpeak(timezone):
  for t in webserver_config_template.TIMEZONES:
    if t[0] == timezone:
      return t[1]
  return None

def normalize(value, do_strip=1):
  if value == None: value = ''
  if value != None and do_strip:
    value = string.strip(str(value))
  return value


# Qualify a commalist, i.e. remove all white space
def CommaListQualifier(list_str):
  return string.join(map(string.strip, string.split(
    list_str, ",")), ",")

# Qualify (clean up) all args, to avoid duplication of errorchecking later on
def AllArgsQualifier(**args):
  nu_args = {}
  for i in args.keys():
    args[i] = normalize(args[i])

  nu_args['serve_ip'] = args.get('serve_ip', '')
  nu_args['switch_ip'] = args.get('switch_ip', '')
  nu_args['crawl_ip'] = args.get('crawl_ip', '')
  nu_args['netmask'] = args.get('netmask', '')
  nu_args['gateway'] = args.get('gateway', '')
  nu_args['dns_servers'] = args.get('dns_servers', '')
  nu_args['dns_search_path'] = args.get('dns_search_path', '')
  nu_args['autonegotiation'] = args.get('autonegotiation', '')
  nu_args['network_speed'] = args.get('network_speed', '')
  nu_args['ntp_servers'] = args.get('ntp_servers', '')
  nu_args['admin_email'] = args.get('admin_email', '')
  nu_args['timezone'] = args.get('timezone', '')
  nu_args['smtp_servers'] = args.get('smtp_servers', '')
  nu_args['outgoing_email_sender'] = args.get('outgoing_email_sender', '')
  nu_args['errors'] = []
  nu_args['admin_pass'] = args.get('admin_pass', '')
  nu_args['admin_pass2'] = args.get('admin_pass2', '')
  nu_args['testurls'] = args.get('testurls', '')
  nu_args['step'] = args.get('step', '%d' % 0)
  nu_args['eula'] = args.get('eula', '')

  if args.has_key('back'):
    nu_args['back'] = 0
  if args.has_key('next'):
    nu_args['next'] = 1
  if args.has_key('commit'):
    nu_args['commit'] = 1
  if args.has_key('accept'):
    nu_args['accept'] = 1

  if nu_args['autonegotiation'] == 'on' or nu_args['autonegotiation'] == 'checked':
    nu_args['autonegotiation'] = 'checked'
  else:
    nu_args['autonegotiation'] = ''

  nu_args['dns_servers'] = CommaListQualifier(nu_args['dns_servers'])
  nu_args['dns_search_path'] = CommaListQualifier(
    nu_args['dns_search_path'])
  nu_args['ntp_servers'] = CommaListQualifier(nu_args['ntp_servers'])

  return nu_args


# check all basic network parameters
# IP
# crawl IP (for 8ways)
# netmask
# gateway
#
# returns list of errors (may be [] if all is OK)
def CheckIPParms(serve_ip, switch_ip, crawl_ip, netmask, gateway, autonegotiation, network_speed):
  Errors = []

  # first check all arguments
  if applianceType == "CLUSTER":
    checks = [
      ('EXTERNAL_SWITCH_IP' , switch_ip, webserver_base.GetMsg('ILLEGAL_SWITCH_IP_SPECIFIED')),
      ('EXTERNAL_CRAWL_IP' , crawl_ip, webserver_base.GetMsg('ILLEGAL_CRAWL_IP_SPECIFIED')),
      ]
  else:
    checks = []


  if autonegotiation == '':
    autonegotiation =  0
  else:
    autonegotiation = 1

  if network_speed == '':
    network_speed =  0

  checks = checks + [
    ('EXTERNAL_WEB_IP' , serve_ip, webserver_base.GetMsg('ILLEGAL_IP_ADDRESS_SPECIFIED')),
    ('EXTERNAL_NETMASK' , netmask, webserver_base.GetMsg('ILLEGAL_NETMASK_SPECIFIED')),
    ('EXTERNAL_DEFAULT_ROUTE' , gateway, webserver_base.GetMsg('ILLEGAL_GATEWAY_SPECIFIED')),
    ('SERVERIRON_AUTONEGOTIATION' , autonegotiation,
     webserver_base.GetMsg('ILLEGAL_AUTONEGOTIATION_SPECIFIED')),
    ('ONEBOX_NETCARD_SETTINGS' , int(network_speed),
     webserver_base.GetMsg('ILLEGAL_NETWORKSPEED_SPECIFIED')),
    ]


  for param, value, msg in checks:
    errors = validator_config.ValidateValue(param, value)
    if errors not in validatorlib.VALID_CODES:
      Errors.append(msg)

  # extra check: make sure all IP's are on the same network:
  if applianceType == "ONEBOX" or applianceType == "MINI" or applianceType == "SUPER":
    networks = map(lambda x, m=netmask: andIP(x, m),
                   (serve_ip, gateway))
  elif applianceType == "CLUSTER":
    networks = map(lambda x, m=netmask: andIP(x, m),
                   (serve_ip, switch_ip, crawl_ip, gateway))
  else:
    networks = ()
  same_network = 1
  for network in networks[1:]:
    if network != networks[0]: same_network = 0
  if not same_network:
    Errors.append(webserver_base.GetMsg('ALL_IPS_AND_GATEWAY_MUST_BE_ON_SAME_NETWORK'))

  if applianceType == "CLUSTER":
    # we check that the gateway does not collide either.
    # This might not kill the serveriron, but is guaranteed not work
    # for the customer
    if gateway in (serve_ip, switch_ip, crawl_ip):
      Errors.append(webserver_base.GetMsg('GATEWAY_MUST_NOT_COLLIDE_WITH_OTHER_IPS'))

  return Errors

#
# ShowAllDiagnostics
#
def ShowAllDiagnostics(serve_ip, gateway, dns_servers, smtp_server,
                       ntp_servers, testurls):
  network_diag.RESULT = []
  if testurls != '':
    for url in string.split(testurls, '\n'):
      network_diag.check_url(string.strip(url), string.split(dns_servers,','))
  for server in string.split(ntp_servers, ","):
    network_diag.Check_NTP(server)
  network_diag.Check_SMTP(smtp_server, serve_ip)
  for server in string.split(dns_servers, ","):
    network_diag.Check_DNS(server)
  network_diag.Check_Gateway(gateway)
  return ShowDiagMessages(network_diag.RESULT, 6)


# see if the network settings we just set seem to work out ok.
#
# the only thing we do here is making sure we can ping the gateway
def ShowIPDiagnostics(gateway):
  network_diag.RESULT = []
  network_diag.Check_Gateway(gateway)
  return ShowDiagMessages(network_diag.RESULT,2)

# check all DNS parameters
# DNS
# searchpath
# returns list of errors (may be [] if all is OK)
def CheckDnsParms(DnsServers=None, SearchPath=None):
  return CheckItems([
    ('BOT_DNS_SERVERS' , DnsServers,
      webserver_base.GetMsg('ILLEGAL_DNS_SERVERS_SPECIFIED')),
    ('DNS_SEARCH_PATH' , SearchPath,
      webserver_base.GetMsg('ILLEGAL_SEARCH_PATH_SPECIFIED')),
    ])

# check all Time parameters
# DNSNTP_SERVERS
# TIMEZONE
# returns list of errors (may be [] if all is OK)
def CheckTimeParms(Ntp=None, timeZone=None):
  Ntp = normalize(Ntp)
  NtpServers = map(string.strip, string.split(Ntp, ","))

  errors = CheckItems([
    ('NTP_SERVERS' , NtpServers, webserver_base.GetMsg('ILLEGAL_NTPSERVER_SPECIFIED')),
    ])
  if not timeZone in map(lambda x: x[0], webserver_config_template.TIMEZONES):
    errors.append(webserver_config_template.TIMEZONE_ERROR % timeZone)
  return errors

def ShowNTPDiagnostics(servers):
  network_diag.RESULT = []
  for server in string.split(servers, ","):
    network_diag.Check_NTP(server)
  return ShowDiagMessages(network_diag.RESULT, 4)

# check all DNS and Time parameters
# DNS_SERVERS
# TIMEZONE
# DNSNTP_SERVERS
# TIMEZONE
# returns list of errors (may be [] if all is OK)
def ShowDNSMailDiagnostics(servers, Smtp, my_ip):
  network_diag.RESULT = []
  for server in string.split(servers, ","):
    try:
      network_diag.Check_DNS(server)
    except:
      # who knows what exceptions
      # the customer's network may bring us
      # better be cautious
      traceback.print_exc()
  try:
    network_diag.Check_SMTP(Smtp, my_ip)
  except:
    # who knows what exceptions
    # the customer's network may bring us
    # better be cautious
    traceback.print_exc()
  return ShowDiagMessages(network_diag.RESULT, 3)


def CheckMailParms(Smtp, outgoing_email_sender):
  return CheckItems([
    ('SMTP_SERVER' , normalize(Smtp), webserver_base.GetMsg('ILLEGAL_SMTPSERVER_SPECIFIED')),
    ('OUTGOING_EMAIL_SENDER' , normalize(outgoing_email_sender), webserver_base.GetMsg('ILLEGAL_OUTGOING_EMAIL_SENDER_SPECIFIED')),
    ])

# check misc parameters
# Syslog
# admin email and password
def CheckMiscParms(admin_email=None, admin_pass=None,
                   admin_pass2=None, emptyPasswordIsOK = 0):
  errors = CheckItems([
    ('VALIDATE_EMAIL', admin_email, webserver_base.GetMsg('INVALID_ADMIN_EMAIL_ADDRESS')),
    ])
  if emptyPasswordIsOK and admin_pass == '' and admin_pass2 == '':
    return errors
  if admin_pass != None:
    if admin_pass2 == None:
      errors.append(webserver_base.GetMsg('MUST_REPEAT_ADMIN_PASSWORD'))
    elif admin_pass2 != admin_pass:
      errors.append(webserver_base.GetMsg('ADMIN_PASSWORDS_DONT_MATCH'))
  if admin_pass == '':
    errors.append(webserver_base.GetMsg('ADMIN_PASSWORDS_MUST_ENTER'))
  return errors

def ShowMiscDiagnostics():
  network_diag.RESULT = []
  return ShowDiagMessages(network_diag.RESULT, 5)

# check some URLs on reachability
# does not test robots.txt and such
def CheckURLParms(TestUrls=None):
  TestUrls = string.split(TestUrls)
  Errors = []
  for url in TestUrls:
    result = validator_config.ValidateValue('VALIDATE_URL', url)
    if result == validatorlib.ERR_URL_NO_PATH:
      # Validator doesn't like domain only urls such as http://www.google.com
      result = validator_config.ValidateValue('VALIDATE_URL', url + '/')
    if result not in validatorlib.VALID_CODES:
      Errors.append("%s: %s %s" % (url,
                    webserver_base.GetMsg('NOT_A_VALID_URL'), repr(result)))
  return Errors

def ShowURLDiags(urls, dns_servers):
  network_diag.RESULT = []
  for url in string.split(urls,'\n'):
    url = string.strip(url)
    if url == '': continue
    network_diag.check_url(string.strip(url), string.split(dns_servers,','))
  return ShowDiagMessages(network_diag.RESULT, 6)

# given a list of (variable_name, value, error_msg) tuples,
# perform the checks and return a list of errors that occured
def CheckItems(checks):
  Errors = []
  for param, value, msg in checks:
    errors = validator_config.ValidateValue(param, value)
    if errors not in validatorlib.VALID_CODES:
      Errors.append(msg)
  return Errors

#############################################################################
#
# H E L P E R   F U N C T I O N S
#
#############################################################################

# determine "AND" of two IP adresses
# e.g. network address == IP_ADDRESS AND NETMASK
def andIP(base, incr):
  if base == None or incr == None: return None
  try:
    octets1 = map(int, string.split(base, '.'))  # split into octets
    octets2 = map(int, string.split(incr, '.'))
  except ValueError:
    return None
  resultOctets = map(lambda x,y: str(x & y), octets1, octets2)
  return string.join(resultOctets, '.')


# read all config parameters into a dictionary and return it
def readGlobalConfig():
  in_params = {}
  ok,response = ar_client.GetAllParamsIntoDict(in_params)
  if not ok:
    return None
  return in_params

# create a config parameter from a dictionary
#
def writeGlobalConfig(in_params):
  global params
  ok = ar_client.SetParamsFromDict(in_params)
  ok2 = ar_client.SaveParams()
  ar_client.GetAllParamsIntoDict(params) # re-read parameters
  if not (ok and ok2):
    return 0
  return 1

# Given a list of error strings, build a nice HTML table from it
def ErrorTable(errors):
  errorlines = []
  if errors:
    for error in errors:
      errorlines.append(webserver_config_template.ERROR_LINE % error)
    return webserver_config_template.ERROR_TABLE % string.join(
      errorlines, '\n')
  return '' # no errors

# Given a list of diagnostic tuples ((type, value, explanation)), build a nice
# colored HTML table from it
# We show all parameters, up to the current step.
# for the previous steps, we just show the value
# for current step, we mark status in red/green (with explanation)
# passed

# TODO: make all 'description text' fron network diag
# internationalized so we we don't need
# to use these translation tables
#
def ShowDiagMessages(diag_msgs, step):
  itemsToShowhow= {}
  for i in diag_msgs:
    if i[2] == "OK": continue
    if itemsToShowhow.has_key(i[0]):
      itemsToShowhow[i[0]].append((i[1], i[2]))
    else:
      itemsToShowhow[i[0]] = [(i[1], i[2])]

  def id(x) :
    if x != None: return x
    else: return ''
  def print_list(x):
    return string.join(x, ', ')


  # triples of the form
  # (PARAMETER_NAME  -- as in crawler.common
  #  display name -- what should be shown on the screen
  #  value function -- how should value be printed
  paramsToScreenname = (
    ('EXTERNAL_WEB_IP', webserver_base.GetMsg('IP_ADDRESS'), id),
    ('EXTERNAL_SWITCH_IP', webserver_base.GetMsg('SWITCH_IP'), id),
    ('EXTERNAL_CRAWL_IP', webserver_base.GetMsg('CRAWL_IP'), id),
    ('EXTERNAL_NETMASK', webserver_base.GetMsg('NETMASK'), id),
    ('EXTERNAL_DEFAULT_ROUTE', network_diag.SERVICE_NAMES[network_diag.GATEWAY], id),
    ('SERVERIRON_AUTONEGOTIATION', webserver_base.GetMsg('AUTONEGOTIATION'), id),
    ('ONEBOX_NETCARD_SETTINGS', webserver_base.GetMsg('NETWORK_SPEED'), id),
    ('BOT_DNS_SERVERS', network_diag.SERVICE_NAMES[network_diag.DNS_SERVER], id),
    ('DNS_SEARCH_PATH', webserver_base.GetMsg('DNS_SEARCH_PATH'), id),
    ('SMTP_SERVER', network_diag.SERVICE_NAMES[network_diag.SMTP_SERVER], id),
    ('OUTGOING_EMAIL_SENDER', webserver_base.GetMsg('OUTGOING_EMAIL_SENDER'), id),
    ('NTP_SERVERS', network_diag.SERVICE_NAMES[network_diag.NTP_SERVER], print_list),
    ('TIMEZONE', webserver_base.GetMsg('YOUR_LOCAL_TIMEZONE'), id),
    )

  diag_lines = []
  # now format what we got - order everything but testurls
  for i in map(lambda x: x[1], paramsToScreenname):
    if applianceType != 'CLUSTER':
      if i in (webserver_base.GetMsg('CRAWL_IP'),
               webserver_base.GetMsg('SWITCH_IP'),
               webserver_base.GetMsg('AUTONEGOTIATION')):
        continue # these items don't exist for 1ways
    else:
      if i == webserver_base.GetMsg('NETWORK_SPEED'):
        continue # these items don't exist for clusters
    if i in itemsToShowhow.keys():
      for j in itemsToShowhow[i]:
        diag_lines.append(DiagLine((0, i) + j))

  # testurls are special as not controlled by params, so:
  if step >= 6:
    for i in itemsToShowhow.keys():
      if i == network_diag.SERVICE_NAMES[network_diag.TEST_URL]:
        for j in itemsToShowhow[i]:
          diag_lines.append(DiagLine((0, i) + j))

  if len(diag_lines) == 0:
    return ''
  return webserver_config_template.DIAG_TABLE % string.join(diag_lines, '\n')

# Element of the table for diagnostic output
def DiagLine((grayed, type, name, status)):
  BadPrefix=""
  BadSuffix=""
  BgColor= ''
  if grayed:
    fontcolor = webserver_config_template.BG_GRAY2
  else:
    fontcolor = webserver_config_template.BG_BLACK
  if status == 'OK':
    BgColor= webserver_config_template.BG_GREEN # light pastel green
  elif status != '':
    BadPrefix="<B>"
    BadSuffix="</B>"
    BgColor = webserver_config_template.BG_RED

  return (webserver_config_template.DIAG_LINE % {
    'font_color'   : fontcolor,
    'bold_on'      : BadPrefix,
    'bold_off'     : BadSuffix,
    'type'         : type,
    'value'        : name,
    'status'       : status,
    'status_color' : BgColor,
    })

def log(string):
  sys.stderr.write(time.asctime(time.gmtime(time.time())) + " " +
                   string +"\n")

# try to get DHCP info
# TODO NOTE: Also, we can't really DHCP detect anything on an 8way (well,
# unclear if we can do this through the serveriron)
#
# Note: this needs to run as root, so we go through the secure_script_wrapper
def GetDHCPInfo():
  dhcp_data = None
  try:
    (status, output) = commands.getstatusoutput(
      "cd %s/local/google/bin/ && " % ent_home
      + "./secure_script_wrapper -p2 "
      + "%s/local/google3/enterprise/legacy/util/dhcp_client.py " % ent_home
      )
    dhcp_data = eval(output) # secure ?
  except:
    return {}

  # if dhcp does not yield an SMTP server entry, try to get MX record
  if ( not dhcp_data.has_key('SMTP_SERVER') and
       dhcp_data.has_key('DOMAIN_NAME') ):

    # so for instance the google DHCP server returns DOMAIN_NAME
    # corp.google.com, for which no MX record is assigned.
    # That's why we now try all suffixes of DOMAIN_NAME and try to find
    # MX records:
    domainName = string.split(dhcp_data['DOMAIN_NAME'], "\000")[0]
    while 1:
      status, server = commands.getstatusoutput(
        "alarm 2 host -v -t mx %s 2>/dev/null|grep MX|head -1|awk '{print $6}'"
        % commands.mkarg(domainName)
        )
      if server != '': break
      comps = string.split(domainName, ".", 1)
      if  len(comps) != 2:
        break # reached TLD
      domainName = comps[1]
    if server != '':
      dhcp_data['SMTP_SERVER'] = server
  return dhcp_data

#############################################################################
#
# some globals to help us validate parameters
#
#############################################################################

validator_config = None

applianceType = None
ent_home = None
ent_version = None
applianceID = None
ar_client = None
params = None

def main():
  global applianceType
  global ent_home
  global ent_version
  global applianceID
  global ar_client
  global params
  global validator_config

  def usage():
    return sys.argv[0]

  if len(sys.argv) != 2:
    sys.exit(usage())

  validator_config = entconfig.EntConfig(sys.argv[1])
  if validator_config.Load() != 1:
    sys.exit("Could not load the config file")

  # log network diagnostics stuff
  network_diag.LOGFILE = sys.stderr

  # wait until adminrunner is up
  while 1:
    try:
      ar_client = adminrunner_client.AdminRunnerClient('localhost', 2100)
      break
    except:
      time.sleep(10)

  # read the config parameters
  # we assume that the appliancetype is not changing without restarting
  # this server
  params = readGlobalConfig()
  if params == None:
    print webserver_base.GetMsg('ERROR_LOADING_CONFIG_FILE')
    return
  ent_home = params['ENTERPRISE_HOME']
  ent_version = params['VERSION']
  applianceType = params.get('ENT_CONFIG_TYPE', 'UNKNOWN')
  applianceID = params.get('ENT_CONFIG_NAME', 'INVALID ID')

  WEBSERVERPORT = 1111

  os.chdir('../../../../googledata/enterprise/statichtml')

  # Run the standard webserver
  # to make we don't run internal functions by accident, we
  # explicitely
  webserver_base.handlers = {
    '__name__' : None,            # hack to keep webserver_base happy
    'home_page' : home_page,
    'cgi_main_config' : cgi_main_config,
    'cgi_haltappliance' : cgi_haltappliance,
    'cgi_restartappliance' : cgi_restartappliance,
    'cgi_resetwizard' : cgi_resetwizard,
    'cgi_selfdestruct' : cgi_selfdestruct,  # clean the box up for good
    'cgi_help_page' : cgi_help_page, # a static help page
    'cgi_enablesshd' : cgi_enablesshd,
    'cgi_disablesshd' : cgi_disablesshd,
    }
  extra_headers = [('Cache-Control', 'no-cache')]
  # Prep:  define the languages we parse.
  # localizer.BestLanguage defaults to the first language on the list if
  # there is no match for the user-requested language.  Set this to English
  language_list = [ 'en' ]
  language_list.extend([ l.replace('-', '_') for l in languages.LANG_LIST ])
  # The file to parse localizations from
  xlb_file = ('%s/local/google3/enterprise/i18n/WebserverConfigMessages' %
              ent_home)
  webserver_base.go(forking=0, port_range=(WEBSERVERPORT, WEBSERVERPORT),
                    extra_http_headers=extra_headers,
                    xlb_file=xlb_file,
                    languages=language_list)


def localize_messages():
  '''Localize the messages for the locale of this request by reloading
  template.
  '''
  reload(webserver_config_template)

if __name__ == '__main__':
  main()
