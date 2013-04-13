#!/usr/bin/python2.4
#
# Templates for configuration webserver
# (c) 2002 and onward, Google, Inc.
# Author: Max Ibel
#

# every template is typed either as const template, or level-N-template.
# a level N templated can be substituted N times,
#  e.g. "<b>%s</b>" is a level-1 template
# a level-2-template is something like
#  colored_Bold = "<bgcolor=%s><b>%%s</b>"
#  and can be used to make level-1 templates, e.g.
#    blue_bold = colored_bold % "0x0000ff"

from google3.enterprise.legacy.web import webserver_base
import string

FRAME_TABLE = """
<table width="90%%" align=center border=0 cellpadding=2 cellspacing=0><tr bgcolor=#3366CC><td>
<table cellSpacing=0 align=center cellPadding=2 width="100%%" border=0 bgcolor=#3366CC>
"""
FRAME_TABLE1 = """
<tr bgcolor=#ffffff><td>
"""

FRAME_TABLEEND = """
</td></tr></table>
</tr></td></table>
"""

FRAME_TABLE_SEPERATOR="""
<tr><td colspan=2><hr size=1 color=#3366CC></td></tr>
"""

# produce a nice blue frame around some HTML object
# level-2-template (used to shunt a lvl-1 template in)
FRAME_OBJECT2 = """
<table width=90%%%% align=center border=0 cellpadding=0 cellspacing=0><tr><td>
<table cellSpacing=0 cellPadding=0 border=0>
<tr><td align=center nowrap><font face=arial,sans-serif><b>%s%s%s%s</b></td></tr></table>
</td></tr></table>
"""

TAB_OBJECT = """
<table border=0 cellpadding=2 cellspacing=2 width="90%%%%" align=center><tr>
<td bgcolor=%s width="20%%%%" nowrap><font face=arial,sans-serif color=%s><b>%s</b><br><font size=-1>%s</td>
<td bgcolor=%s width="20%%%%" nowrap><font face=arial,sans-serif color=%s><b>%s</b><br><font size=-1>%s</td>
<td bgcolor=%s width="20%%%%" nowrap><font face=arial,sans-serif color=%s><b>%s</b><br><font size=-1>%s</td>
<td bgcolor=%s width="20%%%%" nowrap><font face=arial,sans-serif color=%s><b>%s</b><br><font size=-1>%s</td>
<td bgcolor=%s width="20%%%%" nowrap><font face=arial,sans-serif color=%s><b>%s</b><br><font size=-1>%s</td>
</tr></table>
"""

SMTP_SEP = FRAME_TABLE_SEPERATOR + """
</table></td></tr></table> <b> """ + webserver_base.GetMsg('MAIL_SERVER_SETTINGS') + """
</b> <table border=0 width="100%%" bgcolor=ffffff><tr><td width="1%%">
<center>

<table border=0 cellpadding=2 cellspacing=0 width="100%%%%">
""" + FRAME_TABLE_SEPERATOR

SPACER = """<table width="100%%" border="0" cellpadding="0" cellspacing="0">
<tbody>
<tr>
<td align=right valign=bottom bgcolor="#d8e4f1">
<img src="images/cleardot.gif" alt="" height=2></td></tr></tbody></table>"""


CONGRATULATIONS_PAGE_DIAG = SPACER + """ <p>
<table width="90%%%%" align=center border=0 cellpadding=2 cellspacing=0><tr bgcolor=3366CC><td>

<table cellSpacing=0 align=center cellPadding=2 width="100%%%%" border=0 bgcolor=3366CC><tr bgcolor=ffffff><td>
<table border=0 width="100%%%%" bgcolor=ffffff><tr><td width="1%%%%">


</td></tr><tr><td nowrap width="1%%%%">
<font size=-1><b>%s:</b></font></td>
<td>
<font size=-1>%%(serve_ip)s</font>

</td></tr><tr><td nowrap width="1%%%%">
<font size=-1><b>%s</b></font></td>
<td>
<font size=-1>%%(netmask)s</font>


</td></tr><tr><td nowrap width="1%%%%">
<font size=-1><b>%s:</b></font></td><td>
<font size=-1>%%(gateway)s</font>

</td></tr><tr><td nowrap width="1%%%%"></td><td>
</td></tr><tr><td colspan=2>
<hr size=1 color=3366CC></td></tr><tr><td  nowrap width="1%%%%">


<font size=-1><b>%s:</b></font></td><td>
<font size=-1>%%(dns_servers)s</font>


</td></tr><tr><td nowrap width="1%%%%">
<font size=-1><b>%s:</b></font></td><td>
<font size=-1>%%(dns_search_path)s</font>

</td></tr><tr><td colspan=2>
<hr size=1 color=3366CC></td></tr><tr><td nowrap width="1%%%%">
<font size=-1><b>%s:</b></font></td><td>
<font size=-1>%%(smtp_servers)s</font>

</td></tr>
<tr><td  nowrap width="1%%%%">
<font size=-1><b>%s:</b></font></td><td>
<font size=-1>%%(outgoing_email_sender)s</font>
</td></tr>
<tr><td nowrap width="1%%%%"></td><td>
</td></tr><tr><td colspan=2>
<hr size=1 color=3366CC></td></tr>

<tr><td nowrap width="1%%%%">
<font size=-1><b>%s:</b></font></td><td>
<font size=-1>%%(timezone_screen)s</font>
</td></tr>

<tr><td nowrap width="1%%%%">
<font size=-1><b>%s:</b></font></td><td>
<font size=-1>%%(ntp_servers)s</font>
</td></tr>
<tr><td colspan=2>
<hr size=1 color=3366CC></td></tr>

      <tr>
        <td><font size=-1><b>%s:</b></td><td><font size=-1>%s
</td></tr><tr><td>
         <b> <font size=-1>%s:</b></td><td>*******
                 </td></tr><tr><td>
          <font size=-1><b>%s:</b></td><td><font size=-1>%%(admin_email)s

          </font>
        </td>
      </tr>
<tr><td colspan=2>
<hr size=1 color=3366CC></td></tr><tr><td nowrap width="1%%%%" valign=top>
<font size=-1><b>%s:</b></td><td>
<font size=-1>%s

</td></tr></table>

</td></tr></table>
</tr></td></table>
""" % (webserver_base.GetMsg('IP_ADDRESS'),
       webserver_base.GetMsg('NETMASK'),
       webserver_base.GetMsg('GATEWAY'),
       webserver_base.GetMsg('DNS_SERVERS'),
       webserver_base.GetMsg('DNS_SEARCH_PATH'),
       webserver_base.GetMsg('SMTP_SERVER'),
       webserver_base.GetMsg('OUTGOING_EMAIL_SENDER'),
       webserver_base.GetMsg('YOUR_LOCAL_TIMEZONE'),
       webserver_base.GetMsg('NTP_SERVERS'),
       webserver_base.GetMsg('USERNAME'),
       'admin',
       webserver_base.GetMsg('CHANGE_PASSWORD'),
       webserver_base.GetMsg('EMAIL_ADDRESS'),
       webserver_base.GetMsg('TESTURLS'),
       string.join(string.split("""%(testurls)s""", ' '), '\n') )

CONGRATULATIONS_PAGE_DIAG_8WAY = SPACER + """ <p>
<table width="90%%%%" align=center border=0 cellpadding=2 cellspacing=0><tr bgcolor=3366CC><td>

<table cellSpacing=0 align=center cellPadding=2 width="100%%%%" border=0 bgcolor=3366CC><tr bgcolor=ffffff><td>
<table border=0 width="100%%%%" bgcolor=ffffff><tr><td width="1%%%%">


</td></tr><tr><td nowrap width="1%%%%">
<font size=-1><b>%s:</b></font></td>
<td>
<font size=-1>%%(serve_ip)s</font>

</td></tr><tr><td nowrap width="1%%%%">
<font size=-1><b>%s:</b></font></td>
<td>
<font size=-1>%%(switch_ip)s</font>

</td></tr><tr><td nowrap width="1%%%%">
<font size=-1><b>%s:</b></font></td>
<td>
<font size=-1>%%(crawl_ip)s</font>

</td></tr><tr><td nowrap width="1%%%%">
<font size=-1><b>%s</b></font></td>
<td>
<font size=-1>%%(netmask)s</font>


</td></tr><tr><td nowrap width="1%%%%">
<font size=-1><b>%s:</b></font></td><td>
<font size=-1>%%(gateway)s</font>

</td></tr><tr><td nowrap width="1%%%%"></td><td>
</td></tr><tr><td colspan=2>
<hr size=1 color=3366CC></td></tr><tr><td  nowrap width="1%%%%">


<font size=-1><b>%s:</b></font></td><td>
<font size=-1>%%(dns_servers)s</font>


</td></tr><tr><td nowrap width="1%%%%">
<font size=-1><b>%s:</b></font></td><td>
<font size=-1>%%(dns_search_path)s</font>

</td></tr><tr><td colspan=2>
<hr size=1 color=3366CC></td></tr><tr><td nowrap width="1%%%%">
<font size=-1><b>%s:</b></font></td><td>
<font size=-1>%%(smtp_servers)s</font>

</td></tr>
<tr><td  nowrap width="1%%%%">
<font size=-1><b>%s:</b></font></td><td>
<font size=-1>%%(outgoing_email_sender)s</font>
</td></tr>
<tr><td nowrap width="1%%%%"></td><td>
</td></tr><tr><td colspan=2>
<hr size=1 color=3366CC></td></tr>

<tr><td nowrap width="1%%%%">
<font size=-1><b>%s:</b></font></td><td>
<font size=-1>%%(timezone_screen)s</font>
</td></tr>

<tr><td nowrap width="1%%%%">
<font size=-1><b>%s:</b></font></td><td>
<font size=-1>%%(ntp_servers)s</font>
</td></tr>
<tr><td colspan=2>
<hr size=1 color=3366CC></td></tr>

      <tr>
        <td><font size=-1><b>%s:</b></td><td><font size=-1>%s
</td></tr><tr><td>
         <b> <font size=-1>%s:</b></td><td>*******
                 </td></tr><tr><td>
          <font size=-1><b>%s:</b></td><td><font size=-1>%%(admin_email)s

          </font>
        </td>
      </tr>
<tr><td colspan=2>
<hr size=1 color=3366CC></td></tr><tr><td nowrap width="1%%%%" valign=top>
<font size=-1><b>%s:</b></td><td>
<font size=-1>%s

</td></tr></table>

</td></tr></table>
</tr></td></table>
""" % (webserver_base.GetMsg('IP_ADDRESS'),
       webserver_base.GetMsg('SWITCH_IP'),
       webserver_base.GetMsg('CRAWL_IP'),
       webserver_base.GetMsg('NETMASK'),
       webserver_base.GetMsg('GATEWAY'),
       webserver_base.GetMsg('DNS_SERVERS'),
       webserver_base.GetMsg('DNS_SEARCH_PATH'),
       webserver_base.GetMsg('SMTP_SERVER'),
       webserver_base.GetMsg('OUTGOING_EMAIL_SENDER'),
       webserver_base.GetMsg('YOUR_LOCAL_TIMEZONE'),
       webserver_base.GetMsg('NTP_SERVERS'),
       webserver_base.GetMsg('USERNAME'),
       'admin',
       webserver_base.GetMsg('CHANGE_PASSWORD'),
       webserver_base.GetMsg('EMAIL_ADDRESS'),
       webserver_base.GetMsg('TESTURLS'),
       string.join(string.split("""%(testurls)s""", ' '), '\n') )

# help text is a link to a global page which has all the whatis text
NO_WHATIS_HELP = {
  'whatis_serve_ip'              : '', # on the big form, we give no explanations
  'example_serve_ip'             : '',
  'whatis_switch_ip'             : '',
  'whatis_crawl_ip'              : '',
  'whatis_autonegotiation'       : '',
  'whatis_network_speed'         : '',
  'whatis_netmask'               : '',
  'example_netmask'              : '',
  'whatis_gateway'               : '',
  'example_gateway'              : '',
  'whatis_dns'                   : '',
  'example_dns'                  : '',
  'whatis_dns_path'              : '',
  'example_dns_path'             : '',
  'whatis_smtp'                  : '',
  'whatis_outgoing_email_sender' : '',
  'whatis_timezone'              : '',
  'whatis_ntp'                   : '',
  'example_ntp'                  : '',
  'alert_ntp'                    : '',
  'whatis_admin_mail'            : '',
  'admin_mail1'                  : '',
  'admin_mail2'                  : '',
  'admin_mail3'                  : '',
  'admin_mail4'                  : '',
  'whatis_testurl'               : '',
  'testurls_bullet1'             : '',
  'testurls_bullet2'             : '',
  'testurls_example1'            : '',
  'testurls_example2'            : '',
  'help_network_settings'        : '(<A href = /help_page#network_settings>Help</a>)',
  'help_dns_and_mail_settings'   : '(<A href = /help_page#dns_and_mail_settings>Help</a>)',
  'help_time_settings'           : '(<A href = /help_page#time_settings>Help</a>)',
  'help_misc_settings'           : '(<A href = /help_page#misc_settings>Help</a>)',
  'help_testurls'                : '(<A href = /help_page#testurls>Help</a>)',
  }

MISC_HELPER_NOHELP = {
  'whatis_tablesep'              : '',
  'whatis_lastsep'               : FRAME_TABLE_SEPERATOR,
  'header_seperator'             : FRAME_TABLE_SEPERATOR,
  'surrounding_table'            : '',
  'surrounding_table1'           : '',
  'surrounding_tableend'         : '',
  'smtp_sep'                     : SMTP_SEP,
  'separate_commas'              : '',

# NOTE
# The code uses the template in two places, one of which has help strings
# the other of which does not.  The formatting tokens need to be omitted when
# the help strings are not displayed, otherwise an empty bulletted list will
# be displayed.  We therefore use symbols to represent the formatting tokens
# and substitute empty strings when we aren't displaying the help messages.

  'basic_network_message_br'     : '',
  'basic_network_message_ul'     : '',
  'basic_network_message_ul_end' : '',
  'basic_network_message_li'     : '',
  'basic_network_message_li_end' : '',
  'example'                      : '',
  'colon'                        : '',
  }

WHATIS_HELP = { # in the wizard, we display the whatis text directly so don't have a help page
  'whatis_serve_ip'              : webserver_base.GetMsg('WHATIS_SERVE_IP') + "<BR>",
  'example_serve_ip'             : webserver_base.GetMsg('EXAMPLE_SERVE_IP'),
  'whatis_switch_ip'             : webserver_base.GetMsg('WHATIS_SWITCH_IP') + "<BR>",
  'whatis_crawl_ip'              : webserver_base.GetMsg('WHATIS_CRAWL_IP') + "<BR>",
  'whatis_autonegotiation'       : webserver_base.GetMsg('WHATIS_SERVERIRON_AUTONEGOTIATION') + "<BR>",
  'whatis_network_speed'         : webserver_base.GetMsg('WHATIS_NETWORK_SPEED') + "<BR>",
  'whatis_netmask'               : webserver_base.GetMsg('WHATIS_NETMASK') + "<BR>",
  'example_netmask'              : webserver_base.GetMsg('EXAMPLE_NETMASK'),
  'whatis_gateway'               : webserver_base.GetMsg('WHATIS_DEFAULT_GATEWAY') + "<BR>",
  'example_gateway'              : webserver_base.GetMsg('EXAMPLE_DEFAULT_GATEWAY'),
  'whatis_dns'                   : webserver_base.GetMsg('WHATIS_DNS_SERVER') + "<BR>",
  'example_dns'                  : webserver_base.GetMsg('EXAMPLE_DNS_SERVER'),
  'whatis_dns_path'              : webserver_base.GetMsg('WHATIS_DNS_SEARCH_PATH') + "<BR>",
  'example_dns_path'             : webserver_base.GetMsg('EXAMPLE_DNS_SEARCH_PATH'),
  'whatis_smtp'                  : webserver_base.GetMsg('WHATIS_SMTP_SERVER') + "<BR>",
  'whatis_outgoing_email_sender' : webserver_base.GetMsg('WHATIS_OUTGOING_EMAIL_SENDER') + "<BR>",
  'whatis_timezone'              : webserver_base.GetMsg('WHATIS_TIME_ZONE') + "<BR>",
  'whatis_ntp'                   : webserver_base.GetMsg('WHATIS_NTP_SERVER') + "<BR>",
  'example_ntp'                  : webserver_base.GetMsg('EXAMPLE_NTP_SERVER'),
  'alert_ntp'                    : webserver_base.GetMsg('ALERT_NTP_SERVER'),
  'whatis_admin_mail'            : webserver_base.GetMsg('WHATIS_ADMIN_ACCOUNT') + "<BR>",
  'admin_mail1'                  : webserver_base.GetMsg('ADMIN_ACCOUNT_BULLET1'),
  'admin_mail2'                  : webserver_base.GetMsg('ADMIN_ACCOUNT_BULLET2'),
  'admin_mail3'                  : webserver_base.GetMsg('ADMIN_ACCOUNT_BULLET3'),
  'admin_mail4'                  : webserver_base.GetMsg('ADMIN_ACCOUNT_BULLET4'),
  'whatis_testurl'               : webserver_base.GetMsg('WHATIS_TESTURLS') + "<BR>",
  'testurls_bullet1'             : webserver_base.GetMsg('TESTURLS_BULLET1'),
  'testurls_bullet2'             : webserver_base.GetMsg('TESTURLS_BULLET2'),
  'testurls_example1'            : webserver_base.GetMsg('TESTURLS_EXAMPLE1'),
  'testurls_example2'            : webserver_base.GetMsg('TESTURLS_EXAMPLE2'),
  'help_network_settings'        : '',
  'help_dns_and_mail_settings'   : '',
  'help_time_settings'           : '',
  'help_misc_settings'           : '',
  'help_testurls'                : '',
  }

MISC_HELPER_HELP = {
  'whatis_tablesep'              : FRAME_TABLE_SEPERATOR,
  'whatis_lastsep'               : '',
  'header_seperator'             : '',
  'surrounding_table'            : FRAME_TABLE,
  'surrounding_table1'           : FRAME_TABLE1,
  'surrounding_tableend'         : FRAME_TABLEEND,
  'smtp_sep'                     : '',
  'separate_commas'              : webserver_base.GetMsg('SEPARATE_BY_COMMAS'),

# See note above in MISC_HELPER_NOHELP

  'basic_network_message_br'     : '<br>',
  'basic_network_message_ul'     : '<ul>',
  'basic_network_message_ul_end' : '</ul>',
  'basic_network_message_li'     : '<li>',
  'basic_network_message_li_end' : '</li>',
  'example'                      : webserver_base.GetMsg('EXAMPLE'),
  'colon'                        : ':',
  }

# lvl-0 template
# redirects to main config page
REDIRECT_PAGE = """ <html><head>
<meta content="text/html; charset=UTF-8" http-equiv="content-type">
<title>HTML REDIRECT</title> <meta
HTTP-EQUIV="REFRESH" CONTENT="0; URL=/main_config"> </head> <body>%s
</body> </html> """


# header of a page
# lvl-1 template
# needs the ID-#
PAGE_HEADER="""
<html><head>
<meta content="text/html; charset=UTF-8" http-equiv="content-type">
<title>%s</title>
<style>BODY {
        MARGIN-LEFT: 1em; MARGIN-RIGHT: 2em; FONT-FAMILY:
}
</STYLE>
<font face=arial,sans-serif>
</head>
<body text=#000000 vLink=#800080 aLink=#ff0000 link=#0000cc bgColor=#ffffff>

<table cellSpacing=0 cellPadding=2 width="100%%%%" border=0>
<tbody>
<tr>
<td width="1%%%%"><img height=59 alt=Google
      src="images/google_sm.gif" width=143 border=0> </td>
<td vAlign=center>
<table cellSpacing=0 cellPadding=2 width="100%%%%" border=0>
<tbody>
<tr bgColor=#3366CC>
<td vAlign=center><font color=#ffffff><b>%s</b></font></td>
</tr></tbody></table></td> </tr></tbody></table>
"""

PAGE_TEMPLATE_HEADER = PAGE_HEADER % (
  webserver_base.GetMsg('NETWORK_INSTALLATION'),
  webserver_base.GetMsg('NETWORK_INSTALLATION'))

PAGE_TEMPLATE_LICENSE_HEADER = PAGE_HEADER % (
  webserver_base.GetMsg('LICENSE_WELCOME'),
  webserver_base.GetMsg('LICENSE_WELCOME'))


# Header line  for wizard page (ie., Page 4 of 5)
HEADER_LINE = """
<H3>%s:%s</H3>
"""

# footer of a page
# const template
PAGE_TEMPLATE_FOOTER=("""</form>""" +
                      SPACER + """
<center><font color=#6f6f6f size=-1>&copy;2002-2007 Google
</center></font></body></html>
""")

# produce a nice blue frame around some HTML object
# level-1-template
FRAME_OBJECT = """
<table width=90%% align=center border=0 cellpadding=2 cellspacing=0><tr bgcolor=#3366CC><td>
<table cellSpacing=0 align=center cellPadding=2 width="100%%" border=0 bgcolor=#3366CC><tr bgcolor=#ffffff><td>
%s
</td></tr></table>
</tr></td></table>
"""


# 4 types of submit buttons
# with next button only, bot back and next, and only back buttons
# (also: commit)
SUBMIT_BUTTON_NEXT = """
<P> <table border=0 width=90%%%%><tr>
<td align=right valign=bottom>
<font size=-1>
<input type=submit name=next value="%s">
</font></td></tr></table>
""" % webserver_base.GetMsg('CONTINUE')

SUBMIT_BUTTON_BACK_NEXT = """
<table border=0 width="90%%%%" align=center><tr><td align=left>
<font size=-1>
<input type=submit name=back value="%s">
</font></td>
<td align=right valign=bottom>
<font face=arial,sans-serif size=-1>
<input type=submit name=next value="%s">
</font></td></tr></table>
""" % (webserver_base.GetMsg('BACK'),
       webserver_base.GetMsg('CONTINUE')
       )

SUBMIT_BUTTON_ACCEPT_REJECT = """
<center>
<table border=0 width="90%%%%" align=center><tr><td align=right width="60%%%%">
<font size=-1>
<input type=submit name=accept value="%s">
</font></td>
<td align=left valign=bottom>
<font face=arial,sans-serif size=-1>
<input type=submit name=reject value="%s">
</font></td></tr></table>
</center>
""" % (webserver_base.GetMsg('ACCEPT'),
       webserver_base.GetMsg('REJECT')
       )

SUBMIT_BUTTON_BACK = """
<P> <table border=0 width=90%%%%><tr><td align=left>
<font size=-1>
<input type=submit name=back value="%s">
</font></td>
</tr></table>
""" % webserver_base.GetMsg('BACK')

SUBMIT_BUTTON_COMMIT= """
<P> <table border=0 width=90%%%%><tr>
<td align=right valign=bottom>
<font size=-1>
<input type=submit name=commit value="%s">
</font></td></tr></table>
""" % webserver_base.GetMsg('MODIFY')

# config file could not be loaded.
# lvl-1 template - needs ID-# template
ERROR_LOADING_CONFIG_FILE = (PAGE_TEMPLATE_HEADER +
                             FRAME_OBJECT % webserver_base.GetMsg('ERROR_LOADING_CONFIG_FILE') +
                             PAGE_TEMPLATE_FOOTER)

# all parameters we want to lug along
#
##<input type=hidden value="%%(serve_ip)s" name=serve_ip>
##<input type=hidden value="%%(crawl_ip)s" name=crawl_ip>
##<input type=hidden value="%%(netmask)s" name=netmask>
##<input type=hidden value="%%(gateway)s" name=gateway>
##<input type=hidden value="%%(dns_servers)s" name=dns_servers>
##<input type=hidden value="%%(dns_search_path)s" name=dns_search_path>
##<input type=hidden value="%%(autonegotiation)s" name=autonegotiation>
##<input type=hidden value="%%(network_speed)s" name=network_speed>
##<input type=hidden value="%%(ntp_servers)s" name=ntp_servers>
##<input type=hidden value="%%(admin_email)s" name=admin_email>
##<input type=hidden value="%%(timezone)s" name=timezone>
##<input type=hidden value="%%(smtp_servers)s" name=smtp_servers>
##<input type=hidden value="%%(testurls)s" name=testurls>
##<input type=hidden value="%(outgoing_email_sender)s" name=outgoing_email_sender>


# IP setting details
# level-1 template - requires values for
# - IP
# - netmask
# - gateway
IP_SETTINGS = """
%%(surrounding_table)s
%%(surrounding_table1)s
<center>
<table border=0 cellpadding=2 cellspacing=0 width="100%%%%"><tr><td  width="1%%%%" valign=top>
<font size=-1>
%%(basic_network_message_br)s
</font></td></tr>
<tr><td colspan=2><hr size=1 color=3366CC></TD></TR>
</table>

<table border=0 cellpadding=2 cellspacing=0 width="100%%%%">

<tr><td  nowrap width="1%%%%" valign=top scope="row">
<font size=-1><b>%s:</b></font></td><td>
<font size=-1><label for="serve_ip"> %%(whatis_serve_ip)s </label></font>
<input type="text" value="%%(serve_ip)s" name=serve_ip size="50" id="serve_ip">
%%(basic_network_message_br)s<font size=-1>%%(example)s%%(colon)s %%(example_serve_ip)s</font>
</td></tr>
%%(whatis_tablesep)s

<tr><td nowrap width="1%%%%" valign=top scope="row">
<font size=-1><b>%s:</b></font></td><td>
<font size=-1><label for="netmask">%%(whatis_netmask)s</label></font>
<input type="text" value="%%(netmask)s" name=netmask size="50" id="netmask">
%%(basic_network_message_br)s<font size=-1>%%(example)s%%(colon)s %%(example_netmask)s</font>
</td></tr>
%%(whatis_tablesep)s
<tr><td nowrap width="1%%%%" valign=top scope="row">
<font size=-1><b>%s:</b></font></td><td>
<font size=-1><label for="gateway">%%(whatis_gateway)s </label></font>
<input type="text" value="%%(gateway)s" name=gateway size="50" id="gateway">
%%(basic_network_message_br)s<font size=-1>%%(example)s%%(colon)s %%(example_gateway)s</font>
</td></tr>

%%(whatis_tablesep)s
<tr><td nowrap width="1%%%%" valign=top scope="row">
<font size=-1><b>%s:</b></font></td><td>
<font size=-1>%%(whatis_network_speed)s
<input type="radio" name=network_speed value=0 %%(network_speed_0)s> %s<br>
<input type="radio" name=network_speed value=1 %%(network_speed_1)s> %s<br>
<input type="radio" name=network_speed value=2 %%(network_speed_2)s> %s<br>
<input type="radio" name=network_speed value=3 %%(network_speed_3)s> %s<br>
<input type="radio" name=network_speed value=4 %%(network_speed_4)s> %s<br>
<input type="radio" name=network_speed value=5 %%(network_speed_5)s> %s<br>
</font></td></tr>

%%(whatis_lastsep)s
</table>
%%(surrounding_tableend)s
""" % (webserver_base.GetMsg('IP_ADDRESS'), webserver_base.GetMsg('NETMASK'),
       webserver_base.GetMsg('GATEWAY'),
       webserver_base.GetMsg('NETWORK_SPEED'),
       webserver_base.GetMsg('NETWORK_SPEED_OPTION_0'),
       webserver_base.GetMsg('NETWORK_SPEED_OPTION_1'),
       webserver_base.GetMsg('NETWORK_SPEED_OPTION_2'),
       webserver_base.GetMsg('NETWORK_SPEED_OPTION_3'),
       webserver_base.GetMsg('NETWORK_SPEED_OPTION_4'),
       webserver_base.GetMsg('NETWORK_SPEED_OPTION_5'))

# IP setting details (for 8wyas, needs crawl IP)
# level-1 template - requires values for
# - IP
# - crawl-ip
# - netmask
# - gateway
IP_SETTINGS_8WAY = """
%%(surrounding_table)s
%%(surrounding_table1)s
<center>
<table border=0 cellpadding=2 cellspacing=0 width="100%%%%"><tr><td  width="1%%%%" valign=top>
<font size=-1>
%%(basic_network_message_br)s
</font></td></tr>
<tr><td colspan=2><hr size=1 color=3366CC></TD></TR>
</table>

<table border=0 cellpadding=2 cellspacing=0 width="100%%%%">

<tr><td  nowrap width="1%%%%" valign=top>
<font size=-1><b>%s:</b></font></td><td>
<font size=-1> %%(whatis_serve_ip)s </font>
<input type="text" value="%%(serve_ip)s" name=serve_ip size="50" id="serve_ip">

</td></tr>
%%(whatis_tablesep)s

<tr><td  nowrap width="1%%%%" valign=top>
<font size=-1><b>%s:</b></font></td><td>
<font size=-1> %%(whatis_switch_ip)s </font>
<input type="text" value="%%(switch_ip)s" name=switch_ip size="50">

</td></tr>
%%(whatis_tablesep)s

<tr><td  nowrap width="1%%%%" valign=top>
<font size=-1><b>%s:</b></font></td><td>
<font size=-1> %%(whatis_crawl_ip)s </font>
<input type="text" value="%%(crawl_ip)s" name=crawl_ip size="50">

</td></tr>
%%(whatis_tablesep)s

<tr><td nowrap width="1%%%%" valign=top>
<font size=-1><b>%s:</b></font></td><td>
<font size=-1>%%(whatis_netmask)s</font>
<input type="text" value="%%(netmask)s" name=netmask size="50">
</td></tr>
%%(whatis_tablesep)s

<tr><td nowrap width="1%%%%" valign=top>
<font size=-1><b>%s:</b></font></td><td>
<font size=-1>%%(whatis_gateway)s</font>
<input type="text" value="%%(gateway)s" name=gateway size="50">
</td></tr>
%%(whatis_tablesep)s

<tr><td nowrap width="1%%%%" valign=top>
<font size=-1><b>%s:</b></font></td><td>
<font size=-1>%%(whatis_autonegotiation)s</font>
<input type="checkbox" "%%(autonegotiation)s" name=autonegotiation>
</td></tr>
%%(whatis_lastsep)s
</table>
%%(surrounding_tableend)s
""" % ( webserver_base.GetMsg('IP_ADDRESS'),
        webserver_base.GetMsg('SWITCH_IP'),
        webserver_base.GetMsg('CRAWL_IP'),
        webserver_base.GetMsg('NETMASK'),
        webserver_base.GetMsg('GATEWAY'),
        webserver_base.GetMsg('AUTONEGOTIATION')
      )



# page for IP settings
# level 1 template - needs:
# - ID-#
# - errors (HTML TABLE)
# - IP
# - crawl-ip
# - netmask
# - gateway

IP_SETTINGS_PAGE = (PAGE_TEMPLATE_HEADER +
                    """<form method=POST action="/main_config">
                    %(Errors)s<BR>
                    <center>
                    """+
                    TAB_OBJECT % ('009900', 'ffffff',
                                  webserver_base.GetMsg('STEP_1_OF_5'),
                                  webserver_base.GetMsg('BASIC_NETWORK_SETTINGS'),
                                  'efefef', '999999',
                                  webserver_base.GetMsg('STEP_2_OF_5'),
                                  webserver_base.GetMsg('DNS_SETTINGS'),
                                  'efefef', '999999',
                                  webserver_base.GetMsg('STEP_3_OF_5'),
                                  webserver_base.GetMsg('TIME_SETTINGS'),
                                  'efefef', '999999',
                                  webserver_base.GetMsg('STEP_4_OF_5'),
                                  webserver_base.GetMsg('ADMIN_SETTINGS'),
                                  'efefef', '999999',
                                  webserver_base.GetMsg('STEP_5_OF_5'),
                                  webserver_base.GetMsg('TESTURL_SETTINGS')
                                 )  +
                    """ <p> """ +
                                                IP_SETTINGS +
                    SUBMIT_BUTTON_NEXT +
                    """
<input type=hidden value="%(switch_ip)s" name=switch_ip>
<input type=hidden value="%(crawl_ip)s" name=crawl_ip>
<input type=hidden value="%(dns_servers)s" name=dns_servers>
<input type=hidden value="%(dns_search_path)s" name=dns_search_path>
<input type=hidden value="%(autonegotiation)s" name=autonegotiation>
<input type=hidden value="%(network_speed)s" name=network_speed>
<input type=hidden value="%(ntp_servers)s" name=ntp_servers>
<input type=hidden value="%(admin_email)s" name=admin_email>
<input type=hidden value="%(timezone)s" name=timezone>
<input type=hidden value="%(smtp_servers)s" name=smtp_servers>
<input type=hidden value="%(testurls)s" name=testurls>
<input type=hidden value="%(outgoing_email_sender)s" name=outgoing_email_sender>
<input type=hidden name=step value="%(step)s">
                    """ +
                    PAGE_TEMPLATE_FOOTER)


IP_SETTINGS_PAGE_8WAY = (PAGE_TEMPLATE_HEADER +
                         """<form method=POST action="/main_config">
                         %(Errors)s<BR>
                         <center>
                         """ +
                         TAB_OBJECT % ('009900', 'ffffff',
                                       webserver_base.GetMsg('STEP_1_OF_5'),
                                       webserver_base.GetMsg('BASIC_NETWORK_SETTINGS'),
                                       'efefef', '999999',
                                       webserver_base.GetMsg('STEP_2_OF_5'),
                                       webserver_base.GetMsg('DNS_SETTINGS'),
                                       'efefef', '999999',
                                       webserver_base.GetMsg('STEP_3_OF_5'),
                                       webserver_base.GetMsg('TIME_SETTINGS'),
                                       'efefef', '999999',
                                       webserver_base.GetMsg('STEP_4_OF_5'),
                                       webserver_base.GetMsg('ADMIN_SETTINGS'),
                                       'efefef', '999999',
                                       webserver_base.GetMsg('STEP_5_OF_5'),
                                       webserver_base.GetMsg('TESTURL_SETTINGS')
                                      )  +
                         """ <p> """ +
                         IP_SETTINGS_8WAY +
                         SUBMIT_BUTTON_NEXT +
                         """
<input type=hidden value="%(dns_servers)s" name=dns_servers>
<input type=hidden value="%(dns_search_path)s" name=dns_search_path>
<input type=hidden value="%(ntp_servers)s" name=ntp_servers>
<input type=hidden value="%(admin_email)s" name=admin_email>
<input type=hidden value="%(timezone)s" name=timezone>
<input type=hidden value="%(smtp_servers)s" name=smtp_servers>
<input type=hidden value="%(testurls)s" name=testurls>
<input type=hidden value="%(outgoing_email_sender)s" name=outgoing_email_sender>
<input type=hidden name=step value="%(step)s">
                         """ +
                         PAGE_TEMPLATE_FOOTER)

# End user license agreement
# level-1 template

# page for country selection
# level 1 template
# needs
COUNTRY_SETTINGS_PAGE = (PAGE_TEMPLATE_LICENSE_HEADER +
                     """<form method=POST action="/main_config">
                     %(Errors)s<BR>""" + """
 <FONT face=arial,sans-serif size=-1>""" +
                     webserver_base.GetMsg('COUNTRY_TEMPLATE_HEADER') +
"""</FONT>%(Selector)s<FONT size=-2>
<P>

""" +

                     SUBMIT_BUTTON_NEXT +
                     """
<input type=hidden value="%(serve_ip)s" name=serve_ip>
<input type=hidden value="%(crawl_ip)s" name=crawl_ip>
<input type=hidden value="%(netmask)s" name=netmask>
<input type=hidden value="%(gateway)s" name=gateway>
<input type=hidden value="%(autonegotiation)s" name=autonegotiation>
<input type=hidden value="%(network_speed)s" name=network_speed>
<input type=hidden value="%(ntp_servers)s" name=ntp_servers>
<input type=hidden value="%(admin_email)s" name=admin_email>
<input type=hidden value="%(timezone)s" name=timezone>
<input type=hidden value="%(testurls)s" name=testurls>
<input type=hidden name=step value="%(step)s">
                     %(Diags)s<br>
                     """ +
                     PAGE_TEMPLATE_FOOTER)

# page for license settings
# level 1 template
# needs
LICENSE_SETTINGS_PAGE = (PAGE_TEMPLATE_LICENSE_HEADER +
                     """<form method=POST action="/main_config">
                     %(Errors)s<BR>""" + """
<table width=90%% align=center cellpadding=0><tr><td>

 <FONT face=arial,sans-serif size=-1>""" +
                     webserver_base.GetMsg('LICENSE_TEMPLATE_HEADER') +
"""</FONT></td><td></td></tr></table> <FONT size=-2>
<P>
<iframe src="%(License)s" width=100%% height=50%%></iframe>
<font size="-1"><a href="%(License)s" target="_blank">""" +
                     webserver_base.GetMsg('OPEN_LICENSE') +
"""</a></font>""" +
                     SUBMIT_BUTTON_ACCEPT_REJECT +
                     """
<input type=hidden value="%(serve_ip)s" name=serve_ip>
<input type=hidden value="%(crawl_ip)s" name=crawl_ip>
<input type=hidden value="%(netmask)s" name=netmask>
<input type=hidden value="%(gateway)s" name=gateway>
<input type=hidden value="%(autonegotiation)s" name=autonegotiation>
<input type=hidden value="%(network_speed)s" name=network_speed>
<input type=hidden value="%(ntp_servers)s" name=ntp_servers>
<input type=hidden value="%(admin_email)s" name=admin_email>
<input type=hidden value="%(timezone)s" name=timezone>
<input type=hidden value="%(testurls)s" name=testurls>
<input type=hidden name=step value="%(step)s">
                     %(Diags)s<br>
                     """ +
                     PAGE_TEMPLATE_FOOTER)

# DNS setting details
# level-1 template - requires values for
# - DNS-servers
# - DNS search path
DNS_SETTINGS = """
%%(surrounding_table)s
%%(surrounding_table1)s
<center>

<table border=0 cellpadding=2 cellspacing=0 width="100%%%%">
%%(header_seperator)s
<tr><td  nowrap width="1%%%%" valign=top>
<font size=-1><b>%s:</b></font></td><td>
<font size=-1> %%(whatis_dns)s</font>
<input type="text" value="%%(dns_servers)s" name=dns_servers size="50">
%%(basic_network_message_br)s<font size=-1>%%(separate_commas)s</font>
%%(basic_network_message_br)s<font size=-1>%%(example)s%%(colon)s %%(example_dns)s</font>
</td></tr>
%%(whatis_tablesep)s
<tr><td nowrap width="1%%%%" valign=top>
<font size=-1><b>%s:</b></font></td><td>
<font size=-1>%%(whatis_dns_path)s</font>
<input type="text" value="%%(dns_search_path)s" name=dns_search_path size="50">
%%(basic_network_message_br)s<font size=-1>%%(example)s%%(colon)s %%(example_dns_path)s</font>
</td></tr>
%%(whatis_tablesep)s
%%(smtp_sep)s
<tr><td nowrap width="1%%%%" valign=top>
<font size=-1><b>%s:</b></font></td><td>
<font size=-1>%%(whatis_smtp)s</font>
<input type="text" value="%%(smtp_servers)s" name=smtp_servers size="50">
</td></tr>
%%(whatis_tablesep)s
<tr><td  nowrap width="1%%%%">
<font size=-1><b>%s:</b></font></td><td>
<font size=-1>%%(whatis_outgoing_email_sender)s</font>
<input type="text" value="%%(outgoing_email_sender)s" name=outgoing_email_sender size="50">
</td></tr>
%%(whatis_lastsep)s
</table>
%%(surrounding_tableend)s
""" % ( webserver_base.GetMsg('DNS_SERVERS'),
                          webserver_base.GetMsg('DNS_SEARCH_PATH'),
                          webserver_base.GetMsg('SMTP_SERVER'),
                          webserver_base.GetMsg('OUTGOING_EMAIL_SENDER'))

# page for DNS settings
# level 1 template
# needs
# ID-#
# - errors (HTML TABLE)
# - diagnostics (HTML TABLE)
# - DNS-servers
# - DNS search path
DNS_SETTINGS_PAGE = (PAGE_TEMPLATE_HEADER +
                     """<form method=POST action="/main_config">
                     %(Errors)s<BR>
                     """ +
                     TAB_OBJECT % ('99cc99', 'ffffff',
                                   webserver_base.GetMsg('STEP_1_OF_5'),
                                   webserver_base.GetMsg('BASIC_NETWORK_SETTINGS'),
                                   '009900', 'ffffff',
                                   webserver_base.GetMsg('STEP_2_OF_5'),
                                   webserver_base.GetMsg('DNS_SETTINGS'),
                                   'efefef', '999999',
                                   webserver_base.GetMsg('STEP_3_OF_5'),
                                   webserver_base.GetMsg('TIME_SETTINGS'),
                                   'efefef', '999999',
                                   webserver_base.GetMsg('STEP_4_OF_5'),
                                   webserver_base.GetMsg('ADMIN_SETTINGS'),
                                   'efefef', '999999',
                                   webserver_base.GetMsg('STEP_5_OF_5'),
                                   webserver_base.GetMsg('TESTURL_SETTINGS'),
                                  )  +
                     """ <p> """ +
                     DNS_SETTINGS +
                     SUBMIT_BUTTON_BACK_NEXT +
                     """
<input type=hidden value="%(serve_ip)s" name=serve_ip>
<input type=hidden value="%(switch_ip)s" name=switch_ip>
<input type=hidden value="%(crawl_ip)s" name=crawl_ip>
<input type=hidden value="%(netmask)s" name=netmask>
<input type=hidden value="%(gateway)s" name=gateway>
<input type=hidden value="%(autonegotiation)s" name=autonegotiation>
<input type=hidden value="%(network_speed)s" name=network_speed>
<input type=hidden value="%(ntp_servers)s" name=ntp_servers>
<input type=hidden value="%(admin_email)s" name=admin_email>
<input type=hidden value="%(timezone)s" name=timezone>
<input type=hidden value="%(testurls)s" name=testurls>
<input type=hidden name=step value="%(step)s">
                     %(Diags)s<br>
                     """ +
                     PAGE_TEMPLATE_FOOTER)

# build a menu of timezones
TIMEZONE_START = "<select name=timezone>"
TIMEZONE_ITEM = "<option %s value=%s> %s"
TIMEZONE_END = "</select>"


# TODO: we need to find a way to allow selection from maybe hundreds
# of timezones in a nice way. This list is only a small set of timezones
# that will have entries close to most customers.
# Note: We need to pick names that are also available in Java (oh Joy!)
# Use java.util.TimeZone.getAvailableIDs() to find out which ones
# you can use.
TIMEZONES = (
  # unix timezone name, interface name

  ("Africa/Abidjan", "Africa/Abidjan"),
  ("Africa/Accra", "Africa/Accra"),
  ("Africa/Addis_Ababa", "Africa/Addis_Ababa"),
  ("Africa/Algiers", "Africa/Algiers"),
  ("Africa/Asmera", "Africa/Asmera"),
  ("Africa/Bamako", "Africa/Bamako"),
  ("Africa/Bangui", "Africa/Bangui"),
  ("Africa/Banjul", "Africa/Banjul"),
  ("Africa/Bissau", "Africa/Bissau"),
  ("Africa/Blantyre", "Africa/Blantyre"),
  ("Africa/Brazzaville", "Africa/Brazzaville"),
  ("Africa/Bujumbura", "Africa/Bujumbura"),
  ("Africa/Cairo", "Africa/Cairo"),
  ("Africa/Casablanca", "Africa/Casablanca"),
  ("Africa/Ceuta", "Africa/Ceuta"),
  ("Africa/Conakry", "Africa/Conakry"),
  ("Africa/Dakar", "Africa/Dakar"),
  ("Africa/Dar_es_Salaam", "Africa/Dar_es_Salaam"),
  ("Africa/Djibouti", "Africa/Djibouti"),
  ("Africa/Douala", "Africa/Douala"),
  ("Africa/El_Aaiun", "Africa/El_Aaiun"),
  ("Africa/Freetown", "Africa/Freetown"),
  ("Africa/Gaborone", "Africa/Gaborone"),
  ("Africa/Harare", "Africa/Harare"),
  ("Africa/Johannesburg", "Africa/Johannesburg"),
  ("Africa/Kampala", "Africa/Kampala"),
  ("Africa/Khartoum", "Africa/Khartoum"),
  ("Africa/Kigali", "Africa/Kigali"),
  ("Africa/Kinshasa", "Africa/Kinshasa"),
  ("Africa/Lagos", "Africa/Lagos"),
  ("Africa/Libreville", "Africa/Libreville"),
  ("Africa/Lome", "Africa/Lome"),
  ("Africa/Luanda", "Africa/Luanda"),
  ("Africa/Lubumbashi", "Africa/Lubumbashi"),
  ("Africa/Lusaka", "Africa/Lusaka"),
  ("Africa/Malabo", "Africa/Malabo"),
  ("Africa/Maputo", "Africa/Maputo"),
  ("Africa/Maseru", "Africa/Maseru"),
  ("Africa/Mbabane", "Africa/Mbabane"),
  ("Africa/Mogadishu", "Africa/Mogadishu"),
  ("Africa/Monrovia", "Africa/Monrovia"),
  ("Africa/Nairobi", "Africa/Nairobi"),
  ("Africa/Ndjamena", "Africa/Ndjamena"),
  ("Africa/Niamey", "Africa/Niamey"),
  ("Africa/Nouakchott", "Africa/Nouakchott"),
  ("Africa/Ouagadougou", "Africa/Ouagadougou"),
  ("Africa/Porto-Novo", "Africa/Porto-Novo"),
  ("Africa/Sao_Tome", "Africa/Sao_Tome"),
  ("Africa/Timbuktu", "Africa/Timbuktu"),
  ("Africa/Tripoli", "Africa/Tripoli"),
  ("Africa/Tunis", "Africa/Tunis"),
  ("Africa/Windhoek", "Africa/Windhoek"),
  ("America/Adak", "America/Adak"),
  ("America/Anchorage", "America/Anchorage"),
  ("America/Anguilla", "America/Anguilla"),
  ("America/Antigua", "America/Antigua"),
  ("America/Araguaina", "America/Araguaina"),
  ("America/Aruba", "America/Aruba"),
  ("America/Asuncion", "America/Asuncion"),
  ("America/Atka", "America/Atka"),
  ("America/Barbados", "America/Barbados"),
  ("America/Belem", "America/Belem"),
  ("America/Belize", "America/Belize"),
  ("America/Boa_Vista", "America/Boa_Vista"),
  ("America/Bogota", "America/Bogota"),
  ("America/Boise", "America/Boise"),
  ("America/Buenos_Aires", "America/Buenos_Aires"),
  ("America/Cambridge_Bay", "America/Cambridge_Bay"),
  ("America/Cancun", "America/Cancun"),
  ("America/Caracas", "America/Caracas"),
  ("America/Catamarca", "America/Catamarca"),
  ("America/Cayenne", "America/Cayenne"),
  ("America/Cayman", "America/Cayman"),
  ("America/Chicago", "America/Chicago"),
  ("America/Chihuahua", "America/Chihuahua"),
  ("America/Cordoba", "America/Cordoba"),
  ("America/Costa_Rica", "America/Costa_Rica"),
  ("America/Cuiaba", "America/Cuiaba"),
  ("America/Curacao", "America/Curacao"),
  ("America/Danmarkshavn", "America/Danmarkshavn"),
  ("America/Dawson", "America/Dawson"),
  ("America/Dawson_Creek", "America/Dawson_Creek"),
  ("America/Denver", "America/Denver"),
  ("America/Detroit", "America/Detroit"),
  ("America/Dominica", "America/Dominica"),
  ("America/Edmonton", "America/Edmonton"),
  ("America/Eirunepe", "America/Eirunepe"),
  ("America/El_Salvador", "America/El_Salvador"),
  ("America/Ensenada", "America/Ensenada"),
  ("America/Fortaleza", "America/Fortaleza"),
  ("America/Fort_Wayne", "America/Fort_Wayne"),
  ("America/Glace_Bay", "America/Glace_Bay"),
  ("America/Godthab", "America/Godthab"),
  ("America/Goose_Bay", "America/Goose_Bay"),
  ("America/Grand_Turk", "America/Grand_Turk"),
  ("America/Grenada", "America/Grenada"),
  ("America/Guadeloupe", "America/Guadeloupe"),
  ("America/Guatemala", "America/Guatemala"),
  ("America/Guayaquil", "America/Guayaquil"),
  ("America/Guyana", "America/Guyana"),
  ("America/Halifax", "America/Halifax"),
  ("America/Havana", "America/Havana"),
  ("America/Hermosillo", "America/Hermosillo"),
  ("America/Indiana/Indianapolis", "America/Indiana/Indianapolis"),
  ("America/Indiana/Knox", "America/Indiana/Knox"),
  ("America/Indiana/Marengo", "America/Indiana/Marengo"),
  ("America/Indianapolis", "America/Indianapolis"),
  ("America/Indiana/Vevay", "America/Indiana/Vevay"),
  ("America/Inuvik", "America/Inuvik"),
  ("America/Iqaluit", "America/Iqaluit"),
  ("America/Jamaica", "America/Jamaica"),
  ("America/Jujuy", "America/Jujuy"),
  ("America/Juneau", "America/Juneau"),
  ("America/Kentucky/Louisville", "America/Kentucky/Louisville"),
  ("America/Kentucky/Monticello", "America/Kentucky/Monticello"),
  ("America/Knox_IN", "America/Knox_IN"),
  ("America/La_Paz", "America/La_Paz"),
  ("America/Lima", "America/Lima"),
  ("America/Los_Angeles", "America/Los_Angeles"),
  ("America/Louisville", "America/Louisville"),
  ("America/Maceio", "America/Maceio"),
  ("America/Managua", "America/Managua"),
  ("America/Manaus", "America/Manaus"),
  ("America/Martinique", "America/Martinique"),
  ("America/Mazatlan", "America/Mazatlan"),
  ("America/Mendoza", "America/Mendoza"),
  ("America/Menominee", "America/Menominee"),
  ("America/Merida", "America/Merida"),
  ("America/Mexico_City", "America/Mexico_City"),
  ("America/Miquelon", "America/Miquelon"),
  ("America/Monterrey", "America/Monterrey"),
  ("America/Montevideo", "America/Montevideo"),
  ("America/Montreal", "America/Montreal"),
  ("America/Montserrat", "America/Montserrat"),
  ("America/Nassau", "America/Nassau"),
  ("America/New_York", "America/New_York"),
  ("America/Nipigon", "America/Nipigon"),
  ("America/Nome", "America/Nome"),
  ("America/Noronha", "America/Noronha"),
  ("America/North_Dakota/Center", "America/North_Dakota/Center"),
  ("America/Panama", "America/Panama"),
  ("America/Pangnirtung", "America/Pangnirtung"),
  ("America/Paramaribo", "America/Paramaribo"),
  ("America/Phoenix", "America/Phoenix"),
  ("America/Port-au-Prince", "America/Port-au-Prince"),
  ("America/Porto_Acre", "America/Porto_Acre"),
  ("America/Port_of_Spain", "America/Port_of_Spain"),
  ("America/Porto_Velho", "America/Porto_Velho"),
  ("America/Puerto_Rico", "America/Puerto_Rico"),
  ("America/Rainy_River", "America/Rainy_River"),
  ("America/Rankin_Inlet", "America/Rankin_Inlet"),
  ("America/Recife", "America/Recife"),
  ("America/Regina", "America/Regina"),
  ("America/Rio_Branco", "America/Rio_Branco"),
  ("America/Rosario", "America/Rosario"),
  ("America/Santiago", "America/Santiago"),
  ("America/Santo_Domingo", "America/Santo_Domingo"),
  ("America/Sao_Paulo", "America/Sao_Paulo"),
  ("America/Scoresbysund", "America/Scoresbysund"),
  ("America/Shiprock", "America/Shiprock"),
  ("America/St_Johns", "America/St_Johns"),
  ("America/St_Kitts", "America/St_Kitts"),
  ("America/St_Lucia", "America/St_Lucia"),
  ("America/St_Thomas", "America/St_Thomas"),
  ("America/St_Vincent", "America/St_Vincent"),
  ("America/Swift_Current", "America/Swift_Current"),
  ("America/Tegucigalpa", "America/Tegucigalpa"),
  ("America/Thule", "America/Thule"),
  ("America/Thunder_Bay", "America/Thunder_Bay"),
  ("America/Tijuana", "America/Tijuana"),
  ("America/Tortola", "America/Tortola"),
  ("America/Vancouver", "America/Vancouver"),
  ("America/Virgin", "America/Virgin"),
  ("America/Whitehorse", "America/Whitehorse"),
  ("America/Winnipeg", "America/Winnipeg"),
  ("America/Yakutat", "America/Yakutat"),
  ("America/Yellowknife", "America/Yellowknife"),
  ("Antarctica/Casey", "Antarctica/Casey"),
  ("Antarctica/Davis", "Antarctica/Davis"),
  ("Antarctica/DumontDUrville", "Antarctica/DumontDUrville"),
  ("Antarctica/Mawson", "Antarctica/Mawson"),
  ("Antarctica/McMurdo", "Antarctica/McMurdo"),
  ("Antarctica/Palmer", "Antarctica/Palmer"),
  ("Antarctica/Rothera", "Antarctica/Rothera"),
  ("Antarctica/South_Pole", "Antarctica/South_Pole"),
  ("Antarctica/Syowa", "Antarctica/Syowa"),
  ("Antarctica/Vostok", "Antarctica/Vostok"),
  ("Arctic/Longyearbyen", "Arctic/Longyearbyen"),
  ("Asia/Aden", "Asia/Aden"),
  ("Asia/Almaty", "Asia/Almaty"),
  ("Asia/Amman", "Asia/Amman"),
  ("Asia/Anadyr", "Asia/Anadyr"),
  ("Asia/Aqtau", "Asia/Aqtau"),
  ("Asia/Aqtobe", "Asia/Aqtobe"),
  ("Asia/Ashgabat", "Asia/Ashgabat"),
  ("Asia/Ashkhabad", "Asia/Ashkhabad"),
  ("Asia/Baghdad", "Asia/Baghdad"),
  ("Asia/Bahrain", "Asia/Bahrain"),
  ("Asia/Baku", "Asia/Baku"),
  ("Asia/Bangkok", "Asia/Bangkok"),
  ("Asia/Beirut", "Asia/Beirut"),
  ("Asia/Bishkek", "Asia/Bishkek"),
  ("Asia/Brunei", "Asia/Brunei"),
  ("Asia/Calcutta", "Asia/Calcutta"),
  ("Asia/Choibalsan", "Asia/Choibalsan"),
  ("Asia/Chongqing", "Asia/Chongqing"),
  ("Asia/Chungking", "Asia/Chungking"),
  ("Asia/Colombo", "Asia/Colombo"),
  ("Asia/Dacca", "Asia/Dacca"),
  ("Asia/Damascus", "Asia/Damascus"),
  ("Asia/Dhaka", "Asia/Dhaka"),
  ("Asia/Dili", "Asia/Dili"),
  ("Asia/Dubai", "Asia/Dubai"),
  ("Asia/Dushanbe", "Asia/Dushanbe"),
  ("Asia/Gaza", "Asia/Gaza"),
  ("Asia/Harbin", "Asia/Harbin"),
  ("Asia/Hong_Kong", "Asia/Hong_Kong"),
  ("Asia/Hovd", "Asia/Hovd"),
  ("Asia/Irkutsk", "Asia/Irkutsk"),
  ("Asia/Istanbul", "Asia/Istanbul"),
  ("Asia/Jakarta", "Asia/Jakarta"),
  ("Asia/Jayapura", "Asia/Jayapura"),
  ("Asia/Jerusalem", "Asia/Jerusalem"),
  ("Asia/Kabul", "Asia/Kabul"),
  ("Asia/Kamchatka", "Asia/Kamchatka"),
  ("Asia/Karachi", "Asia/Karachi"),
  ("Asia/Kashgar", "Asia/Kashgar"),
  ("Asia/Katmandu", "Asia/Katmandu"),
  ("Asia/Krasnoyarsk", "Asia/Krasnoyarsk"),
  ("Asia/Kuala_Lumpur", "Asia/Kuala_Lumpur"),
  ("Asia/Kuching", "Asia/Kuching"),
  ("Asia/Kuwait", "Asia/Kuwait"),
  ("Asia/Macao", "Asia/Macao"),
  ("Asia/Macau", "Asia/Macau"),
  ("Asia/Magadan", "Asia/Magadan"),
  ("Asia/Makassar", "Asia/Makassar"),
  ("Asia/Manila", "Asia/Manila"),
  ("Asia/Muscat", "Asia/Muscat"),
  ("Asia/Nicosia", "Asia/Nicosia"),
  ("Asia/Novosibirsk", "Asia/Novosibirsk"),
  ("Asia/Omsk", "Asia/Omsk"),
  ("Asia/Oral", "Asia/Oral"),
  ("Asia/Phnom_Penh", "Asia/Phnom_Penh"),
  ("Asia/Pontianak", "Asia/Pontianak"),
  ("Asia/Pyongyang", "Asia/Pyongyang"),
  ("Asia/Qatar", "Asia/Qatar"),
  ("Asia/Qyzylorda", "Asia/Qyzylorda"),
  ("Asia/Rangoon", "Asia/Rangoon"),
  ("Asia/Riyadh", "Asia/Riyadh"),
  ("Asia/Riyadh87", "Asia/Riyadh87"),
  ("Asia/Riyadh88", "Asia/Riyadh88"),
  ("Asia/Riyadh89", "Asia/Riyadh89"),
  ("Asia/Saigon", "Asia/Saigon"),
  ("Asia/Sakhalin", "Asia/Sakhalin"),
  ("Asia/Samarkand", "Asia/Samarkand"),
  ("Asia/Seoul", "Asia/Seoul"),
  ("Asia/Shanghai", "Asia/Shanghai"),
  ("Asia/Singapore", "Asia/Singapore"),
  ("Asia/Taipei", "Asia/Taipei"),
  ("Asia/Tashkent", "Asia/Tashkent"),
  ("Asia/Tbilisi", "Asia/Tbilisi"),
  ("Asia/Tehran", "Asia/Tehran"),
  ("Asia/Tel_Aviv", "Asia/Tel_Aviv"),
  ("Asia/Thimbu", "Asia/Thimbu"),
  ("Asia/Thimphu", "Asia/Thimphu"),
  ("Asia/Tokyo", "Asia/Tokyo"),
  ("Asia/Ujung_Pandang", "Asia/Ujung_Pandang"),
  ("Asia/Ulaanbaatar", "Asia/Ulaanbaatar"),
  ("Asia/Ulan_Bator", "Asia/Ulan_Bator"),
  ("Asia/Urumqi", "Asia/Urumqi"),
  ("Asia/Vientiane", "Asia/Vientiane"),
  ("Asia/Vladivostok", "Asia/Vladivostok"),
  ("Asia/Yakutsk", "Asia/Yakutsk"),
  ("Asia/Yekaterinburg", "Asia/Yekaterinburg"),
  ("Asia/Yerevan", "Asia/Yerevan"),
  ("Atlantic/Azores", "Atlantic/Azores"),
  ("Atlantic/Bermuda", "Atlantic/Bermuda"),
  ("Atlantic/Canary", "Atlantic/Canary"),
  ("Atlantic/Cape_Verde", "Atlantic/Cape_Verde"),
  ("Atlantic/Faeroe", "Atlantic/Faeroe"),
  ("Atlantic/Jan_Mayen", "Atlantic/Jan_Mayen"),
  ("Atlantic/Madeira", "Atlantic/Madeira"),
  ("Atlantic/Reykjavik", "Atlantic/Reykjavik"),
  ("Atlantic/South_Georgia", "Atlantic/South_Georgia"),
  ("Atlantic/Stanley", "Atlantic/Stanley"),
  ("Atlantic/St_Helena", "Atlantic/St_Helena"),
  ("Australia/ACT", "Australia/ACT"),
  ("Australia/Adelaide", "Australia/Adelaide"),
  ("Australia/Brisbane", "Australia/Brisbane"),
  ("Australia/Broken_Hill", "Australia/Broken_Hill"),
  ("Australia/Canberra", "Australia/Canberra"),
  ("Australia/Darwin", "Australia/Darwin"),
  ("Australia/Hobart", "Australia/Hobart"),
  ("Australia/LHI", "Australia/LHI"),
  ("Australia/Lindeman", "Australia/Lindeman"),
  ("Australia/Lord_Howe", "Australia/Lord_Howe"),
  ("Australia/Melbourne", "Australia/Melbourne"),
  ("Australia/North", "Australia/North"),
  ("Australia/NSW", "Australia/NSW"),
  ("Australia/Perth", "Australia/Perth"),
  ("Australia/Queensland", "Australia/Queensland"),
  ("Australia/South", "Australia/South"),
  ("Australia/Sydney", "Australia/Sydney"),
  ("Australia/Tasmania", "Australia/Tasmania"),
  ("Australia/Victoria", "Australia/Victoria"),
  ("Australia/West", "Australia/West"),
  ("Australia/Yancowinna", "Australia/Yancowinna"),
  ("Brazil/Acre", "Brazil/Acre"),
  ("Brazil/DeNoronha", "Brazil/DeNoronha"),
  ("Brazil/East", "Brazil/East"),
  ("Brazil/West", "Brazil/West"),
  ("Canada/Atlantic", "Canada/Atlantic"),
  ("Canada/Central", "Canada/Central"),
  ("Canada/Eastern", "Canada/Eastern"),
  ("Canada/East-Saskatchewan", "Canada/East-Saskatchewan"),
  ("Canada/Mountain", "Canada/Mountain"),
  ("Canada/Newfoundland", "Canada/Newfoundland"),
  ("Canada/Pacific", "Canada/Pacific"),
  ("Canada/Saskatchewan", "Canada/Saskatchewan"),
  ("Canada/Yukon", "Canada/Yukon"),
  ("CET", "CET"),
  ("Chile/Continental", "Chile/Continental"),
  ("Chile/EasterIsland", "Chile/EasterIsland"),
  ("CST6CDT", "CST6CDT"),
  ("Cuba", "Cuba"),
  ("EET", "EET"),
  ("Egypt", "Egypt"),
  ("Eire", "Eire"),
  ("EST", "EST"),
  ("EST5EDT", "EST5EDT"),
  ("Etc/GMT", "Etc/GMT"),
  ("Etc/GMT+1", "Etc/GMT+1"),
  ("Etc/GMT-1", "Etc/GMT-1"),
  ("Etc/GMT+10", "Etc/GMT+10"),
  ("Etc/GMT-10", "Etc/GMT-10"),
  ("Etc/GMT+11", "Etc/GMT+11"),
  ("Etc/GMT-11", "Etc/GMT-11"),
  ("Etc/GMT+12", "Etc/GMT+12"),
  ("Etc/GMT-12", "Etc/GMT-12"),
  ("Etc/GMT+13", "Etc/GMT+13"),
  ("Etc/GMT+14", "Etc/GMT+14"),
  ("Etc/GMT+2", "Etc/GMT+2"),
  ("Etc/GMT-2", "Etc/GMT-2"),
  ("Etc/GMT+3", "Etc/GMT+3"),
  ("Etc/GMT-3", "Etc/GMT-3"),
  ("Etc/GMT+4", "Etc/GMT+4"),
  ("Etc/GMT-4", "Etc/GMT-4"),
  ("Etc/GMT+5", "Etc/GMT+5"),
  ("Etc/GMT-5", "Etc/GMT-5"),
  ("Etc/GMT+6", "Etc/GMT+6"),
  ("Etc/GMT-6", "Etc/GMT-6"),
  ("Etc/GMT+7", "Etc/GMT+7"),
  ("Etc/GMT-7", "Etc/GMT-7"),
  ("Etc/GMT+8", "Etc/GMT+8"),
  ("Etc/GMT-8", "Etc/GMT-8"),
  ("Etc/GMT+9", "Etc/GMT+9"),
  ("Etc/GMT-9", "Etc/GMT-9"),
  ("Etc/Greenwich", "Etc/Greenwich"),
  ("Etc/UCT", "Etc/UCT"),
  ("Etc/Universal", "Etc/Universal"),
  ("Etc/UTC", "Etc/UTC"),
  ("Etc/Zulu", "Etc/Zulu"),
  ("Europe/Amsterdam", "Europe/Amsterdam"),
  ("Europe/Andorra", "Europe/Andorra"),
  ("Europe/Athens", "Europe/Athens"),
  ("Europe/Belfast", "Europe/Belfast"),
  ("Europe/Belgrade", "Europe/Belgrade"),
  ("Europe/Berlin", "Europe/Berlin"),
  ("Europe/Bratislava", "Europe/Bratislava"),
  ("Europe/Brussels", "Europe/Brussels"),
  ("Europe/Bucharest", "Europe/Bucharest"),
  ("Europe/Budapest", "Europe/Budapest"),
  ("Europe/Chisinau", "Europe/Chisinau"),
  ("Europe/Copenhagen", "Europe/Copenhagen"),
  ("Europe/Dublin", "Europe/Dublin"),
  ("Europe/Gibraltar", "Europe/Gibraltar"),
  ("Europe/Helsinki", "Europe/Helsinki"),
  ("Europe/Istanbul", "Europe/Istanbul"),
  ("Europe/Kaliningrad", "Europe/Kaliningrad"),
  ("Europe/Kiev", "Europe/Kiev"),
  ("Europe/Lisbon", "Europe/Lisbon"),
  ("Europe/Ljubljana", "Europe/Ljubljana"),
  ("Europe/London", "Europe/London"),
  ("Europe/Luxembourg", "Europe/Luxembourg"),
  ("Europe/Madrid", "Europe/Madrid"),
  ("Europe/Malta", "Europe/Malta"),
  ("Europe/Minsk", "Europe/Minsk"),
  ("Europe/Monaco", "Europe/Monaco"),
  ("Europe/Moscow", "Europe/Moscow"),
  ("Europe/Nicosia", "Europe/Nicosia"),
  ("Europe/Oslo", "Europe/Oslo"),
  ("Europe/Paris", "Europe/Paris"),
  ("Europe/Prague", "Europe/Prague"),
  ("Europe/Riga", "Europe/Riga"),
  ("Europe/Rome", "Europe/Rome"),
  ("Europe/Samara", "Europe/Samara"),
  ("Europe/San_Marino", "Europe/San_Marino"),
  ("Europe/Sarajevo", "Europe/Sarajevo"),
  ("Europe/Simferopol", "Europe/Simferopol"),
  ("Europe/Skopje", "Europe/Skopje"),
  ("Europe/Sofia", "Europe/Sofia"),
  ("Europe/Stockholm", "Europe/Stockholm"),
  ("Europe/Tallinn", "Europe/Tallinn"),
  ("Europe/Tirane", "Europe/Tirane"),
  ("Europe/Tiraspol", "Europe/Tiraspol"),
  ("Europe/Uzhgorod", "Europe/Uzhgorod"),
  ("Europe/Vaduz", "Europe/Vaduz"),
  ("Europe/Vatican", "Europe/Vatican"),
  ("Europe/Vienna", "Europe/Vienna"),
  ("Europe/Vilnius", "Europe/Vilnius"),
  ("Europe/Warsaw", "Europe/Warsaw"),
  ("Europe/Zagreb", "Europe/Zagreb"),
  ("Europe/Zaporozhye", "Europe/Zaporozhye"),
  ("Europe/Zurich", "Europe/Zurich"),
  ("GB", "GB"),
  ("GB-Eire", "GB-Eire"),
  ("GMT", "GMT"),
  ("Greenwich", "Greenwich"),
  ("Hongkong", "Hongkong"),
  ("HST", "HST"),
  ("Iceland", "Iceland"),
  ("Indian/Antananarivo", "Indian/Antananarivo"),
  ("Indian/Chagos", "Indian/Chagos"),
  ("Indian/Christmas", "Indian/Christmas"),
  ("Indian/Cocos", "Indian/Cocos"),
  ("Indian/Comoro", "Indian/Comoro"),
  ("Indian/Kerguelen", "Indian/Kerguelen"),
  ("Indian/Mahe", "Indian/Mahe"),
  ("Indian/Maldives", "Indian/Maldives"),
  ("Indian/Mauritius", "Indian/Mauritius"),
  ("Indian/Mayotte", "Indian/Mayotte"),
  ("Indian/Reunion", "Indian/Reunion"),
  ("Iran", "Iran"),
  ("Israel", "Israel"),
  ("Jamaica", "Jamaica"),
  ("Japan", "Japan"),
  ("Kwajalein", "Kwajalein"),
  ("Libya", "Libya"),
  ("MET", "MET"),
  ("Mexico/BajaNorte", "Mexico/BajaNorte"),
  ("Mexico/BajaSur", "Mexico/BajaSur"),
  ("Mexico/General", "Mexico/General"),
  ("Mideast/Riyadh87", "Mideast/Riyadh87"),
  ("Mideast/Riyadh88", "Mideast/Riyadh88"),
  ("Mideast/Riyadh89", "Mideast/Riyadh89"),
  ("MST", "MST"),
  ("MST7MDT", "MST7MDT"),
  ("Navajo", "Navajo"),
  ("NZ", "NZ"),
  ("NZ-CHAT", "NZ-CHAT"),
  ("Pacific/Apia", "Pacific/Apia"),
  ("Pacific/Auckland", "Pacific/Auckland"),
  ("Pacific/Chatham", "Pacific/Chatham"),
  ("Pacific/Easter", "Pacific/Easter"),
  ("Pacific/Efate", "Pacific/Efate"),
  ("Pacific/Enderbury", "Pacific/Enderbury"),
  ("Pacific/Fakaofo", "Pacific/Fakaofo"),
  ("Pacific/Fiji", "Pacific/Fiji"),
  ("Pacific/Funafuti", "Pacific/Funafuti"),
  ("Pacific/Galapagos", "Pacific/Galapagos"),
  ("Pacific/Gambier", "Pacific/Gambier"),
  ("Pacific/Guadalcanal", "Pacific/Guadalcanal"),
  ("Pacific/Guam", "Pacific/Guam"),
  ("Pacific/Honolulu", "Pacific/Honolulu"),
  ("Pacific/Johnston", "Pacific/Johnston"),
  ("Pacific/Kiritimati", "Pacific/Kiritimati"),
  ("Pacific/Kosrae", "Pacific/Kosrae"),
  ("Pacific/Kwajalein", "Pacific/Kwajalein"),
  ("Pacific/Majuro", "Pacific/Majuro"),
  ("Pacific/Marquesas", "Pacific/Marquesas"),
  ("Pacific/Midway", "Pacific/Midway"),
  ("Pacific/Nauru", "Pacific/Nauru"),
  ("Pacific/Niue", "Pacific/Niue"),
  ("Pacific/Norfolk", "Pacific/Norfolk"),
  ("Pacific/Noumea", "Pacific/Noumea"),
  ("Pacific/Pago_Pago", "Pacific/Pago_Pago"),
  ("Pacific/Palau", "Pacific/Palau"),
  ("Pacific/Pitcairn", "Pacific/Pitcairn"),
  ("Pacific/Ponape", "Pacific/Ponape"),
  ("Pacific/Port_Moresby", "Pacific/Port_Moresby"),
  ("Pacific/Rarotonga", "Pacific/Rarotonga"),
  ("Pacific/Saipan", "Pacific/Saipan"),
  ("Pacific/Samoa", "Pacific/Samoa"),
  ("Pacific/Tahiti", "Pacific/Tahiti"),
  ("Pacific/Tarawa", "Pacific/Tarawa"),
  ("Pacific/Tongatapu", "Pacific/Tongatapu"),
  ("Pacific/Truk", "Pacific/Truk"),
  ("Pacific/Wake", "Pacific/Wake"),
  ("Pacific/Wallis", "Pacific/Wallis"),
  ("Pacific/Yap", "Pacific/Yap"),
  ("Poland", "Poland"),
  ("Portugal", "Portugal"),
  ("PRC", "PRC"),
  ("PST8PDT", "PST8PDT"),
  ("ROC", "ROC"),
  ("ROK", "ROK"),
  ("Singapore", "Singapore"),
  ("SystemV/AST4", "SystemV/AST4"),
  ("SystemV/AST4ADT", "SystemV/AST4ADT"),
  ("SystemV/CST6", "SystemV/CST6"),
  ("SystemV/CST6CDT", "SystemV/CST6CDT"),
  ("SystemV/EST5", "SystemV/EST5"),
  ("SystemV/EST5EDT", "SystemV/EST5EDT"),
  ("SystemV/HST10", "SystemV/HST10"),
  ("SystemV/MST7", "SystemV/MST7"),
  ("SystemV/MST7MDT", "SystemV/MST7MDT"),
  ("SystemV/PST8", "SystemV/PST8"),
  ("SystemV/PST8PDT", "SystemV/PST8PDT"),
  ("SystemV/YST9", "SystemV/YST9"),
  ("SystemV/YST9YDT", "SystemV/YST9YDT"),
  ("Turkey", "Turkey"),
  ("UCT", "UCT"),
  ("Universal", "Universal"),
  ("US/Alaska", "US/Alaska"),
  ("US/Aleutian", "US/Aleutian"),
  ("US/Arizona", "US/Arizona"),
  ("US/Central", "US/Central"),
  ("US/Eastern", "US/Eastern"),
  ("US/East-Indiana", "US/East-Indiana"),
  ("US/Hawaii", "US/Hawaii"),
  ("US/Indiana-Starke", "US/Indiana-Starke"),
  ("US/Michigan", "US/Michigan"),
  ("US/Mountain", "US/Mountain"),
  ("US/Pacific", "US/Pacific"),
  ("US/Samoa", "US/Samoa"),
  ("UTC", "UTC"),
  ("WET", "WET"),
  ("W-SU", "W-SU"),
  ("Zulu", "Zulu"),
  )

TIMEZONE_ERROR = """'%%s' %s""" \
% webserver_base.GetMsg('IS_NOT_A_VALID_TIMEZONE')

# Time Settings page
#
# level-1 template - requires values for
# - ID-#
# - errors (HTML TABLE)
# - diagnostics (HTML TABLE)
# time zone
# NTP servers
TIME_SETTINGS = """
%%(surrounding_table)s
%%(surrounding_table1)s
<table border=0 width="100%%%%" bgcolor=#ffffff><tr><td width="1%%%%">

%%(header_seperator)s
<tr><td nowrap width="1%%%%" valign=top>
<font size=-1><b>%s:</b></font></td><td>
<font size=-1>%%(whatis_timezone)s</font>
%%(timezone)s
</td></tr>
%%(whatis_tablesep)s
<tr><td nowrap width="1%%%%" valign=top>
<font size=-1><b>%s:</b></font></td><td>
<font size=-1>%%(whatis_ntp)s</font>
<input type="text" value="%%(ntp_servers)s" name=ntp_servers size="50">
%%(basic_network_message_br)s<font size=-1>%%(separate_commas)s</font>
%%(basic_network_message_br)s<font size=-1>%%(example)s%%(colon)s %%(example_ntp)s</font>
%%(basic_network_message_br)s<font size=-1>%%(alert_ntp)s</font>
%%(whatis_lastsep)s
</td></tr></table>
%%(surrounding_tableend)s
""" % ( webserver_base.GetMsg('YOUR_LOCAL_TIMEZONE'),
        webserver_base.GetMsg('NTP_SERVERS'),
      )

# page for time settings
# level 1 template
# needs
# ID-#
# - errors (HTML TABLE)
# - diagnostics (HTML TABLE)
# time zone
# NTP servers

TIME_SETTINGS_PAGE = (PAGE_TEMPLATE_HEADER +
                      """<form method=POST action="/main_config">
                      %(Errors)s<BR>
                      """ +
                      TAB_OBJECT % ('99cc99', 'ffffff',
                                    webserver_base.GetMsg('STEP_1_OF_5'),
                                    webserver_base.GetMsg('BASIC_NETWORK_SETTINGS'),
                                    '99cc99', 'ffffff',
                                    webserver_base.GetMsg('STEP_2_OF_5'),
                                    webserver_base.GetMsg('DNS_SETTINGS'),
                                    '009900', 'ffffff',
                                    webserver_base.GetMsg('STEP_3_OF_5'),
                                    webserver_base.GetMsg('TIME_SETTINGS'),
                                    'efefef', '999999',
                                    webserver_base.GetMsg('STEP_4_OF_5'),
                                    webserver_base.GetMsg('ADMIN_SETTINGS'),
                                    'efefef', '999999',
                                    webserver_base.GetMsg('STEP_5_OF_5'),
                                    webserver_base.GetMsg('TESTURL_SETTINGS')
                                   )  +
                      """ <p> """ +
                      TIME_SETTINGS +
                      SUBMIT_BUTTON_BACK_NEXT +
                      """
<input type=hidden value="%(serve_ip)s" name=serve_ip>
<input type=hidden value="%(switch_ip)s" name=switch_ip>
<input type=hidden value="%(crawl_ip)s" name=crawl_ip>
<input type=hidden value="%(netmask)s" name=netmask>
<input type=hidden value="%(gateway)s" name=gateway>
<input type=hidden value="%(dns_servers)s" name=dns_servers>
<input type=hidden value="%(dns_search_path)s" name=dns_search_path>
<input type=hidden value="%(autonegotiation)s" name=autonegotiation>
<input type=hidden value="%(network_speed)s" name=network_speed>
<input type=hidden value="%(admin_email)s" name=admin_email>
<input type=hidden value="%(smtp_servers)s" name=smtp_servers>
<input type=hidden value="%(testurls)s" name=testurls>
<input type=hidden value="%(outgoing_email_sender)s" name=outgoing_email_sender>
<input type=hidden name=step value="%(step)s">
                      %(Diags)s<br>""" +
                      PAGE_TEMPLATE_FOOTER)


# MISC setting details
# level-1 template - requires values for
# - (for 8-way: autonegotiation toggle)
MISC_SETTINGS = """
%%(surrounding_table)s
%%(surrounding_table1)s
<font size=-1>%%(whatis_admin_mail)s</font>
 %%(basic_network_message_ul)s
  %%(basic_network_message_li)s<font size=-1>%%(admin_mail1)s</font>%%(basic_network_message_li_end)s
  %%(basic_network_message_li)s<font size=-1>%%(admin_mail2)s</font>%%(basic_network_message_li_end)s
  %%(basic_network_message_li)s<font size=-1>%%(admin_mail3)s</font>%%(basic_network_message_li_end)s
  %%(basic_network_message_li)s<font size=-1>%%(admin_mail4)s</font>%%(basic_network_message_li_end)s
 %%(basic_network_message_ul_end)s

 <hr size=1 color=#3366CC>


  <table border=0 cellspacing=0 cellpadding=2 width="100%%%%" bgcolor=#ffffff>
    <tr>
      <th>
        <font size=-1>%s
        </font>
      </th>

      <th>
        <font size=-1>%s
        </font>
      </th>
      <th>
        <font size=-1>%s
        </font>
        </th>
      </tr>
      <tr><td colspan=4><hr size=1 color=#3366CC></td></tr>
      <tr>
        <td align=center valign =top>
          <font size=-1><b>%s</b>

          </font>
        </td>

        <td align=center valign=top>
          <table> <tr> <td>
          <font size=-1>
          %s
          </font>
          </td><td>
          <font size=-1>
          <input type=password name=admin_pass size=25><br>
          </font>
          </td> </tr> <tr><td>
          <font size=-1>
          %s
          </font>
          </td><td>
          <font size=-1>
          <input type=password name=admin_pass2 size=25>
          </font>
          </td> </tr>
                  </table>
        </td>
        <td align=center valign=top>
          <font size=-1>

      <input type=text name=admin_email
           value=\"%%(admin_email)s\" size=30>
          </font>
        </td>
      </tr>
    </table>
%%(surrounding_tableend)s

""" % ( webserver_base.GetMsg('USERNAME'),
        webserver_base.GetMsg('CHANGE_PASSWORD'),
        webserver_base.GetMsg('EMAIL_ADDRESS'),
        'admin',
        webserver_base.GetMsg('NEW_PASSWORD'),
        webserver_base.GetMsg('REENTER'),
       )


# page for misc settings
# level 1 template
# needs
# ID-#
# - errors (ERROR_TABLE)
# - diagnostics (HTML TABLE)
# - admin_email
# - admin_pass
# - admin_pass2 (confirmation)
MISC_SETTINGS_PAGE = (PAGE_TEMPLATE_HEADER +
                      """<form method=POST action="/main_config">
                      %(Errors)s<BR>
                      """ +
                      TAB_OBJECT % ('99cc99', 'ffffff',
                                    webserver_base.GetMsg('STEP_1_OF_5'),
                                    webserver_base.GetMsg('BASIC_NETWORK_SETTINGS'),
                                    '99cc99', 'ffffff',
                                    webserver_base.GetMsg('STEP_2_OF_5'),
                                    webserver_base.GetMsg('DNS_SETTINGS'),
                                    '99cc99', 'ffffff',
                                    webserver_base.GetMsg('STEP_3_OF_5'),
                                    webserver_base.GetMsg('TIME_SETTINGS'),
                                    '009900', 'ffffff',
                                    webserver_base.GetMsg('STEP_4_OF_5'),
                                    webserver_base.GetMsg('ADMIN_SETTINGS'),
                                    'efefef', '999999',
                                    webserver_base.GetMsg('STEP_5_OF_5'),
                                    webserver_base.GetMsg('TESTURL_SETTINGS')
                                   )  +
                      """ <p> """ +
                      MISC_SETTINGS +
                      SUBMIT_BUTTON_BACK_NEXT +
                      """
<input type=hidden value="%(serve_ip)s" name=serve_ip>
<input type=hidden value="%(switch_ip)s" name=switch_ip>
<input type=hidden value="%(crawl_ip)s" name=crawl_ip>
<input type=hidden value="%(netmask)s" name=netmask>
<input type=hidden value="%(gateway)s" name=gateway>
<input type=hidden value="%(dns_servers)s" name=dns_servers>
<input type=hidden value="%(dns_search_path)s" name=dns_search_path>
<input type=hidden value="%(autonegotiation)s" name=autonegotiation>
<input type=hidden value="%(network_speed)s" name=network_speed>
<input type=hidden value="%(ntp_servers)s" name=ntp_servers>
<input type=hidden value="%(timezone)s" name=timezone>
<input type=hidden value="%(smtp_servers)s" name=smtp_servers>
<input type=hidden value="%(testurls)s" name=testurls>
<input type=hidden name=step value="%(step)s">
<input type=hidden value="%(outgoing_email_sender)s" name=outgoing_email_sender>
                      %(Diags)s<br>""" +
                      PAGE_TEMPLATE_FOOTER)


TESTURL_SETTINGS = """
%%(surrounding_table)s
%%(surrounding_table1)s
<font size=-1>%%(whatis_testurl)s</font>
<hr size=1 color=#3366CC>
<table border=0 width="100%%%%"><tr><td nowrap width="1%%%%">
<font size=-1><b>%s:</b></font><br>
<textarea NAME=testurls rows=6 cols=80></textarea>
</td></tr>
</table> <BR>
%%(basic_network_message_ul)s
  %%(basic_network_message_li)s<font size=-1>%%(testurls_bullet1)s</font>
    %%(basic_network_message_ul)s
      %%(basic_network_message_li)s<font size=-1>%%(testurls_example1)s</font>%%(basic_network_message_li_end)s
      %%(basic_network_message_li)s<font size=-1>%%(testurls_example2)s</font>%%(basic_network_message_li_end)s
  %%(basic_network_message_ul_end)s
  %%(basic_network_message_li)s<font size=-1>%%(testurls_bullet2)s</font>%%(basic_network_message_li_end)s
%%(basic_network_message_ul_end)s
%%(surrounding_tableend)s
""" % ( webserver_base.GetMsg('TESTURLS') )

# level 1 template
# needs
# ID-#
# - errors (ERROR_TABLE)
# - diagnostics (HTML TABLE)
# - testurls
TESTURL_SETTINGS_PAGE = (PAGE_TEMPLATE_HEADER +
                         """<form method=POST action="/main_config">
                         %(Errors)s<BR>
                         """ +
                         TAB_OBJECT % ('99cc99', 'ffffff',
                                       webserver_base.GetMsg('STEP_1_OF_5'),
                                       webserver_base.GetMsg('BASIC_NETWORK_SETTINGS'),
                                       '99cc99', 'ffffff',
                                       webserver_base.GetMsg('STEP_2_OF_5'),
                                       webserver_base.GetMsg('DNS_SETTINGS'),
                                       '99cc99', 'ffffff',
                                       webserver_base.GetMsg('STEP_3_OF_5'),
                                       webserver_base.GetMsg('TIME_SETTINGS'),
                                       '99cc99', 'ffffff',
                                       webserver_base.GetMsg('STEP_4_OF_5'),
                                       webserver_base.GetMsg('ADMIN_SETTINGS'),
                                       '009900', 'ffffff',
                                       webserver_base.GetMsg('STEP_5_OF_5'),
                                       webserver_base.GetMsg('TESTURL_SETTINGS'),
                                      ) +
                         """ <p> """ +
                         TESTURL_SETTINGS +
                         SUBMIT_BUTTON_BACK_NEXT +
                         """
<input type=hidden value="%(serve_ip)s" name=serve_ip>
<input type=hidden value="%(switch_ip)s" name=switch_ip>
<input type=hidden value="%(crawl_ip)s" name=crawl_ip>
<input type=hidden value="%(netmask)s" name=netmask>
<input type=hidden value="%(gateway)s" name=gateway>
<input type=hidden value="%(dns_servers)s" name=dns_servers>
<input type=hidden value="%(dns_search_path)s" name=dns_search_path>
<input type=hidden value="%(autonegotiation)s" name=autonegotiation>
<input type=hidden value="%(network_speed)s" name=network_speed>
<input type=hidden value="%(ntp_servers)s" name=ntp_servers>
<input type=hidden value="%(admin_email)s" name=admin_email>
<input type=hidden value="%(timezone)s" name=timezone>
<input type=hidden value="%(smtp_servers)s" name=smtp_servers>
<input type=hidden name=step value="%(step)s">
<input type=hidden value="%(outgoing_email_sender)s" name=outgoing_email_sender>
                         %(Diags)s<br>""" +
                         PAGE_TEMPLATE_FOOTER)
# level 1 template
# needs
# ID-#
# - errors (ERROR_TABLE)
# - diagnostics (HTML TABLE)
# - testurls
CONGRATULATIONS_PAGE = (PAGE_TEMPLATE_HEADER +
                        """<form method=POST action="/main_config">
                        %%(Errors)s<BR>
                        %s""" % webserver_base.GetMsg('CONGRATULATIONS_YOUR_APPLIANCE_IS_CONFIGURED') + """
<input type=hidden value="%(serve_ip)s" name=serve_ip>
<input type=hidden value="%(switch_ip)s" name=switch_ip>
<input type=hidden value="%(crawl_ip)s" name=crawl_ip>
<input type=hidden value="%(netmask)s" name=netmask>
<input type=hidden value="%(gateway)s" name=gateway>
<input type=hidden value="%(dns_servers)s" name=dns_servers>
<input type=hidden value="%(dns_search_path)s" name=dns_search_path>
<input type=hidden value="%(autonegotiation)s" name=autonegotiation>
<input type=hidden value="%(network_speed)s" name=network_speed>
<input type=hidden value="%(ntp_servers)s" name=ntp_servers>
<input type=hidden value="%(admin_email)s" name=admin_email>
<input type=hidden value="%(timezone)s" name=timezone>
<input type=hidden value="%(smtp_servers)s" name=smtp_servers>
<input type=hidden value="%(testurls)s" name=testurls>
<input type=hidden name=step value="%(step)s">
<input type=hidden value="%(outgoing_email_sender)s" name=outgoing_email_sender>
                        """ +
                        SUBMIT_BUTTON_BACK_NEXT +
                        CONGRATULATIONS_PAGE_DIAG +
                        """ %(Diags)s<br>""" +
                        PAGE_TEMPLATE_FOOTER)

CONGRATULATIONS_PAGE_8WAY = (PAGE_TEMPLATE_HEADER +
                        """<form method=POST action="/main_config">
                        %%(Errors)s<BR>
                        %s""" % webserver_base.GetMsg('CONGRATULATIONS_YOUR_APPLIANCE_IS_CONFIGURED') + """
<input type=hidden value="%(serve_ip)s" name=serve_ip>
<input type=hidden value="%(switch_ip)s" name=switch_ip>
<input type=hidden value="%(crawl_ip)s" name=crawl_ip>
<input type=hidden value="%(netmask)s" name=netmask>
<input type=hidden value="%(gateway)s" name=gateway>
<input type=hidden value="%(dns_servers)s" name=dns_servers>
<input type=hidden value="%(dns_search_path)s" name=dns_search_path>
<input type=hidden value="%(autonegotiation)s" name=autonegotiation>
<input type=hidden value="%(network_speed)s" name=network_speed>
<input type=hidden value="%(ntp_servers)s" name=ntp_servers>
<input type=hidden value="%(admin_email)s" name=admin_email>
<input type=hidden value="%(timezone)s" name=timezone>
<input type=hidden value="%(smtp_servers)s" name=smtp_servers>
<input type=hidden value="%(testurls)s" name=testurls>
<input type=hidden name=step value="%(step)s">
<input type=hidden value="%(outgoing_email_sender)s" name=outgoing_email_sender>
                        """ +
                        SUBMIT_BUTTON_BACK_NEXT +
                        CONGRATULATIONS_PAGE_DIAG_8WAY +
                        """ %(Diags)s<br>""" +
                        PAGE_TEMPLATE_FOOTER)

# level 1 template
# needs
# ID-#
# - challenge string
SELFDESTRUCT_CHALLENGE_PAGE = (PAGE_TEMPLATE_HEADER +
                        """<form method=POST action="/selfdestruct">
                        %s
                        <table border=0 width=100%%%%><tr><td width=1%%%%>
                        <font size=-1><b>%s:</b></font></td><td>
                        <input type="text" readonly value="%%(challenge)s"
                        name=challenge size="50">
                        </td></tr>
                        <tr><td width=1%%%%>
                        <font size=-1><b>%s:</b></font></td><td>
                        <input type="text" value=""
                        name=response size="50">
                        </td></tr>
                        </table>
                        """ % (webserver_base.GetMsg('ABOUT_TO_SELFDESTRUCT'),
                               webserver_base.GetMsg('CHALLENGE'),
                               webserver_base.GetMsg('RESPONSE'),
                               ) +
                        SUBMIT_BUTTON_NEXT +
                        PAGE_TEMPLATE_FOOTER)

# level 1 template
# needs
# ID-#
SELFDESTRUCT_DONE_PAGE = (PAGE_TEMPLATE_HEADER +
                          webserver_base.GetMsg('YOUR_APPLIANCE_IS_TOAST') +
                          PAGE_TEMPLATE_FOOTER)

# level 1 template
# needs
# ID-#
# - challenge string
HALT_CHALLENGE_PAGE = (PAGE_TEMPLATE_HEADER +
                        """<form method=POST action="/haltappliance">
                        %s
                        <table border=0 width=100%%%%><tr><td width=1%%%%>
                        <font size=-1><b>%s:</b></font></td><td>
                        <input type="text" readonly value="%%(challenge)s"
                        name=challenge size="50">
                        </td></tr>
                        <tr><td width=1%%%%>
                        <font size=-1><b>%s:</b></font></td><td>
                        <input type="text" value=""
                        name=response size="50">
                        </td></tr>
                        </table>
                        """ % (webserver_base.GetMsg('ABOUT_TO_HALT'),
                               webserver_base.GetMsg('CHALLENGE'),
                               webserver_base.GetMsg('RESPONSE'),
                               ) +
                        SUBMIT_BUTTON_NEXT +
                        PAGE_TEMPLATE_FOOTER)

# level 1 template
# needs
# ID-#
HALT_DONE_PAGE = (PAGE_TEMPLATE_HEADER +
  webserver_base.GetMsg('YOUR_APPLIANCE_WILL_BE_HALTED_SOON') +
  PAGE_TEMPLATE_FOOTER)


# level 1 template
# needs
# ID-#
# - challenge string
ENABLESSHD_CHALLENGE_PAGE = (PAGE_TEMPLATE_HEADER +
                        """<form method=POST action="/enablesshd">
                        %s
                        <table border=0 width=100%%%%><tr><td width=1%%%%>
                        <font size=-1><b>%s:</b></font></td><td>
                        <input type="text" readonly value="%%(challenge)s"
                        name=challenge size="50">
                        </td></tr>
                        <tr><td width=1%%%%>
                        <font size=-1><b>%s:</b></font></td><td>
                        <input type="text" value=""
                        name=response size="50">
                        </td></tr>
                        </table>
                        """ % (webserver_base.GetMsg('ABOUT_TO_ENABLESSHD'),
                               webserver_base.GetMsg('CHALLENGE'),
                               webserver_base.GetMsg('RESPONSE'),
                               ) +
                        SUBMIT_BUTTON_NEXT +
                        PAGE_TEMPLATE_FOOTER)

# level 1 template
# needs
# ID-#
ENABLESSHD_DONE_PAGE = (PAGE_TEMPLATE_HEADER +
  webserver_base.GetMsg('YOUR_APPLIANCE_SSHD_IS_NOW_ENABLED') +
  PAGE_TEMPLATE_FOOTER)

# level 1 template
# needs
# ID-#
# - challenge string
DISABLESSHD_CHALLENGE_PAGE = (PAGE_TEMPLATE_HEADER +
                        """<form method=POST action="/disablesshd">
                        %s
                        <table border=0 width=100%%%%><tr><td width=1%%%%>
                        <font size=-1><b>%s:</b></font></td><td>
                        <input type="text" readonly value="%%(challenge)s"
                        name=challenge size="50">
                        </td></tr>
                        <tr><td width=1%%%%>
                        <font size=-1><b>%s:</b></font></td><td>
                        <input type="text" value=""
                        name=response size="50">
                        </td></tr>
                        </table>
                        """ % (webserver_base.GetMsg('ABOUT_TO_DISABLESSHD'),
                               webserver_base.GetMsg('CHALLENGE'),
                               webserver_base.GetMsg('RESPONSE'),
                               ) +
                        SUBMIT_BUTTON_NEXT +
                        PAGE_TEMPLATE_FOOTER)

# level 1 template
# needs
# ID-#
DISABLESSHD_DONE_PAGE = (PAGE_TEMPLATE_HEADER +
  webserver_base.GetMsg('YOUR_APPLIANCE_SSHD_IS_NOW_DISABLED') +
  PAGE_TEMPLATE_FOOTER)

# level 1 template
# needs
# ID-#
# - challenge string
RESTART_CHALLENGE_PAGE = (PAGE_TEMPLATE_HEADER +
                        """<form method=POST action="/restartappliance">
                        %s
                        <table border=0 width=100%%%%><tr><td width=1%%%%>
                        <font size=-1><b>%s:</b></font></td><td>
                        <input type="text" readonly value="%%(challenge)s"
                        name=challenge size="50">
                        </td></tr>
                        <tr><td width=1%%%%>
                        <font size=-1><b>%s:</b></font></td><td>
                        <input type="text" value=""
                        name=response size="50">
                        </td></tr>
                        </table>
                        """ % (webserver_base.GetMsg('ABOUT_TO_RESTART_SERVICES'),
                               webserver_base.GetMsg('CHALLENGE'),
                               webserver_base.GetMsg('RESPONSE'),
                               ) +
                        SUBMIT_BUTTON_NEXT +
                        PAGE_TEMPLATE_FOOTER)

# level 1 template
# needs
# ID-#
RESTARTING_PAGE = (PAGE_TEMPLATE_HEADER +
  webserver_base.GetMsg('YOUR_APPLIANCE_IS_RESTARTING') +
  PAGE_TEMPLATE_FOOTER)


ALL_SETTINGS_PAGE = (PAGE_TEMPLATE_HEADER +
                      """<form method=POST action="/main_config">
                      %(Errors)s<br>
                      <center>
                      """ +
                      FRAME_TABLE +
                      FRAME_TABLE1 +
                      """ <b> """ + webserver_base.GetMsg('BASIC_NETWORK_SETTINGS') + """</b> """ +
                      """ <font size=-1> %(help_network_settings)s </font> """ +
                      """<table border=0 width="100%%%%" bgcolor=ffffff><tr><td width="1%%%%">""" +
                      IP_SETTINGS +
                      """ </td></tr></table> """ +
                      """ <b> """ + webserver_base.GetMsg('ONLY_DNS_SETTINGS') + """ </b> """ +
                      """ <font size=-1> %(help_dns_and_mail_settings)s </font> """ +
                      """<table border=0 width="100%%%%" bgcolor=ffffff><tr><td width="1%%%%">""" +
                      DNS_SETTINGS +
                      """ </td></tr></table> """ +
                      """ <b> """ + webserver_base.GetMsg('TIME_SETTINGS') + """</b> """ +
                      """ <font size=-1> %(help_time_settings)s </font> """ +
                      """<table border=0 width="100%%%%" bgcolor=ffffff><tr><td width="1%%%%">""" +
                     TIME_SETTINGS +
                      """ </td></tr></table> """ +
                      """ <b> """ + webserver_base.GetMsg('ADMIN_SETTINGS') + """</b> """ +
                      """ <font size=-1> %(help_misc_settings)s </font> """ +
                      """<table border=0 width="100%%%%" bgcolor=ffffff><tr><td width="1%%%%">""" +
                      MISC_SETTINGS +
                      """ </td></tr></table> """ +
                      """ <hr size=2 color=3366CC> """ +
                      """ <b> """ + webserver_base.GetMsg('TESTURL_SETTINGS') + """</b> """ +
                      """ <font size=-1> %(help_testurls)s </font> """ +
                      """<table border=0 width="100%%%%" bgcolor=ffffff><tr><td width="1%%%%">""" +
                      TESTURL_SETTINGS +
                      """ </td></tr></table> """ +
                      FRAME_TABLEEND +
                      SUBMIT_BUTTON_COMMIT +
                      "<BR>%(Diags)s" +
                      PAGE_TEMPLATE_FOOTER
                      )

ALL_SETTINGS_PAGE_8WAY = (PAGE_TEMPLATE_HEADER +
                          """<form method=POST action="/main_config">
                          %(Errors)s<BR>
                          <center>
                          """ +
                          FRAME_TABLE +
                          FRAME_TABLE1 +
                          """ <b> """ + webserver_base.GetMsg('BASIC_NETWORK_SETTINGS') + """</b> """ +
                          """ <font size=-1> %(help_network_settings)s </font> """ +
                          """<table border=0 width="100%%%%" bgcolor=ffffff><tr><td width="1%%%%">""" +
                          IP_SETTINGS_8WAY +
                          """ </td></tr></table> """ +
                          """ <b> """ + webserver_base.GetMsg('ONLY_DNS_SETTINGS') + """ </b> """ +
                          """ <font size=-1> %(help_dns_and_mail_settings)s </font> """ +
                          """<table border=0 width="100%%%%" bgcolor=ffffff><tr><td width="1%%%%">""" +
                          DNS_SETTINGS +
                          """ </td></tr></table> """ +
                          """ <b> """ + webserver_base.GetMsg('TIME_SETTINGS') + """</b> """ +
                          """ <font size=-1> %(help_time_settings)s </font> """ +
                          """<table border=0 width="100%%%%" bgcolor=ffffff><tr><td width="1%%%%">""" +
                         TIME_SETTINGS +
                          """ </td></tr></table> """ +
                          """ <b> """ + webserver_base.GetMsg('ADMIN_SETTINGS') + """</b> """ +
                          """ <font size=-1> %(help_misc_settings)s </font> """ +
                          """<table border=0 width="100%%%%" bgcolor=ffffff><tr><td width="1%%%%">""" +
                          MISC_SETTINGS +
                          """ </td></tr></table> """ +
                          """ <hr size=2 color=3366CC> """ +
                          """ <b> """ + webserver_base.GetMsg('TESTURL_SETTINGS') + """</b> """ +
                          """ <font size=-1> %(help_testurls)s </font> """ +
                          """<table border=0 width="100%%%%" bgcolor=ffffff><tr><td width="1%%%%">""" +
                          TESTURL_SETTINGS +
                          """ </td></tr></table> """ +
                          FRAME_TABLEEND +
                          SUBMIT_BUTTON_COMMIT +
                          "<BR>%(Diags)s" +
                          PAGE_TEMPLATE_FOOTER
                          )


BG_RED = """#FF9090"""   # somewhat light pastel red
BG_GREEN = """#E0FFE0""" # light pastel green
BG_WHITE = """#FFFFFF""" # white
BG_BLACK = """#000000""" # utter black
BG_GRAY = """#F0F0F0"""  # gray
BG_GRAY2 = """#999999""" # a different shade of gray


DIAG_LINE = """<TR><TD><FONT color=%(font_color)s> %(type)s</FONT></td>
<td><FONT color=%(font_color)s size=-1>%(value)s</FONT></td>
<td BGCOLOR=%(status_color)s><FONT color=%(font_color)s size=-1>%(bold_on)s%(status)s%(bold_off)s</FONT></td></tr>"""

DIAG_TABLE = SPACER + """
<center>
<table border=0 width="90%%%%"><tr><td>
<b>%s</b>
<br><font size=-1>%s</font>
<p>
<table border=0 cellpadding=2 cellspacing=0><tr bgcolor=3366CC><td>
<table CELLPADDING=5 cellspacing=0 BORDER=0 bgcolor=ffffff>
%%s
</table>
</td></tr></table>
</td></tr></table>
</center>
""" % ( webserver_base.GetMsg('DIAGNOSTIC_MESSAGES'),
        webserver_base.GetMsg('DIAGNOSTIC_MESSAGES_DETAIL'))

# <H3>%s</H3><TABLE CELLPADDING=5 BORDER=0 ALIGN=CENTER>
#   %%s
# </TABLE>""" % webserver_base.GetMsg('DIAGNOSTIC_MESSAGES')


#lvl-1 template
# requires an error message
ERROR_LINE = """
<tr><td><font  face="arial,sans-serif" size="-1" color="red">
  %s
</font></td></tr>
"""

# lvl-1 template
# requires a string consisting of ERROR_LINEs
ERROR_TABLE = """
<table border=0 width=50%%><tr><td width=1%%>
%s
</table
"""


# This is a static help file explaining the options
HELP_PAGE = (PAGE_TEMPLATE_HEADER +
             """
             <ul>
             <li> <A name=network_settings></a> <b>%s:</b> %s </li><br>
             <li> <b>%s:</b> %s </li><br>
             <li> <b>%s:</b> %s </li><br>
             <li> <b>%s:</b> %s </li><br>
             <li> <b>%s:</b> %s </li><br>
             <li> <b>%s:</b> %s </li><br>
             <li> <A name=dns_and_mail_settings></a> <b>%s:</b> %s </li><br>
             <li> <b>%s:</b> %s </li><br>
             <li> <b>%s:</b> %s </li><br>
             <li> <b>%s:</b> %s </li><br>
             <li> <A name=time_settings></a> <b>%s:</b> %s </li><br>
             <li> <b>%s:</b> %s </li><br>
             <li> <A name=misc_settings></a> <b>%s:</b> %s </li><br>
             <li> <b>%s:</b> %s </li><br>
             </ul>
             """ % (webserver_base.GetMsg('IP_ADDRESS'),
                    webserver_base.GetMsg('WHATIS_SERVE_IP'),
                    webserver_base.GetMsg('SWITCH_IP'),
                    webserver_base.GetMsg('WHATIS_SWITCH_IP'),
                    webserver_base.GetMsg('CRAWL_IP'),
                    webserver_base.GetMsg('WHATIS_CRAWL_IP'),
                    webserver_base.GetMsg('AUTONEGOTIATION'),
                    webserver_base.GetMsg('WHATIS_SERVERIRON_AUTONEGOTIATION'),
                    webserver_base.GetMsg('NETWORK_SPEED'),
                    webserver_base.GetMsg('WHATIS_NETWORK_SPEED'),
                    webserver_base.GetMsg('GATEWAY'),
                    webserver_base.GetMsg('WHATIS_DEFAULT_GATEWAY'),
                    webserver_base.GetMsg('DNS_SERVERS'),
                    webserver_base.GetMsg('WHATIS_DNS_SERVER'),
                    webserver_base.GetMsg('DNS_SEARCH_PATH'),
                    webserver_base.GetMsg('WHATIS_DNS_SEARCH_PATH'),
                    webserver_base.GetMsg('SMTP_SERVER'),
                    webserver_base.GetMsg('WHATIS_SMTP_SERVER'),
                    webserver_base.GetMsg('OUTGOING_EMAIL_SENDER'),
                    webserver_base.GetMsg('WHATIS_OUTGOING_EMAIL_SENDER'),
                    webserver_base.GetMsg('YOUR_LOCAL_TIMEZONE'),
                    webserver_base.GetMsg('WHATIS_TIME_ZONE'),
                    webserver_base.GetMsg('NTP_SERVERS'),
                    webserver_base.GetMsg('WHATIS_NTP_SERVER'),
                    webserver_base.GetMsg('ADMINISTRATOR'),
                    webserver_base.GetMsg('WHATIS_ADMIN_ACCOUNT'),
                    webserver_base.GetMsg('TESTURLS'),
                    webserver_base.GetMsg('WHATIS_TESTURLS')
                  ) +
             PAGE_TEMPLATE_FOOTER
             )
