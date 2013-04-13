# Library to parse GWS logs

import sys, string, urllib, urlparse, re

# TODO: Move client determination code into a separate function

class LogEntry:
    "A place to put parsed log line information"
    line = ''     # Entire log line
    logtype = ''  # One of the LOGTYPE_* constants
    client = ''   # The client name, computed from several other fields
    fields = None # Log line split by tabs into fields
    when = 0      # Unix time of when the log line was created
    where = ''    # Machine name where log line was created
    method = 'GET'# "GET", "HEAD", "PUT", etc.
    http_version = '' # "HTTP/1.0", "HTTP/1.1", etc.
    url = ''      # The requested relative URL
    document = '' # The request URL, without CGI arguments
    query_string = '' # The CGI arguments for the requested URL

    display_language = '' # The GWS-guessed display language
    accept_language = '' # The Accept-Language header
    language_restrict = '' # Like restrict, but for languages only
    query_language = '' # The GWS-guessed language the query is in
    input_encoding = '' # The GWS-guessed encoding for the query

    gzip_encoding = 0
    chunk_encoding = 0
    
    # For queries:
    args = None   # An object of type LogQueryArguments
    # The arguments plus other information lets us compute these:
    search_index = '' # Which index are we using?
    search_restrict = '' # Which restrict within the index?
    search_output = '' # What output format?

    # For Free WebSearch partners, the awfid will be set to the
    # *encrypted* version of the Free ID.  In addition, the client
    # name will be 'custom'.
    awfid = None  # The *encrypted* version of the Free ID
    
    # For Silver/Gold WebSearch partners, the awpid will be set to the
    # *encrypted* version of the Pay ID.  In addition, the client name
    # will be 'cobrand-'+string.lower(awpid).  This way, we can track
    # each Silver/Gold customer separately.
    awpid = None  # The *encrypted* version of the Pay ID

    # For Groups, we want to know the view type (article, thread, etc.)
    groups_view_type = ''
    
    ipaddr = ''   # IP address of user
    response_code = 0 # 200, 404, etc.
    response_bytes = 0 # number of bytes sent in the response content
    response_numresults = 0 # If a search, estimated total # of results
    referer = ''  # Referer field from browser
    user_agent = '' # User-Agent field from browser
    host = ''     # Host field from browser, or blank for 'www.google.com'
    cookie = ''   # Cookie from browser, in ID=1938750193875; * format
    experiment_label = '' # If this line is part of an experiment, its label
    elapsed_total = 0.0 # Total time elapsed (server+client), in seconds
    elapsed_index = 0.0 # Total time in the index servers
    elapsed_doc = 0.0 # Total time spent in the doc servers
    elapsed_server = 0.0 # Total time spent on all server activities
    impressions = '' # Advertisement impressions
    results     = '' # A python list of search result URLs OR a singleton
                     # python list of the url returned by navclient info: query
    session_info_exp = '' # A python list of information requested by the
                          # quality people so that they can more information
                          # about what happens during the SessionInfo Experiment
                          # defined in GWS.  This is a field containing space
                          # separated lists of colon separated lists so the data
                          # should NOT contain colons or spaces.  
                          
# NOTE: 15-Apr-2000, Craig & Marissa changed the sa="I'm Feeling
# Lucky" to btnI="I'm Feeling Lucky".  The result of this is that we
# don't really need to check for I'm Feeling Lucky in other languages.
# If btnI is non-empty, then it's an I'm Feeling Lucky button.
# Marissa is brilliant.

class LogQueryArguments:
    "A place to store default values for cgi arguments"
    # Note that everything here is a string, except for num and start,
    # which are special cased to be integers.
    
    q = ''        # Visible query
    hq = ''       # Hidden query
    dq = ''       # Display query (outdated?)
    num = 10      # Number of results
    start = 0     # Start point (0 based)
    sa = ''       # Button used ('search action'), or special one-letter code
    btnG = ''     # Google Search button used
    btnI = ''     # I'm Feeling Lucky button used
    lc = ''       # Language control ('' or 'www' means "All languages")
    lr = ''       # Language restrict (overrides 'lc')
    hl = ''       # Display language (not really needed, since GWS logs it separately)
    deb = ''      # Debug flags (see gws)
    nocache = ''  # Flag to turn off the cache
    skip = ''     # Skip flags (replaces nocache in GWS 1.5)
    trace = ''    # Tracing flags (see gws)
    search = ''   # An alternative to setting the .../URI?...
    output = ''   # Output only
    site = ''     # Use this (primary) index
    restrict = '' # Restrict within the index
    cat = ''      # Category restrict for the directory
    cof = ''      # Free/Silver/Gold WebSearch custom output form data
    location = '' # Geographic location
    safe = ''     # Safe Search mode
    ai = ''       # Advertising clickthrough information
    rnnav = ''    # RealNames navigation information
    client = ''   # Client name, computed using heuristics
    sourceid = '' # Affiliate ID
    testing = '0'   # '1' if someone is performing a test (still billed)
    u = ''        # URL, for WAP proxy mode
    ie = ''       # Input Encoding
    oe = ''       # Output Encoding
    text = ''     # Text to be translated
    
    # NOTE: COF values are &cof=XYZ where XYZ is
    # FIELD:VALUE;FIELD:VALUE;...  Libgwslog only extracts the AWPID
    # or AWFID.
    
    def is_new_query(self):
        return self.start == 0 and self.sa != 'N'

# List of known clients and their types
try:
    try:
        import clients_file
    except ImportError:
        import sys
        sys.path.append('/home/google/logs/logs_branch/database/')
        import clients_file # TODO: move this to lib? move the data file to ~logs/data ?
    CLIENTS_DATA = clients_file.ClientsData(
                       '/home/google/logs/logs_branch/database/clients-file')
except ImportError:
    # not found, we give up trying
    CLIENTS_DATA = {}
    
TOP_LEVEL_SEARCH_NAMES = {
    # These are /names where we want "/name" to be equivalent to
    # "/name?".  TODO: how can we maintain this list?
    'wml': 1,
    'search': 1,
    'unclesam': 1,
    'bsd': 1,
    'mac': 1,
    'linux': 1,
    'ie': 1,
    'palm': 1,
    'pqa': 1,
    }

# Special dates
MAR_1_2000 = 951897600
APR_2_2001 = 986194800
APR_5_2001 = 986454000
SEP_15_2000 = 969001200
SEP_19_2000 = 969346800
YAHOO_LAUNCH_TIME = 962683540 # 2000-July-3 21:05:40

# Special search actions (sa=) are documented in gws-cgi-arguments.html

LOGTYPE_WEB = 'weblog'
LOGTYPE_PARTNER = 'partnerlog'
LOGTYPE_IMG = 'imglog'
LOGTYPE_URL = 'urllog'
LOGTYPE_DIR = 'dirlog' # Google directory
LOGTYPE_SRV = 'srvlog' # Services
LOGTYPE_WAP = 'waplog' # WAP proxy
LOGTYPE_CLICK = 'clicklog'
LOGTYPE_ADWORDS = 'adwords'
LOGTYPE_ADDURL = 'addedurls'
LOGTYPE_POSTING = 'postinglog'
LOGTYPE_ADMINCONSOLE = 'adminconsole'
LOGTYPE_TOOLBAR = 'toolbarlog'
LOGTYPE_RESULT = 'resultlog'
LOGTYPE_ANSWERS = 'answerslog'
LOGTYPE_INS = 'inslog'
LOGTYPE_LABS = 'labslog'
LOGTYPE_FROOGLE_WEB = 'froogle_weblog'
LOGTYPE_FROOGLE_URL = 'froogle_urllog'
LOGTYPE_GVPS_WEB = 'google_viewer_weblog'
LOGTYPE_PSFE_WEB = 'psfe_weblog'
# TODO: what exactly does "normal" log types mean??  If it means log
# types with real page views, then LOGTYPE_URL should not be here.
_NORMAL_LOGTYPES = (LOGTYPE_WEB, LOGTYPE_PARTNER, LOGTYPE_DIR, LOGTYPE_SRV,
                    LOGTYPE_WAP, LOGTYPE_URL, LOGTYPE_ADWORDS, 
                    LOGTYPE_TOOLBAR, LOGTYPE_POSTING,
                    LOGTYPE_ADMINCONSOLE, LOGTYPE_RESULT,
                    LOGTYPE_ANSWERS, LOGTYPE_INS, LOGTYPE_LABS,
                    LOGTYPE_FROOGLE_WEB, LOGTYPE_FROOGLE_URL,
                    LOGTYPE_GVPS_WEB, LOGTYPE_PSFE_WEB)
QUERYTYPE_NORMAL = 'N'
QUERYTYPE_EMPTY = 'E'
QUERYTYPE_LUCKY = 'L'
QUERYTYPE_CACHE = 'C'
QUERYTYPE_RELATED = 'R'
QUERYTYPE_MIRROR = 'M'
QUERYTYPE_LINK = 'B'
QUERYTYPE_FLINK = 'F'
QUERYTYPE_DETAILS = 'D'
QUERYTYPE_SPELL = 'S'
QUERYTYPE_STOCK = 'T'
QUERYTYPE_WHITEPAGES = 'W'
QUERYTYPE_ID = 'I'
QUERYTYPE_THUMBNAIL = 'G'

QueryTypes_map = {
    # Make sure you update the interpretation of these special queries
    # in set_counter_flags().
    'lucky': QUERYTYPE_LUCKY,
    'cache': QUERYTYPE_CACHE,
    'related': QUERYTYPE_RELATED,
    'mirror': QUERYTYPE_MIRROR,
    'link': QUERYTYPE_LINK,
    'flink': QUERYTYPE_FLINK,
    'details': QUERYTYPE_DETAILS,
    'info': QUERYTYPE_DETAILS,
    'phonebook': QUERYTYPE_WHITEPAGES,
    'spell': QUERYTYPE_SPELL,
    'stocks': QUERYTYPE_STOCK,
    'id': QUERYTYPE_ID,
    'tbn': QUERYTYPE_THUMBNAIL,
    # Note: 'site:', 'group:', 'intitle:', and so on are not query
    # types but term types, so we don't track it here.  Instead they
    # get handled by the log analyzer, when it splits up a query into
    # terms.
    }

CLIENT_HOSTNAMES = {
    # These are clients that have their own XYZ.google.com, and they
    # send non-query traffic to those machines.  To build this list,
    # look in //depot/ops/named/google/primary/db.google.
    'gobi':1,
    'jump':1,
    'fspn':1,
    'virgin':1,
    'netscape':1,
    'cisco':1,
    'redhat':1,
    'vmware':1,
    'hungryminds':1,
    'zangle':1,
    'startups':1,
    'eia':1,
    'theman':1,
    'caldera':1,
    'esmas':1,
    'scotland':1,
    'tlfw':1,
    'groups':1,
    'catalogs':1,
    'news':1,
    'answers':1,
    }
CLIENT_SOURCEIDS = {
    # These are the clients that get separated out if they present a sourceid.
    'navclient': 1,
    'navclient-menuext': 1,
    'intekom': 1,
    'athoc': 1,
    'ebookcity': 1,
    'opera': 1,
    'palm-ref': 1,
    'alladv_list': 1,
    'alladv_default': 1,
    'alladv_list_AUNZ': 1,
    'alladv_default_usa': 1,
    'alladv_default_AUNZ': 1,
    'emailresults-refer': 1,
    'emailresults': 1,
}

CLIENTS_NON_PAGEVIEWS = {
    # These are /names that do not count towards total page views,
    # usually because they are related to frames.
    'translate':1, # frameset
    'translate_p':1, # progress meter
    'translate_n':1, # navigation frame
    'gvps':1 # googleviewer proxy
    }
CLIENTS_NON_SEARCHES= {
    # These are /names that set the client name, are considered page
    # views, but are not considered searches.
    'translate_c':1, # translated html document
    'translate_t':1, # translated freeform text
    'imgres':1, # result frame (not PV) and result frameset (PV)
    'post':1,
    }
CLIENTS_NON_SEARCHES.update(CLIENTS_NON_PAGEVIEWS)

# TODO: CLIENTS_NON_PAGEVIEWS, GWS_NON_SEARCH_URLS,
# CLIENTS_NON_SEARCHES form three boundaries: between hit/pageview,
# pageview/dochit, dochit/indexhit.  They should be more consistent
GWS_NON_SEARCH_URLS = {
    # See gws/header.cc:process_header_end for a list of special URIs.
    # These are /names that do not set the client name at all.
    # Instead we consider them to be static page views on Google.com.
    'swr':1,
    'advanced_search':1,
    'advanced_catalog_search':1,
    'advanced_group_search':1,
    'advanced_image_search':1,
    'preferences':1,
    'setprefs':1,
    'language_tools':1,
    'webhp':1,
    'imghp':1,
    'grphp':1,
    'dirhp':1,
    'nwshp':1,
    'cathp':1,
    'quality_form':1,
    'quality_form_thanks':1,
    }

# TODO: robots.txt should not be counted as a page view
NON_PAGEVIEW_EXTENSIONS = ('.gif', '.jpg', '.ico', '.dtd',
                           '.doc', '.pdf', '.css', '.class',
                           '.xul', '.rdf', '.cab', '.reg', '.js')
PROTOCOLS = ('xml', 'xml_no_dtd', 'protocol', 'protocol2', 'protocol4',
             'protocol3', 'protocol4a', 'protocol5', 'protocolgoogle')

# Many times the wrong client name is in the logs.  This dictionary
# maps the wrong client name to the right one.  After the logic for
# determing the client, we run it through this.
_FIXCLIENTS = {
    'localhost': 'internal',
    'searchq': 'search',
    'sarch': 'search',
    'searh': 'search',
    'googlet Search': 'googlet',
    'goolet': 'googlet',
    'googlet1': 'googlet',
    'googllet': 'googlet',
    'googlet Search': 'googlet',
    'googl': 'googlet',
    'goog': 'googlet',
    'virgin.net': 'virgin',
    'googlesite': 'googleabout',
    
    'gotonet': 'go2net',
    
    'go2ne': 'go2net', # NOTE: should these be 'google' or 'go2net' ?
    'go2n': 'go2net',
    'go2': 'go2net',
    'go': 'go2net',

    # I really prefer the name 'yahoo'.
    'yhoo': 'yahoo',
    'yhoo-cn': 'yahoo-cn',
    'yhoo-tw': 'yahoo-tw',

    # We used 'nx' as an abbreviation to save space on phones
    'nx': 'nextel',
    'nx/': 'nextel',
    
    # Really, all the yahoo-b* should become yahoo-b :(
    'yahoob': 'yahoo-b',
    'yahoo-bcom': 'yahoo-b',
    'yahoo-basd': 'yahoo-b',
    
    'washingtonpos': 'washingtonpost',
    'washintonpost': 'washingtonpost',
    'washingtonpot': 'washingtonpost',
    'nescape': 'netscape',
    'netscape2': 'netscape',
    'indiatimescom': 'indiatimes',
    'indiatim': 'indiatimes',
    'indiatimesswww': 'indiatimes',
    'retevisio': 'retevision',
    'RETEVISION': 'retevision',
    'health': 'healthwide', # They use /health?client=healthwide, ugh
    # People can't cut & paste, what do you expect?  Every prefix is valid ..
    'em': 'emailresults-refer',
    'ema': 'emailresults-refer',
    'emai': 'emailresults-refer',
    'email': 'emailresults-refer',
    'emailr': 'emailresults-refer',
    'emailre': 'emailresults-refer',
    'emailres': 'emailresults-refer',
    'emailresu': 'emailresults-refer',
    'emailresul': 'emailresults-refer',
    'emailresult': 'emailresults-refer',
    'emailresults': 'emailresults-refer',
    'emailresults-': 'emailresults-refer',
    'emailresults-r': 'emailresults-refer',
    'emailresults-re': 'emailresults-refer',
    'emailresults-ref': 'emailresults-refer',
    'emailresults-refe': 'emailresults-refer',
    # These are really old restricts that don't really work.  We
    # decided to use site: instead.  Note that 'vt' and 'sc' are
    # actually university searches, and not two letter domain
    # restricts.  Buh.
    'dk': 'google',
    'uk': 'google',
    'it': 'google',
    'de': 'google',
    'fr': 'google',
    'nd': 'google',
    'jp': 'google',
    # Ugh, why do we have demo machine logs from g93?!
    'demo4': 'internal',
    'filtertest': 'internal',
    'indexonly': 'internal',
    'sitetest1': 'internal',
    'sitetest2': 'internal',
    # hehede.com had a search with &output=hehede, but they seem to be bogus
    'hehede': 'google',
    # During testing, Cisco used some weirder stuff
    'cisco-s1': 'cisco',
    'cisco-s2': 'cisco',
    'cisco-s3': 'cisco',
    'cisco-s4': 'cisco',
    'ciscopub': 'cisco',
    'ciscodoc': 'cisco',
    # People misspell the protocol name
    'protoco': 'unknown-protocol-user',
    'protcol': 'unknown-protocol-user',
    'protcol2': 'unknown-protocol-user',
    'protocol6': 'unknown-protocol-user',
    'protocol7': 'unknown-protocol-user',
    'protocol8': 'unknown-protocol-user',
    'protocol12': 'unknown-protocol-user',
    }

# These partners use or have used &search=foo to identify themselves
# in the past.  Unfortunately, most uses of &search= aren't client
# identification.  We therefore keep a special case list of foos when
# &search=foo is actually valid.  NOTE: there may be more in old logs ..
CLIENTS_USING_SEARCH_ARG = ('gobi', 'redhat', 'vmware')

# These are /names that aren't really associated with restricts, just outputs
NON_RESTRICTS = {
    'ie': 1, 'custom': 1, 'protocol': 1, 'protocol2': 1,
    'protocol4': 1, 'xml': 1, 'xml_no_dtd': 1, 'pqa': 1, 'netscape': 1,
    'palm': 1, 'cobrand': 1,
    }

# WebFerret is a client-side meta search application that masquerades as MSIE.
WEBFERRET_USERAGENT = 'Mozilla/4.0 (compatible; MSIE 5.0; Windows NT; DigExt)'
# They send these headers:
#
# GET http://www.google.com:80/search?q=XYZ&num=100&sa=Google+Search HTTP/1.0
# User-Agent: Mozilla/4.0 (compatible; MSIE 5.0; Windows NT; DigExt)
# Accept: */*
# Host: www.google.com

# Web Position Gold is a search engine optimization program that
# masquerades as Netscape.
WPG_USERAGENT = 'Mozilla/4.51 [en] (Win98; U)'

# Copernic is a client-side meta search application
COPERNIC_USERAGENT_BEFORE_22DEC2000 = 'Mozilla/3.0 (Win95; I)'
COPERNIC_USERAGENT_AFTER_22DEC2000 = 'Mozilla/4.0 (compatible; MSIE 4.01; Windows 98)'

LUCKY_BUTTON = "i'm feeling lucky" # must be lowercase

QUIET = 0
def warning(*args):
    "Print out a warning message.  You can replace this function in apps"
    if not QUIET:
        sys.stderr.write(string.join(map(str, args), ' '))
        sys.stderr.write('\n')
        sys.stderr.flush()


# Here we have regular expressions describing what's a valid language
# code.  Language codes are two letters optionally followed by a dash
# or underscore, and two letters for a country code.  For example,
# "de" and "zh-TW" are both valid language codes.  An Accept-Language
# can be any valid language code.  A Language-Restrict can be either
# "www" to mean no restriction, or a sequence of "lang-L" strings
# separated by "|", where L is any valid language code.  For example,
# "www", "lang_de", and "lang_zh-TW|lang_pt" are valid language
# restricts, but "www|lang_fr" is not.
_LANGUAGE_CODE = r'[a-zA-Z][a-zA-Z](?:[-_][a-zA-Z][a-zA-Z])?'
VALID_ACCEPT_LANGUAGE = re.compile(r'^' + _LANGUAGE_CODE + r'$') # PERF: C function?
_ACCEPT_LANGUAGE_PAT = re.compile(r'^\s*(' + _LANGUAGE_CODE + r')(?:;\S*)?\s*$')
_LANGUAGE_RESTRICT = r'lang_[a-zA-Z][a-zA-Z](?:[-_][a-zA-Z][a-zA-Z])?'
VALID_LANGUAGE_RESTRICT = re.compile(r'^(?:www|' + _LANGUAGE_RESTRICT + '(?:\|' + _LANGUAGE_RESTRICT + ')*)$') # PERF: 708/29000

def fallback_is_valid_accept_language(str):
    return VALID_ACCEPT_LANGUAGE.match(str) is not None

def fallback_is_valid_language_restrict(str):
    return VALID_LANGUAGE_RESTRICT.match(str) is not None

def validated_accept_language(str):
    m = _ACCEPT_LANGUAGE_PAT.match(str)
    return m and m.group(1) or ''

def fallback_parse_accept_language(str, n_langs):
    """Return a tuple of the first n_langs valid accept language strings in the
    comma-separated string str.  Invalid accept languages are replaced by null
    strings, and a tuple shorter than n_langs is padded with null strings."""

    al = string.split(str, ',', n_langs)[:n_langs] # Take only the first n_langs
    al = map(validated_accept_language, al)
    while len(al) < n_langs: al.append('') # Add more if there aren't enough
    return tuple(al)


def process_query_string(dict, query_string):
    """Adds key/value pairs from query_string to the dictionary dict.
    The substrings defining the pairs are separated by '&',
    and each key is separated from its corresponding value by the first '='
    in that substring.
    """
    for name_value in string.split(query_string, '&'):
        index = string.find(name_value, '=')
        if index < 0: continue      # ignore name_value strings missing the '='
        name, value = name_value[:index], name_value[index + 1:]
        name = urllib.unquote(string.replace(name, '+', ' '))
        value = urllib.unquote(string.replace(value, '+', ' '))
        if not value: continue      # ignore pairs with blank values
        if name == 'meta':
            # The meta arg contains other CGI arguments (!!).
            process_query_string(dict, query_string=value)
        else:
            dict[name] = value

def fallback_parse_query_string(query_string):
    dict = {}
    process_query_string(dict, query_string)
    return dict


# Safe search options
#   safe=on => OEM websearch
#   safe=strict => OEM websearch
#   safe=active => main index websearch
#   safe=off => either

# The client has to be an alphanumeric string starting with an alpha.
# Dash and underscore are allowed as well.  To handle University
# search, which started using u/foo as client names, we allow / as the
# second character.  But later on in the code we'll canonicalize u/foo
# into university-foo.
CLIENT_FORMAT = re.compile(r'^[a-zA-Z]/?[-_\w]+$') # TODO: write this in C

# 10.3 is Corp (California) 
# 10.4 is Exodus (California)
# 10.6 is San Jose - Above.Net (California)
# 10.7 is Virginia - Above.Net (Virginia)
# 10.8 is Sunnyvale - GlobalCenter (California)
# 10.9 is Herndon - GlobalCenter (Virginia)
# a1.google.com (209.185.108.138) ran a monitor
# ns.google.com (209.185.108.134) ran a monitor
# 10.10.* were used for proxying.
# 10.4.0.250 was used for proxying 22-28 Apr 2000
_INTERNAL_IPADDRS_5PREFIX = ( # len==5
    '10.3.', '10.4.', '10.5.', '10.6.', '10.7.', '10.8.', '10.9.') 
_INTERNAL_IPADDRS = (
    # Note: in the old days (before 1999-06) we logged hostnames, not ips
    'a1.google.com', '209.185.108.138', # a1 and its ip
    'ns.google.com', '209.185.108.134', # ns and its ip
    )
_INTERNAL_IPADDRS_EXCEPTIONS = ('10.4.0.250', '10.4.200.250', '10.5.0.1',
                                '10.3.4.155', # Exception for Sanjeev testing 
                                # proxies that need to be counted as
                                # external so partners get billed
                                # correctly:
                                '10.11.8.11', '10.11.43.13', # proxies at cw
                                '10.8.63.41', '10.8.78.31', # proxies at ab
                                )

# These IP addresses were used by Yahoo! in April (needed for a special case
# for when they omitted client=yhoo for a time).
_YAHOO_APRIL_IPADDR_SET = {
    '64.209.184.233':None,
    '64.209.184.234':None,
    '64.209.184.235':None,
    '64.209.184.236':None,
    '64.209.184.237':None,
    '64.209.233.134':None,
    '64.209.233.135':None,
    '64.209.233.136':None,
    '64.209.233.137':None,
    '64.209.233.138':None,
    # 64.209.233.139 was not observed during this period
    '64.209.233.140':None,
    '64.209.233.141':None,
    }
# These IP addresses were used for proxying.
_PROXY_IPADDRS = (
    '64.208.36.12',
    '64.208.34.240',
    '64.209.200.240',
    '209.185.108.197'
    )
_IGNORE_CLIENTNAMES = ('', 'search', 'url', 'addurl', 'froogle_url',
                       'localhost', 
                       'xml', 'xml_no_dtd', 'protocol', 'protocol1',
                       'protocol2', 'protocol4', 'Search')
_INTERNAL_MONITORING_URLS = ('/monz', '/healthz', '/health-check.html')
_NORMAL_RESPONSE_CODES = (200, 304, 500, 504)

# The following table corresponds to the code in the detect_*_output
# functions in gws/header.c.
_OUTPUT_FROM_USER_AGENT_TABLE = (
    ('palm',  re.compile(r'.*ProxiNet|.*Elaine|.*AvantGo|.*Go\.Web')),
    ('imode', re.compile(r'.*DoCoMo')),
    ('jsky',  re.compile(r'.*J-Phone')),
    ('wml',   re.compile(r'.*UP\.Browser|.*Cellphone|.*CellPhone|.*cellphone'
                         r'|Nokia7110|Nokia9110|Nokia6210|Nokia6250')),
    )

# Concatenates the regular expressions from the previous table into a
# single one that should match any user agent that determines the output.
_USER_AGENT_DETERMINES_OUTPUT = re.compile(string.join(
    map(lambda (o, r): r.pattern, _OUTPUT_FROM_USER_AGENT_TABLE), '|'))

def parse_cgi(entry, i):
    # It's dynamic content (a search), which should tell us the client
    # Split the URL into document + query string
    entry.document = entry.url[:i]
    entry.query_string = entry.url[i+1:] # Extract the query string

    # Now parse the query string into fields
    entry.args = LogQueryArguments()
    args = parse_query_string(entry.query_string)

    for k,v in args.items(): # Turn a dictionary into an object
        if k == 'query': k = 'q' # Special case: (&q=foo) (&query=foo)
        if k == 'source-id': k = 'sourceid' # Oops, Amit told Yahoo & Doug to use source-id
        # Fix up the numeric fields (num, start)
        if k == 'num' or k == 'start':
            try: v = int(v)
            except ValueError: v = None
            if v is None: continue # If we can't convert, don't set this field
        setattr(entry.args, k, v)

    # Sanity check
    if entry.args.num < 0: del entry.args.num
    if entry.args.num > 200: entry.args.num = 32767 # Large invalid number
    if entry.args.start < 0: del entry.args.start
    if entry.args.start > 10000: entry.args.num = 32767 # Large invalid number
    
    # Special case: (/cache?q=foo) (/search?q=cache:foo)
    if entry.document == '/cache':
        entry.document = '/search'
        entry.args.q = 'cache:' + getattr(entry.args, 'q', '')

    # HungryMinds and others used &search= instead of &q=
    if not args.has_key('q') and args.has_key('search'):
        entry.args.q = entry.args.search
        del entry.args.search

def parse_search(entry):
    """Assuming it's a search log line, compute some things like
    the index, restrict, and client"""
    assert entry.args is not None
    # Determine the search type
    base_search_type = entry.document[1:]
    if not base_search_type and entry.args.search in CLIENTS_USING_SEARCH_ARG:
        base_search_type = entry.args.search
        
    entry.search_index = (entry.args.site
                          or entry.args.restrict
                          or base_search_type)
    if _USER_AGENT_DETERMINES_OUTPUT.match(entry.user_agent):
	for output, regexp in _OUTPUT_FROM_USER_AGENT_TABLE:
	    if regexp.match(entry.user_agent):
		entry.search_output = output
	assert entry.search_output

	# See process_query() in gws/query.c for the rationale behind this.
	if entry.document[0:4] == '/pqa':
	    entry.search_output = 'pqa'
    else:
	entry.search_output = entry.args.output or base_search_type
    entry.search_restrict = entry.args.restrict
    if (not entry.search_restrict and
        not NON_RESTRICTS.has_key(base_search_type)):
        # Some /names aren't really restricts
        entry.search_restrict = base_search_type
    entry.language_restrict = entry.args.lr or entry.args.lc or 'www'

    # Special case for rhlinux
    if entry.search_index == 'rhlinux':
        base_search_type = 'redhat'
        entry.search_index = 'redhat'
        entry.search_output = 'redhat'
        entry.search_restrict = 'linux'

    # Determine the client
    ignore_set = _IGNORE_CLIENTNAMES
    client = ''
    if (CLIENT_FORMAT.match(base_search_type) and
        entry.response_code in _NORMAL_RESPONSE_CODES):
        # If it's a normal response, we can consider the base search
        # type.  However if it's a redirect or 404 or something of
        # that sort, then we say that it's the client's fault, and we
        # don't want to consider it a client.  This is mostly an issue
        # with people requesting bogus URLs, and we return 404s.
        if GWS_NON_SEARCH_URLS.has_key(base_search_type):
            client = 'google-site'
        else:
            client = base_search_type

    if base_search_type[:5] == 'univ/':
        # Google-university program
        client = 'google-university'
    
    if client in ignore_set: client = entry.args.output
    if client in ignore_set and entry.args.sourceid:
        # Affiliates have a "&sourceid=" field
        if CLIENT_FORMAT.match(entry.args.sourceid):
            if CLIENT_SOURCEIDS.has_key(entry.args.sourceid):
                # These guys are worth keeping a separate report for
                client = entry.args.sourceid
            elif entry.args.sourceid[:3] == 'ad-':
                # It's a banner ad; lump them all together
                client = 'google-banner-ad'
            else:
                # We don't know what it is .. just lump them together
                client = 'google-referral'
        else:
            client = 'google-affiliate'
    if client in ignore_set: client = 'google'

    # Retevision made a mistake, so we have to check for it
    if (entry.args.output == 'protocol2' and
        hasattr(entry.args, 'cliente') and
        client == 'google'):
        client = entry.args.cliente

    # The &client= value almost always overrides whatever we computed
    # above.  TODO: don't even bother with the above logic when there
    # is a valid &client=.
    if entry.args.client:
        # We will allow &client= to set the client name when the
        # output is 'search', as long as the corrected client name is
        # defined in our valid clients list.
        potential_client_name = _FIXCLIENTS.get(entry.args.client, entry.args.client)
        
        if ((potential_client_name[:1] == '<' and
            potential_client_name[-1:] == '>') or
            (potential_client_name[:1] == '"' and
             potential_client_name[-1:] == '"')):
            # Ray's protocol document says to use <xyz>  or "xyz" but some
            # people take <> or "" literally.  So far I've only noticed
            # webmatchit, in April/2000, and libertel, in July/2000, doing this.
            
            potential_client_name = potential_client_name[1:-1]
            
        if CLIENT_FORMAT.match(potential_client_name) and \
           (entry.search_output != 'search' or
            CLIENTS_DATA.has_key(potential_client_name)):
            if not (potential_client_name == 'yahoo' and
                    entry.search_output not in PROTOCOLS):
                # Note: Yahoo started sending users to
                # google.com/groups?client=yhoo.  :-( So we'll assign
                # the client UNLESS it's the bogus Yahoo ones.
                client = potential_client_name
            
            if client == 'go2net' and entry.search_output not in PROTOCOLS:
                # Note: go2net sent google.com users to
                # gotonet.google.com/search?client=go2net.  We special
                # case these and don't consider the go2net client.  :(
                client = 'google'

            if client == 'virgilio' and entry.search_output in PROTOCOLS:
                # Itmatrix started using client=virgilio for both
                # their WAP deal and their WebSearch deal (which
                # should have client=itmatrix).
                client = 'itmatrix'

            if client == 'palm' and base_search_type == 'pqa':
                # In addition, we have to special case the MyPalm portal.
                # They used /pqa?client=palm&site=search.  In this case we
                # want to set the client name to be 'mypalm' to
                # distinguish it from Google's 'palm' client.
                client = 'mypalm'
            
    # If it's a protocol user and they haven't set a real client, it
    # should be considered separately so that we can figure out their
    # IP address and so forth.
    if client == 'google' and entry.search_output in PROTOCOLS:
        client = 'unknown-protocol-user'
        
        if entry.ipaddr in ('164.109.17.25', '164.109.17.47', '164.109.17.241'):
            # It's PlanetClick, but they didn't put in the proper client=
            client = 'planetclick'
        elif entry.ipaddr[:12] == '208.185.162.':
            # It's esmas, who's doing lots of messed up stuff to us
            client = 'esmas'
        elif entry.ipaddr == '64.41.181.208':
            # Microland doesn't want to put in a client name on some stuff
            client = 'microland'
        elif entry.args and hasattr(entry.args, 'testid'):
            # It's Yahoo's test queries
            client = 'yahoo-test'
        elif (APR_2_2001 <= entry.when <= APR_5_2001 and
              _YAHOO_APRIL_IPADDR_SET.has_key(entry.ipaddr)):
            # Between these dates, Yahoo didn't always send client=yhoo.
            client = 'yahoo'

    if client == 'noname':
        if (entry.ipaddr in ('216.149.228.2', '207.127.106.130') or
            # TODO: this range should be put elsewhere.  It's our new
            # "portable IP address space" (according to Urs).
            '216.239.32.' <= entry.ipaddr[:11] <= '216.239.47.' or
            entry.ipaddr in _PROXY_IPADDRS):
            # It's SearchCactus, but they put in client=noname !?!?
            client = 'searchcactus'

    # Hacks for Nextel
    if base_search_type == 'wml' and entry.ipaddr[:8] == '170.206.':
        # They sent us queries from the 170.206.*.* block, but didn't
        # use &client=nx
        client = 'nx'

    # Sanity check the format of the client
    m = CLIENT_FORMAT.match(client)
    if not m:
        if entry.response_code != 404:
            warning('Warning: bad client string: ', `client`)
        client = 'unknown'

    # Handle the Free/Silver/Gold partners
    if base_search_type == 'custom':
        # It's a Free partner, so look for AWFID= in the cof field
        i = string.find(entry.args.cof, 'AWFID:')
        if i >= 0:
            entry.awfid = string.lower(entry.args.cof[i+6:i+22])
            if not re.match(r'^-?[\da-z]+$', entry.awfid):
                # It's invalid, but GWS doesn't care, so it can happen a lot
                # warning('Warning: invalid AWFID: ', `entry.awfid`)
                del entry.awfid
    elif base_search_type == 'cobrand':
        # It's a Silver/Gold partner, so look for AWPID in the cof field
        i = string.find(entry.args.cof, 'AWPID:')
        if i >= 0:
            entry.awpid = string.lower(entry.args.cof[i+6:i+22])
            if not re.match(r'^[\da-z]+$', entry.awpid):
                # It's invalid, and GWS really cares so this shouldn't happen much
                warning('Warning: invalid AWPID: ', `entry.line`)
                del entry.awpid
            else:
                # Silver/Gold customers get to have their own client strings
                client = 'cobrand-' + entry.awpid
    elif entry.args.cof:
        # Why do they have a cof when they're not /custom or /cobrand??
        #if base_search_type != 'search':
        #    warning('Warning: cof field should not be present: ', `entry.line`)
        pass
        
    if client[1:2] == '/':
        # Special case: university searches use GET /u/universityname
        # as of 9/20/00.  
        if client[:1] == 'u':
            client = 'university-' + client[2:]
        else:
            client = 'unknown'
            
    if client == 'google' and entry.args.cat[:4] == 'gwd/':
        # It's our directory search
        client = 'google-directory'

    if client == 'yahoo' and entry.when < YAHOO_LAUNCH_TIME:
        # Yahoo was testing during this time
        client = 'yahoo-test'
        
    if client == 'indexonly':
        # It's our internal/research scripts
        client = 'internal'

    if entry.url == '/search?num=5&q=foo':
        # It's our monitoring program
        client = 'internal'
        
    if string.find(entry.url, 'this_is_mongoogle') >= 0:
        # It's our monitoring program, mongoogle
        client = 'internal'

    if (hasattr(entry.args, 'siterock') or
        hasattr(entry.args, 'this_is_siterock')):
        # It's our external monitoring program, Site Rock
        client = 'internal'

    if ((entry.args.q == 'foo' or entry.search_output in PROTOCOLS) and
        entry.ipaddr in ('209.220.161.25', '63.83.186.67', '209.237.29.58')):
        # It's Google's corp site -- some other monitoring program or test script
        client = 'internal'

    if entry.args.q[:22] == '_google_monitor_query_':
        # It's external monitoring of a sitesearch partner
        client = 'internal'

    if (client == 'hungryminds' and
        entry.search_output == 'hungryminds' and
        (entry.args.q == 'learning' or
         entry.args.q == 'green' or
         string.find(entry.user_agent, 'CA Web Response Monitor') >= 0)):
        # It's HungryMinds internal testing (IP) or external testing (user agent)
        client = 'hungryminds-testing'
    
    if client == 'news' and hasattr(entry.args, 'persist'):
        if entry.args.persist== '1':
             client = 'news-persistent'
    
    entry.client = string.lower(client)
    

def fallback_parse_logline_basic(entry, line, warning=lambda *args: None):
    entry.line = line

    # The log line is filled with tab separated fields
    entry.fields = fields = string.split(line, '\t')

    if len(fields) < 10 or string.find(fields[0], ']') < 0:
        warning('SUSPICIOUS LINE: ', `line`)
        return None

    # Strip any final newline.
    if fields[-1][-1:] == '\n':
        fields[-1] = fields[-1][:-1]

    # Fill the rest of the line in with blank fields
    while len(fields) < 15:
        fields.append('')

    # Parse the when/where field [date:time] unixtime machinename
    a = string.split(fields[0])
    try: entry.when = int(float(a[1]))
    except (IndexError, ValueError):
        # Something's corrupted with the *collected* logs, ugh.
        warning('Corruption in collected logs: ', `line`)
        return None
    if len(a) < 3: entry.where = ''
    else:          entry.where = a[2]

    # Parse the HTTP request line
    a = string.split(fields[1])
    if len(a) < 2:
        if fields[1]: warning('Warning, bad request: ', `line`)
        return None
    entry.method = a[0]
    entry.url = a[1]
    if len(a) == 3: entry.http_version = a[2]

    # Parse the other fields
    entry.ipaddr = fields[2]

    try: entry.response_code = int(fields[3])
    except ValueError: entry.response_code = 0
    try:
        # Note: as of 9/7/00, Craig is logging "gz" and "ch" in this
        # field if the content was sent back gzipped and/or chunked,
        # respectively.  These tags are separated by spaces from the
        # size in bytes.

        f = fields[4]
        i = string.find(f, ' ')
        if i > 0:
            entry.gzip_encoding = (string.find(f[i:], 'gz') > 0)
            entry.chunk_encoding = (string.find(f[i:], 'ch') > 0)
            f = f[:i]
        entry.response_bytes = int(f)
    except ValueError: entry.response_bytes = 0
    # Note: as of 6/17/00, numresults for cache: queries will be 0 if
    # there was no page found, and 1 if the page was found.
    # Note: as of 7/29/03, numresults is a whitespace separated list of
    # numbers (various result counts for blimpie)
    try: entry.response_numresults = int(string.split(fields[5])[0])
    except ValueError: entry.response_numresults = 0
    except IndexError: entry.response_numresults = 0

    entry.referer = fields[6]
    entry.user_agent = fields[7]
    entry.host = fields[8] # '' == 'www.google.com'
    entry.cookie = fields[9]

    entry.experiment_label = ''
    
    # 24-Feb-2000: Ben S and Amit agreed to free up extra fields in the log
    # format by moving all the timing information into field 10.
    if entry.logtype == LOGTYPE_WAP:
        # Ugh, they put random gunk into the timing field
        timings = (None, None, None, None)
    elif entry.when >= MAR_1_2000 or string.find(fields[10], ' ') >= 0:
        # It's the new format, so expect timing in fields[10]
        timings = string.split(fields[10])
        # and fields[11:14] are free for other uses
        entry.experiment_label = fields[13]
        language = fields[11]
        i = string.find(language, ' ')
        if i < 0: i = len(language)+1 # Rely on "abc"[50:] being ""
        entry.display_language = language[:i]
        entry.accept_language = language[i+1:]

        i = string.find(entry.display_language, ':')
        if i >= 0:
            # As of 6/14/01, Benjamin D refined the display language
            # string to include the input encoding and the query
            # language.
            subfields = string.split(entry.display_language, ':')
            if len(subfields) < 3: subfields = subfields + ['', '', '']
            entry.display_language = subfields[0]
            entry.input_encoding = subfields[1]
            entry.query_language = subfields[2]
        else:
            entry.input_encoding = getattr(entry.args, 'ie', '')
            entry.query_language = entry.display_language
            
        while len(timings) < 4: # Add any omitted fields
            timings.append('0.0')
    elif fields[10]:
        # It's the old format, which takes up four fields
        timings = fields[10:14]
    else:
        # It's just blank, for example, GWD stuff
        timings = (None, None, None, None)

    try: entry.elapsed_total = float(timings[0] or '0')
    except ValueError:
        warning('Could not parse elapsed_total: ', `line`)
    try: entry.elapsed_index = float(timings[1] or '0')
    except ValueError:
        warning('Could not parse elapsed_index: ', `line`)
    try: entry.elapsed_doc = float(timings[2] or '0')
    except ValueError:
        warning('Could not parse elapsed_doc: ', `line`)
    try: entry.elapsed_server = float(timings[3] or '0')
    except ValueError:
        warning('Could not parse elapsed_server: ', `line`)

    entry.impressions = fields[14]
    if len(fields) > 15:
        entry.results = string.strip(fields[15])
        if len(fields) > 16:
            entry.session_info_exp = string.strip(fields[16])
    return entry

def parse_logline(line, logtype):
    entry = LogEntry()
    entry.logtype = logtype
    if not parse_logline_basic(entry, line, warning):
        return None

    # Netscape has a stupid way of implementing the handy "? foo"
    # feature, which performs a search if you either (a) type in
    # multiple words in the address bar, or (2) type in ? followed by
    # some words in the address bar.
    if entry.url[:9] == '/keyword/':
        # We have one of these goofy URLs, which need to be converted
        # into CGI format. It could be /keyword/keyword/... or
        # /keyword/kwoff/... so we find the / after /keyword/ and hope
        # it's enough.
        i = string.find(entry.url, '/', 10)
        if i <= 0: i = 8
        # It might have "?" at the beginning, so strip that off
        if entry.url[i:i+3] == '%3F': i = i+3
        # It might have leading spaces, so strip them off too
        while entry.url[i:i+3] == '%20': i = i+3

        # Now stuff the altered version back into the url so that the
        # rest of the system doesn't have to know about it.
        entry.url = '/search?q=' + entry.url[i+1:]
        
    # Now if it's a CGI script, parse the args
    entry.document = entry.url
    entry.query_string = ''

    # GWS allows the following escaping: everything *before* the first
    # '?' is unescaped.  The escaped characters in this segment are
    # part of the URL.  Escaped characters after the '?' are part of
    # the CGI arguments.
    i = string.find(entry.url, '?')
    if i < 0: i = len(entry.url)
    entry.url = unquote(entry.url[:i]) + entry.url[i:]

    # HTTP/1.1 allows absolute URIs (see section 5.1.2 in HTTP/1.1 spec)
    if entry.url[:7] == 'http://':
        entry.url = urlparse.urlunparse( ('', '') +
                                         urlparse.urlparse(entry.url)[2:])
        
    # Remove the fragment identifier
    i = string.find(entry.document, '#')
    if i >= 0: entry.document = entry.document[:i]
    
    # Now look for CGI arguments
    i = string.find(entry.url, '?')
    if i >= 0:
        # It at least has CGI arguments.
        parse_cgi(entry, i)
    elif TOP_LEVEL_SEARCH_NAMES.has_key(entry.document[1:]):
        # It doesn't have a ?, but it's a "/name" that we want to
        # consider equivalent to "/name?".
        i = len(entry.url)
        entry.args = LogQueryArguments()
        
    if i >= 0 and entry.logtype in (LOGTYPE_WEB, LOGTYPE_PARTNER,
                                    LOGTYPE_URL, LOGTYPE_RESULT,
                                    LOGTYPE_GVPS_WEB):
        # Not only does it have CGI arguments, it's a "standard"
        # search URL, and we want to determine the client name in the
        # usual way.  TODO: urllog doesn't belong here when it's a redirect?
        if 0 <= string.find(entry.url, 'dnquery.xp') < i:
            # It's really a Deja URL, and we should treat it as a
            # redirect.  From 2001-Mar-23 to 2001-Mar-26, Groups was
            # using meta refresh, which gets logged as a 200 instead
            # of a 302.
            entry.response_code = 302
        parse_search(entry)

        # prevent self serve content ads from overwhelming the system:
        if entry.client[:7] == 'ca-pub-':
            entry.client = 'ca-pub'
    else:
        # It's a non-search/click, so we determine the client by
        # the hostname, the filename, and other heuristics.
        i = string.find(entry.host, '.google.')
        if i > 0:
            hostname = string.lower(entry.host[:i])
            if CLIENT_HOSTNAMES.has_key(hostname):
                entry.client = hostname
        elif string.find(entry.host, 'deja') >= 0:
            entry.client = 'groups'

        if entry.method != 'GET' and entry.method != 'POST':
            # We use HEAD / for the Server Iron.
            # TODO: what about bots that hit us with HEAD requests?
            entry.client = 'internal'

        # Now we use the filename and log type, but only if the client
        # wasn't already determined in another way.
        if entry.client:
            pass
        elif string.find(entry.url, 'netscapeimg') >= 0:
            entry.client = 'netscape'
        elif entry.document[1:6] == 'univ/':
            entry.client = 'google-university'
        # TODO: this mapping of log types to client names belongs
        # at the very top, not here, because if you add a new log
        # type, it's easy to forget adding a new client here.
        elif entry.logtype == LOGTYPE_DIR:
            if entry.args and entry.args.client:
                entry.client = _FIXCLIENTS.get(entry.args.client, entry.args.client)
            else:
                entry.client = 'google-directory'
        elif entry.logtype == LOGTYPE_SRV:
            entry.client = 'google-services'
        elif entry.logtype == LOGTYPE_WAP:
            if entry.document[:9] == '/wmltrans':
                entry.client = 'wml'
            elif entry.document[:11] == '/chtmltrans':
                entry.client = 'imode'
            else:
                entry.client = 'wap'
        elif entry.logtype == LOGTYPE_POSTING:
            entry.client = 'post'
        elif entry.logtype == LOGTYPE_ADMINCONSOLE:
            entry.client = 'google-adminconsole'
        elif entry.logtype == LOGTYPE_ADWORDS:
            entry.client = 'google-adwords'
        elif entry.logtype == LOGTYPE_TOOLBAR:
            entry.client = 'google-toolbar'
        elif entry.logtype == LOGTYPE_CLICK:
            entry.client = 'google-ad-click'
        elif entry.logtype == LOGTYPE_INS:
            entry.client = 'google-ins'
        elif entry.logtype == LOGTYPE_LABS:
            entry.client = 'google-labs'
        elif entry.logtype == LOGTYPE_PSFE_WEB:
            entry.client = 'newsalerts'

        elif string.find(entry.url, '/lgtech/') >= 0:
            # It's a Logitech redirect URL, which gets logged as 200 instead of 302
            entry.response_code = 302
        else:
            # TODO: merge this into the default client per logtype
            entry.client = 'google'
            
    # Extra rules for determining the client
    if entry.args and (entry.args.sa == 'D' or entry.args.deb != ''):
        # It's our internal load testing
        entry.client = 'internal'
    elif entry.client == 'wap' and logtype != LOGTYPE_WAP:
        # For a while, the WAP Apache server was sending queries to
        # GWS, so they got logged twice.
        entry.client = 'wap-internal'
    elif ((entry.ipaddr[:5] in _INTERNAL_IPADDRS_5PREFIX and
           entry.ipaddr not in _INTERNAL_IPADDRS_EXCEPTIONS) or
          entry.ipaddr in _INTERNAL_IPADDRS) and entry.client != 'soap':
        # It's our internal monitoring or other activity
        entry.client = 'internal'
    elif entry.ipaddr == '209.185.253.175':
        # It's the external Exodus address # TODO: what about other external IPs?
        if entry.client == 'emailresults-refer':
            # Note: the email results service performs the query again
            # to determine what results to send to the user .. we
            # don't want to count them as real queries
            entry.client = 'emailresults-internal'
        else:
            entry.client = 'internal'
    elif entry.ipaddr[:11] == '216.86.226.' and (
        entry.args and (entry.args.q == 'ichy iktestus' or entry.args.testing != '0')):
        # It's RealNames testing us
        entry.client = 'realnames-testing'
    elif entry.document in _INTERNAL_MONITORING_URLS:
        # It's our internal monitoring
        entry.client = 'internal'
    elif (entry.ipaddr[:11] == '194.168.54.' or
          entry.ipaddr[:10] == '64.69.163.'):
        # It's Virgin, but they didn't put in the proper client=
        # because they aren't even using protocol2.
        if not hasattr(entry.args, 'client'):
            entry.client = 'virgin'
    elif string.find(entry.user_agent, 'Keynote-Perspective') >= 0:
        # It's Keynote - external monitoring
        entry.client = 'keynote'
    elif string.find(entry.user_agent, 'Googlebot') >= 0:
        # It's us crawling ourselves.  Yuck!
        entry.client = 'internal'
    elif (entry.user_agent == WEBFERRET_USERAGENT and
          entry.accept_language == '' and
          entry.referer == '' and
          entry.cookie[:1] == '+'):
        # The bastards!  No cookie, no accept-language, ..
        # And mostly num=100, no referer
        entry.client = 'webferret'
    elif ((SEP_15_2000 <= entry.when <= SEP_19_2000) and
          entry.user_agent == '' and
          entry.cookie[:1] == '+' and
          entry.referer == '' and
          entry.accept_language == ''):
        # The bastards!  From Sep 15 to Sep 19, WebFerret just took out
        # the user agent .. and they did num=10, hl=en, safe=off to
        # look more like our real users.
        entry.client = 'webferret'
    elif (entry.user_agent == WPG_USERAGENT and
          entry.accept_language == 'en' and
          entry.http_version == 'HTTP/1.0' and
          entry.gzip_encoding == 0 and
          entry.cookie[:1] == '+'):
        # Web Position Gold
        entry.client = 'webpositiongold'
    elif (entry.fields[12] == 'HARLEU' and
          entry.search_output == 'search' and
          entry.accept_language == 'en-us' and
          entry.cookie[:1] == '+' and
          entry.response_code == 200):
        # New Web Position Gold
        entry.client = 'webpositiongold'
    elif (((entry.when < 977514120 and # 11:42am Fri 22 Dec 2000
            entry.user_agent == COPERNIC_USERAGENT_BEFORE_22DEC2000)
           or (entry.when >= 977514120 and
               entry.user_agent == COPERNIC_USERAGENT_AFTER_22DEC2000)) and
          entry.args is not None and
          entry.args.site == 'search' and
          entry.referer == ''):
        # Copernic U.S. uses cookies and has &site=search.  We tried
        # to block them the evening of Thursday 21 Dec 2000.  They
        # changed their user agent the morning of Friday 22 Dec 2000.
        entry.client = 'copernic'
    elif (entry.user_agent == COPERNIC_USERAGENT_BEFORE_22DEC2000 and
          entry.args is not None and
          entry.args.hl != '' and
          entry.referer == ''):
        # Copernic Europe uses cookies and has &lr=... &hl=...
        entry.client = 'copernic'
    elif (string.find(entry.user_agent, 'Apple Find') >= 0 or
          (string.find(entry.user_agent, 'URL Access') >= 0 and
           string.find(entry.user_agent, 'Macintosh') >= 0)):
        # Sherlock is tracked separately because it's a potential 
        # distribution deal, and although distribution deals lead to
        # Google.com and would otherwise be marked with the 'google'
        # client name, we want to track them separately.
        entry.client = 'sherlock'
        # TODO: is this worth tracking?  It's going to get confusing
        # because Netscape & Yahoo search also have Sherlock plug-ins.
    elif entry.url[:8] == '/froogle':
        # Since we might be serving froogle through gfe, which logs through
        # weblogs, or through ffe, which logs through froogle_weblogs, we
        # don't want to use the logtype to determine whether a request
        # should be in the froogle client.
        entry.client = 'froogle'
        if entry.args:
            has_query = (getattr(entry.args, 'q', '') + 
                         getattr(entry.args, 'as_q', '') + 
                         getattr(entry.args, 'as_oq', '') + 
                         getattr(entry.args, 'as_epq', ''))
            if string.strip(getattr(entry.args, 'cat', '')) and not has_query:
                entry.client = 'froogle-browse'
            if (entry.response_numresults == 0 and 
                entry.response_code not in (302, 301)):
                # keep redirects in 'froogle' client
                entry.client = 'froogle-nr'
    

    # One last chance to fix up the client
    entry.client = _FIXCLIENTS.get(entry.client, entry.client)
    
    return entry


# For groups URLs having &th= arguments, these are the values of &frame=
# that correspond to an actual thread view, mapping those values to
# view types that we'll put in the groups_view_type field of the entry.
GROUPS_TH_FRAME_TO_VIEW_TYPE = {
    None:    'thread',
    'right': 'thread-fr',
    'off':   'thread-foff',
    }

def set_counter_flags(entry):
    """Determine whether this line counts as a page view, monetizable,
    user search, docserver hit, etc."""
    # The code below looks for evidence that one or more of these
    # flags should be set.  Note: this code determines what could be
    # monetizable, but does not include rules to determine whether
    # something is currently monetized.
    entry.count_pageview = 0 # 0 or 1
    entry.count_search = None # None, 'N' for new (distinct) query, 'E' for existing (continued) query
    entry.count_server = None # None, 'D' for doc only, 'I' for index & doc
    entry.count_monetizable = None # None, 'C' for cat, 'K' for both key & cat
    entry.groups_view_type = '' 

    if entry.document == '/addurl' or (
        entry.document[string.rfind(entry.document, '.'):] in
        NON_PAGEVIEW_EXTENSIONS):
        # It's not a pageview
        pass
    elif entry.response_code == 200 and (
        entry.logtype in _NORMAL_LOGTYPES and entry.logtype != LOGTYPE_URL):
        # It's a page view, except for I'm Feeling Lucky
        entry.count_pageview = 1

        if entry.method != 'GET' and entry.method != 'POST':
            # It's probably HEAD or something else that isn't quite a
            # normal page view.
            entry.count_pageview = 0
        elif entry.logtype == LOGTYPE_DIR:
            # Static directory pages could be used for category ads
            entry.count_monetizable = 'C'
        elif entry.logtype == LOGTYPE_WAP:
            entry.count_server = 'D'
            entry.count_monetizable = 'C'
        elif entry.logtype in (LOGTYPE_SRV, LOGTYPE_TOOLBAR):
            # TODO: we should build both a list of positive and
            # negative examples, and then print warnings on things
            # that fall into neither set.
            if entry.document in ('/go.php3',
                                  '/install.php3',
                                  '/installed.php3',
                                  '/cgi-bin/graphyy.py',
                                  '/already.html',
                                  '/cgi-bin/version.py',
                                  '/cgi-bin/navclient/version.py'):
                entry.count_pageview = 0
            elif entry.document[:6] == '/data/':
                entry.count_pageview = 0
        elif entry.logtype in (LOGTYPE_WEB, LOGTYPE_PARTNER, LOGTYPE_ANSWERS,
                               LOGTYPE_FROOGLE_WEB, LOGTYPE_GVPS_WEB):
            # Web, Groups, Answers, Froogle.  
            # Figure out if there's any query string
            # (&q=, or an advanced query argument that is used to
            # build a query string).  The way q= could be constructed
            # is [q] == [as_q "as_epq" -as_eq] with [as_oq] ORed
            # terms, and [author:as_uauthors], and
            # [subject:as_usubject].  We don't consider as_eq as
            # sufficient to count this as a search, but the others are
            # fine.
            has_query = (getattr(entry.args, 'q', '') +
                         getattr(entry.args, 'as_q', '') +
                         getattr(entry.args, 'as_oq', '') +
                         getattr(entry.args, 'as_epq', '') +
                         getattr(entry.args, 'as_uauthors', '') +
                         getattr(entry.args, 'as_usubject', ''))

            # TODO: as_lq= is like a link: query.  as_rq= is like related:
            
            if entry.client == 'groups' and entry.args:
                # If it's Google groups, we should try to figure out the view type
                # Paul B and Joseph O'S say:
                # regular query:      q=
                # query with group restrict:   q=  group=
                # thread view:        th=
                # article view:        q= (seld= or selm=)
                # full results:         ic=1
                # group list:           group=
                #
                # For the new thread view, Joseph O'S says:
                # frame set:                 threadm=
                # navigation frame:          frame=left th=
                # framed thread:             frame=right th=
                # framed thread docid list:  thl=  (frame assumed)
                # framed article:            frame=right selm=
                frame = getattr(entry.args, 'frame', None)
                if getattr(entry.args, 'th', ''):
                    view_type = GROUPS_TH_FRAME_TO_VIEW_TYPE.get(frame, None)
                    if view_type is not None:
                        # Thread view is rather expensive.  It
                        # involves an indexserver hit plus a
                        # linkserver hit.
                        entry.groups_view_type = view_type
                        entry.count_server = 'I'
                        entry.count_monetizable = 'C'
                    elif frame == 'left':
                        # Navigation frame
                        entry.count_server = 'I'
                        entry.count_pageview = 0
                    else:
                        # Bogus frame=
                        warning('Unknown groups &frame=%s' % `frame`)
                        entry.count_pageview = 0
                elif getattr(entry.args, 'thl', ''):
                    # Thread view by docid list only hits the docservers.
                    entry.groups_view_type = 'thread-docs-fr'
                    entry.count_server = 'D'
                    entry.count_monetizable = 'C'
                elif (getattr(entry.args, 'seld', '') or
                      getattr(entry.args, 'selm', '') or
                      string.find(has_query, 'msgid:') >= 0):
                    # Article view is relatively cheap.  It
                    # involves a linkserver hit followed by a
                    # docserver hit
                    if frame == 'right':
                        entry.groups_view_type = 'article-fr'
                    else:
                        entry.groups_view_type = 'article'
                    entry.count_server = 'D'
                    entry.count_monetizable = 'C'
                elif getattr(entry.args, 'threadm', ''):
                    # Frameset for a framed view
                    entry.groups_view_type = 'frameset'
                    entry.count_pageview = 0
                elif getattr(entry.args, 'ic', ''):
                    # It's "Inline Content", which doesn't really get
                    # used
                    entry.groups_view_type = 'fullresults'
                    entry.count_server = 'D'
                    entry.count_monetizable = 'C'
                elif getattr(entry.args, 'as_umsgid', ''):
                    # It's article view, from advanced search
                    entry.count_server = 'D'
                    entry.count_monetizable = 'C'
                    entry.groups_view_type = 'article'
                elif has_query:
                    # It's a search, possibly with a group restrict
                    # (which we don't track here)
                    entry.count_search = 'N'
                    if entry.args.start != 0 or entry.args.sa == 'N':
                        entry.count_search = 'E'
                    entry.count_server = 'I'
                    entry.count_monetizable = 'K'
                elif getattr(entry.args, 'group', '') or getattr(entry.args, 'as_ugroup', ''):
                    # It's group browsing, which shows both
                    # subgroups of a group name and messages
                    # within the current group name.  Either
                    # section could be blank.  The logs do not say
                    # which sections were shown.  For message
                    # lists, date ranges can be involved.  Group
                    # browsing with messages is essentially an
                    # indexserver hit.
                    entry.groups_view_type = 'group'
                    entry.count_server = 'I'
                    entry.count_monetizable = 'C'
                else:
                    # warning('Unknown view type: %s' % `entry.line`)
                    pass
            elif CLIENTS_NON_PAGEVIEWS.has_key(entry.document[1:]):
                # It looks like a pageview, but it's something that's not
                entry.count_pageview = 0
            elif GWS_NON_SEARCH_URLS.has_key(entry.document[1:]):
                # It looks like a search, but it's just a static page
                pass
            elif CLIENTS_NON_SEARCHES.has_key(entry.document[1:]):
                # It looks like a search, but it's a dynamic page
                entry.count_server = 'D'
                if entry.client == 'translate_c':
                    entry.count_monetizable = 'C'
                elif entry.client == 'translate_t':
                    entry.count_monetizable = 'K'
                elif entry.client == 'imgres':
                    entry.count_server = None
                    if getattr(entry.args, 'frame', '') == 'small':
                        # It's the content frame
                        entry.count_pageview = 0
                    else:
                        # It's the frameset
                        pass
            elif has_query:
                # It's a search!  Well, probably.  We need to make an
                # exception for the navclient, I'm Feeling Lucky, etc.
                if entry.args.num != 0 or entry.client == 'opera':
                    entry.count_search = 'N'
                    if entry.args.start != 0 or entry.args.sa == 'N':
                        entry.count_search = 'E'
                    entry.count_server = 'I'
                else:
                    # An ad server hit counts as a docserver-like hit
                    entry.count_server = 'D'
                entry.count_monetizable = 'K'

                # Note that the 1+ ensures that this will work even if ':' is not found.
                query_prefix = string.lower(entry.args.q[:1+string.find(entry.args.q, ':')])
                query_type = QueryTypes_map.get(query_prefix[:-1], None)
                if (getattr(entry.args, 'sa', '') == 'X' and
                    getattr(entry.args, 'oi', '') in ('rwp', 'bwp')):
                    # These are special flags that tell us this is a
                    # (Residential / Business) Whitepages query.
                    query_type = QUERYTYPE_WHITEPAGES
                    # TODO: there needs to be a way to convey this
                    # query type to hit_pageview_query_special.  Also,
                    # we need to distinguish between business and
                    # residential whitepages.
                    
                if query_type is not None:
                    # We assume all the special searches are docserver
                    # hits.  This is mostly true.  It's not clear how
                    # "Whitepages" and other such things should be
                    # tracked, but considering them docserver hits is
                    # reasonable at least.
                    entry.count_server = 'D'
                    entry.count_monetizable = 'C'
                    if query_type ==  QUERYTYPE_WHITEPAGES:
                        # We can show ads on business but not
                        # residential white pages.
                        if getattr(entry.args, 'oi', '') == 'bwp':
                            entry.count_monetizable = 'K'
                        else:
                            entry.count_monetizable = None
                        entry.count_server = 'I'
                    elif query_type == QUERYTYPE_CACHE:
                        # This is our header on someone else's content
                        entry.count_search = None
                        entry.count_monetizable = None
                    elif query_type == QUERYTYPE_STOCK:
                        # This is really our frame on someone else's content
                        entry.count_monetizable = None
                        entry.count_search = None
                        entry.count_server = None
                    elif query_type == QUERYTYPE_THUMBNAIL:
                        # This is an image, not a page
                        entry.count_monetizable = None
                        entry.count_search = None
                        entry.count_pageview = 0

                if (entry.args.btnI or
                    string.find(string.lower(entry.args.sa),
                                LUCKY_BUTTON) >= 0):
                    # I'm Feeling Lucky is user-initiated but not
                    # something we can sell ads on.  Note that if
                    # there is no query (has_query is false), then I'm
                    # Feeling Lucky *is* a page view (!), because it
                    # shows an input box.  But it's still not
                    # monetizable.
                    entry.count_pageview = 0
                    entry.count_monetizable = None

                if entry.client == 'navclient-auto':
                    # These are automatically generated and therefore
                    # neither user-initiated nor monetizable.  TODO:
                    # we need to count the Logitech navclient the same
                    # way.
                    entry.count_pageview = 0
                    entry.count_search = None
                    entry.count_monetizable = None

        if entry.client == 'soap':
            # Queries from the SOAP client are not pageviews, and are
            # not monetizable.
            entry.count_pageview = 0
            entry.count_monetizable = None

    if entry.args and (entry.args.sa == 'D' or entry.args.deb != ''):
        # It's a debug line, and we don't count these as real, but it
        # does hit the server
        entry.count_pageview = 0
        entry.count_search = None
        entry.count_monetizable = None
                    
class LogAnalyzer:
    "A base class that can be used to derive log analysis classes"

    # Notes:
    #
    # Create a derived class that defines the triggers (hit_* methods)
    # you're interested in.  Note that it's your responsibility to
    # check whether a log line is from a weblog or urllog, and if part
    # of a urllog, which experiment it's part of.  In particular, a
    # query can be logged to both the weblog and the urllog, so if you
    # don't check the logtype, you will see it *twice*.
    #
    # Then instantiate the class, and call process() on it with each
    # parsed log line.  You can get a parsed log line from an unparsed
    # log line by calling parse_logline().
    
    def process(self, entry):
        "Determine what kind of line this is and call appropriate handlers"
        self.hit(entry) # All hits
        if entry.response_code >= 400 or entry.response_code == 0:
            # It's an error of some sort
            self.hit_error(entry)
        elif entry.logtype in _NORMAL_LOGTYPES:
            if entry.document == '/addurl':
                # Hack to fix things up if the /addurl got into the wrong log file ..
                entry.logtype = LOGTYPE_ADDURL
                return self.process(entry)
            elif entry.document == '/url' and entry.args is not None:
                # It's a click of some sort
                self.hit_click(entry)
                if entry.args.sa == 'R' or entry.args.sa == 'r':
                    self.hit_click_realnames(entry)
                elif entry.args.sa in ('A', 'a', 'C', 'c', 'l', 'L'):
                    self.hit_click_advertising(entry)
                elif entry.args.sa == 'S':
                    self.hit_click_searchengine(entry)
                elif entry.args.sa == 'B':
                    if hasattr(entry.args, 'ai'): # Silly adstoo...
                        self.hit_click_advertising(entry)
                    else:
                        self.hit_click_bannerad(entry)
                elif entry.args.sa == 'U':
                    # It's a results click
                    self.hit_click_searchresult(entry)
                elif entry.args.sa == 'm':
                    # maps click
                    self.hit_click_maps(entry)
                elif entry.args.sa == 'X':
                    # Onebox hit of some type...
                    if (hasattr(entry.args, 'start') and
                        hasattr(entry.args, 'num') and
                        hasattr(entry.args, 'q')):
                        # news click
                        self.hit_click_news(entry)
                    elif (hasattr(entry.args, 'q') and
                          entry.args.q[:42] == 'http://www.dictionary.com/cgi-bin/dict.pl?'):
                        # dictionary click
                        self.hit_click_dictionary(entry)
                elif entry.args.sa not in ('a', 'u', 's', 'w'):
                    # NOTE: a, u, s, x are not really defined.  They
                    # are sent by bots that lowercase everything,
                    # thinking the whole world uses Windows.
                    warning('No search action in', `entry.line`)
            elif entry.response_code in (302, 301):
                # It's a redirect, and it's not a click ..
                self.hit_redirect(entry)
            elif (entry.document[string.rfind(entry.document, '.'):] in
                  NON_PAGEVIEW_EXTENSIONS):
                # it's not a pageview
                self.hit_image(entry)
            elif CLIENTS_NON_PAGEVIEWS.has_key(entry.document[1:]):
                # It looks like a pageview, but it's something that's
                # not counted that way (e.g., framesets)
                pass
            else:
                if entry.logtype == LOGTYPE_TOOLBAR:
                    # TODO: Maybe this early out when it doesn't count as
                    # a page view should be taken for all log types.
                    # (But I didn't want to risk that change presently.)
                    if not hasattr(entry, 'count_pageview'):
                      set_counter_flags(entry)
                    if not entry.count_pageview:
                        return
                # It's a page view
                self.hit_pageview(entry)
                if not entry.args:
                    self.hit_pageview_static(entry)
                elif (entry.logtype == LOGTYPE_ANSWERS and 
                      string.strip(entry.args.q)):
                    # answers logs sometimes have queries
                    self.hit_pageview_query(entry)
                    # these queries are "normal" searches in the sense
                    # that we want to keep track of keywords and query
                    # terms
                    self.hit_pageview_query_normal(entry)
                elif (entry.logtype not in (LOGTYPE_WEB, LOGTYPE_PARTNER, 
                                            LOGTYPE_FROOGLE_WEB,
                                            LOGTYPE_GVPS_WEB,
                                            LOGTYPE_PSFE_WEB) or
                      GWS_NON_SEARCH_URLS.has_key(entry.document[1:]) or
                      CLIENTS_NON_SEARCHES.has_key(entry.document[1:])):
                    # Only web logs currently have queries.  Other log
                    # types have URLs with query arguments that are
                    # not actually queries.  In addition, GWS web logs
                    # have some /names with arguments that are not
                    # actually queries. For now, we will consider
                    # these to be plain (but not static) page views.
                    # TODO: rethink the levels we have.  A static page
                    # view != dynamic page view != search query.
                    pass
                elif not string.strip(entry.args.q):
                    self.hit_pageview_query(entry)
                    self.hit_pageview_query_special(entry, QUERYTYPE_EMPTY)
                else:
                    self.hit_pageview_query(entry)
                    i = string.find(entry.args.q, ':')
                    if (entry.args.btnI or
                        string.find(string.lower(entry.args.sa),
                                    LUCKY_BUTTON) >= 0):
                        self.hit_pageview_query_special(entry, QUERYTYPE_LUCKY)
                    elif i < 0:
                        self.hit_pageview_query_normal(entry)
                    else:
                        prefix = string.lower(entry.args.q[:i])
                        if prefix[:1] == '+': prefix = prefix[1:] # Hack for +ing
                        if QueryTypes_map.has_key(prefix):
                            if QueryTypes_map[prefix] == QUERYTYPE_CACHE:
                                # HACK: we should probably do this in parse_logline()
                                entry.num = 1
                            self.hit_pageview_query_special(
                                entry, QueryTypes_map[prefix])
                        else:
                            self.hit_pageview_query_normal(entry)
        elif entry.logtype == LOGTYPE_IMG:
            self.hit_image(entry)
        elif entry.logtype == LOGTYPE_CLICK:
            if entry.args.sa in ('A', 'a', 'C', 'c', 'L', 'l'):
                self.hit_click(entry)
                self.hit_click_advertising(entry)
            else:
                warning("Invalid sa=", `entry.args.sa`, " in clicklog line:",
                        `entry.line`)
        elif entry.logtype == LOGTYPE_ADDURL:
            self.hit_addurl(entry)
        else:
            raise "Unknown hit type: " + entry.logtype

    # Override these functions in the subclass
    def hit(self, entry): pass
    def hit_pageview(self, entry): pass
    def hit_pageview_static(self, entry): pass
    def hit_pageview_query(self, entry): pass
    def hit_pageview_query_normal(self, entry): pass
    def hit_pageview_query_special(self, entry, querytype): pass
    def hit_click(self, entry): pass
    def hit_click_realnames(self, entry): pass
    def hit_click_advertising(self, entry): pass # Internal advertising
    def hit_click_bannerad(self, entry): pass # External advertising
    def hit_click_searchengine(self, entry): pass
    def hit_click_searchresult(self, entry): pass
    def hit_click_news(self, entry): pass
    def hit_click_dictionary(self, entry): pass
    def hit_click_maps(self, entry): pass
    def hit_redirect(self, entry): pass # other than clickthrough tracking
    def hit_error(self, entry): pass # 404, 408, 500, 504, etc.
    def hit_image(self, entry): pass # image or other helper data
    def hit_addurl(self, entry): pass

_BROWSER_TYPES = [
    # The first item in each line is the browser type.  The second
    # item is the version.  The remainder are patterns to search for,
    # and if the version is 0, we use the first number we can find
    # after the found text.

    # Find some spiders at (http://www.customcover.com/spiders.html)
    # and (http://www.jafsoft.com/misc/opinion/webbots.html).

    # Find a list of user agents for phones / PDAs at
    # (http://www.allnetdevices.com/faq/useragents.php3)
    
    # Cisco uses "public" and "internal" in the user-agent field.
    ['WebTV', 0, 'WebTV'], # They put WebTV *and* MSIE 2.0
    ['AOL', 0, '; AOL'], # AOL overrides MSIE-ness
    ['MSIE-DigExt', 0, 'DigExt'], # They put DigExt and MSIE 5.0
    ['MSIE', 0, 'MSIE', 'Microsoft Internet Explorer'],
    ['Perl', 0, 'LWP::Simple', 'lwp-trivial', 'libwww-perl'],
    ['WWW::Search', 0, 'WWW::Search'],
    ['LibWWW', 0, 'libwww'],
    ['Lynx', 0, 'Lynx'],
    ['"lynx" fake', 1, 'lynx'], # lowercase
    ['Sherlock', 0, 'Apple Find', 'URL Access', 'URL_Access',
     'Accs URL', 'Accs_URL'],
    ['SOFTWING_TEAR_AGENT', 1, 'SOFTWING_TEAR_AGENT'],
    ['Hungry Minds', 1, 'Hungry Minds'],
    ['Python', 0, 'Python'],
    ['GNU Wget', 0, 'Wget'],
    ['Elaine', 0, 'Elaine'],
    ['ProxiNet', 0, 'ProxiNet', 'Proxinet'],
    ['MetaCrawler', 0, 'MetaCrawler'],
    ['EmailSiphon', 0, 'EmailSiphon'], # Email harvesting program
    ['ExtractorPro', 0, 'ExtractorPro'], # Email harvesting program
    ['EmailWolf', 0, 'EmailWolf'], # Email harvesting program??
    ['Go!Zilla', 0, 'Go!Zilla'], # Downloading crawler
    ['SAPO', 1, 'SAPO/Google Search'],
    ['PHP', 0, 'PHP'],
    ['WIAGENT', 0, 'WIAGENT'], # Sending &sa=Google+Search
    ['iCab', 1, 'iCab/Pre', 'iCab'],
    ['infoGIST', 0, 'infoGIST'], # Client side metasearch called infoFinder (www.infogist.com)
    ['AnswerChase', 0, 'AnswerChase'], # Some search technology
    ['Links', 0, 'Links ('], # Yes, Links is a real browser != Lynx
    ['Cyberdog', 0, 'Cyberdog'],
    ['France Cybermedia Java Client', 1, 'France Cybermedia Java Client'],
    ['Opera', 0, 'Opera'],
    ['Copernic', 0, 'Mozilla/3.0 (Win95; I)', 'Mozilla/3.0 (compatible; Copernic)', 'Mozilla/3.0 (compatible)'], # Windows metasearch client, TODO: we use a client name now, not user agent
    ['libghttp', 0, 'libghttp'],
    ['Lotus Notes', 0, 'Lotus'],
    ['infisearch', 0, 'infisearch'], # Server side metasearch, www.infinisearch.net
    ['Internet Explorer fake', 0, 'IE4'],
    ['fetch', 0, 'fetch/'],
    ['Bogus Mozilla', 1, 'Mozilla/3.Mozilla/2'],
    ['Crescent', 0, 'Crescent Internet ToolPak HTTP OLE Control'],
    ['AvantGo', 0, 'AvantGo'],
    ['Konqueror', 0, 'Konqueror'],
    ['Mosaic', 0, 'Mosaic'],
    ['SavvySearch', 1, 'SavvySearch'],
    ['Promotion-Pro', 0, 'Promotion-Pro'],
    ['MetaGopher', 0, 'METAGOPHER'],
    ['parallel-crawler', 0, 'parallel-crawler'],
    ['htdig', 0, 'htdig'], # Some sort of search engine, I think.
    ['Dreamcast [ja]', 0, 'DreamPassport'],
    ['Dreamcast [en]', 0, 'Planetweb'],
    ['Arachne', 0, 'Arachne'], # http://home.arachne.cz/ 
    ['ANTFresco', 0, 'ANTFresco'], # http://www.ant.co.uk/prod/inetbroch/ 
    ['HotJava', 0, 'HotJava'],
    ['BeOS NetPositive', 0, 'NetPositive'],
    ['WebFerret', 0, 'WebFerret'], # They claimed they would identify themselves 9/15/00
    ['Emacs-W3', 0, 'Emacs-W3'],
    ['MSProxy', 0, 'MSProxy'],
    ['javElink', 0, 'javElink'],
    ['curl', 0, 'curl'],
    ['RepoMonkey', 0, 'RepoMonkey'], # Used by hungryhippo.com, or backflip.com
    ['IM4U', 1, 'IM4U'], # ???
    ['QNX Voyager', 1, 'QNX Voyager'],
    ['AmigaVoyager', 0, 'AmigaVoyager'],
    ['Browser X', 1, 'Browser X'], # www.entera.com caching proxy???
    ['Java', 0, 'JDK', 'java', 'Java'],
    ['I-Opener', 0, 'I-Opener'],
    ['IZPSd', 0, 'InfoZoid.com meta-search'], # 205.177.76.102
    ['OmniWeb', 0, 'OmniWeb'],
    ['RPT-HTTPClient', 0, 'RPT-HTTPClient'],
    ['IBM WebExplorer', 0, 'WebExplorer'],
    ['Inforian Quest', 1, 'Inforian Quest'],
    ['Proxomitron', 1, 'SpaceBison'],
    ['RPT-HTTPClient', 0, 'RPT-HTTPClient'],
    ['AcoiRobot', 0, 'AcoiRobot'],
    ['askOnce', 0, 'askOnce'], # (V1.5alpha; Xerox Corp; k-support@mkms.xerox.com; Aug 2000)
    ['HomePageSearch', 0, 'HomePageSearch'], # (hpsearch.uni-trier.de)
    ['WebCompass', 0, 'WebCompass'],
    ['Googlebot', 0, 'Googlebot'],
    ['Slurp (Inktomi bot)', 0, 'Slurp'], # Inktomi bot
    ['Scooter (AltaVista bot)', 0, 'Scooter'], # AltaVista bot
    ['Architext (Excite bot)', 0, 'Architext'], # Excite bot
    ['Lycos_Spider', 0, 'Lycos_Spider'], # Lycos bot
    ['Sidewinder (Infoseek)', 0, 'Sidewinder'], # Infoseek bot
    ['NorthernLight bot', 0, 'Gulliver'], # Northern Light bot
    ['GentleSpider', 0, 'GentleSpider'], # Seems to be from AT&T Research (Amit Singhal??)
    ['PortalJuice bot', 0, 'PJspider'],
    ['DWII-QServer', 0, 'DWII-QServer'],
    ['Teleport Pro', 0, 'Teleport Pro'],
    ['FetchAgent', 0, 'FetchAgent'],
    ['DoCoMo', 0, 'DoCoMo'], # Phone
    # 'Nokia' is not in the list because we want to know _which_ Nokia
    # phones.  But why?
    ['Nokia', 0, 'Nokia7110', 'Nokia6210', 'Nokia7160', 'Nokia3330'], # Phone
    ['J-PHONE', 0, 'J-PHONE'],
    ['EricssonT20', 0, 'EricssonT20'], # Phone
    ['Mitsu', 0, 'Mitsu'], # Phone
    ['WebSauger', 0, 'WebSauger'], # Some offline browsing bot
    ['UP.Browser', 0, 'UP.Browser', 'UP.Link', 'UP'], # Generic phone
    
    ['ColdFusion', 0, 'ColdFusion'],
    ['CodeChecker', 0, 'CodeChecker'],
    ['Rover', 0, 'Rover'],
    ['convert4', 0, 'convert4'],
    ['West Wind Web Connection', 0, 'West Wind Web Connection'],
    ['WhatsUp_Gold', 0, 'WhatsUp_Gold'],
    ['Dialer 2000', 0, 'Dialer 2000'],
    ['spybot', 0, 'spybot'],
    ['MonGoogle', 0, 'MonGoogle'], # jreese's monitoring script
    ['Keynote', 0, 'Keynote-Perspective'], # external monitoring
    ['CA Web Response', 0, 'CA Web Response Monitor'], # external monitoring
    ['mon.d/http.monitor', 1, 'mon.d/http.monitor'], # external monitoring???
    ]

# These are the operating systems along with aliases to look for
_OPERATING_SYSTEMS = [
    # The first item is the OS name we'll return.  All are patterns to look for.
    ['Windows95', 'Win95', 'Windows 95', 'Windows 4'],
    ['Windows98', 'Win98', 'Windows 98'],
    ['Windows2000', 'Windows NT 5.0'],
    ['WindowsXP', 'Windows NT 5.1'],
    ['WindowsNT', 'WinNT', 'Windows NT'],
    ['Macintosh', 'Mac'],
    ['OS/2'],
    ['Netbox', 'NetBox'],
    ['Linux', 'linux'],
    ['IRIX', 'Irix'],
    ['HP-UX'],
    ['BSD'],
    ['OSF'],
    ['AIX'],
    ['SCO'],
    ['NCR'],
    ['SunOS', 'Solaris'],
    ['VAX', 'VMS'],
    ['Palm', 'ProxiNet'],
    ['X11', 'UNIX'],
    ['Netpliance'],
    ['Amiga'],
    ['WebTV'],
    ['Microsoft Windows 3.x', 'Win16'],
    ['Other Microsoft Windows', 'Win'],
    ]

def parse_user_agent(user_agent): # TODO: this could be in C, taking 1800/29000 ticks
    "Return (browsername, browserversion, os)"

    # Avoid the whole bit if it's a simple bot ..
    if not user_agent: return ('(empty)', 0, '(empty)')
    
    # Avoid the expensive test by checking the most common cases first
    if user_agent[:29] == 'Mozilla/4.0 (compatible; MSIE':
        # It's Internet Explorer
        try: version = float(user_agent[30:33])
        except ValueError: version = 0
        rest = user_agent[33:]
        msie = 'MSIE'
        if string.find(rest, 'AOL') >= 0:
            # It's the AOL version of MSIE.  It may also be DigExt but
            # we know and care about AOLness whereas we don't know
            # (and care less about) DigExtness.
            msie = 'MSIE-AOL'
        elif string.find(rest, 'DigExt') >= 0:
            # This is an unknown variant of MSIE
            msie = 'MSIE-DigExt'
            
        index = string.find(rest, 'Windows ')
        if index >= 0:
            tag = rest[index+8:index+10]
            if tag == '95':
                return (msie, version, 'Windows95')
            if tag == '98':
                return (msie, version, 'Windows98')
            if tag == 'NT':
                nt_version =  rest[index+11:index+14]
                if nt_version == '5.0':
                    return (msie, version, 'Windows2000')
                if nt_version == '5.1':
                    return (msie, version, 'WindowsXP')
                return (msie, version, 'WindowsNT')
        if string.find(rest, 'Mac') >= 0:
            return (msie, version, 'Macintosh')
        # Else, fallthrough to general browser detection code

    # Figure out the operating system, and store both the operating
    # system name and the position in the string where we found it.
    # We'll use this later in a Mozilla detection hack.
    for kinds in _OPERATING_SYSTEMS:
        found = 0
        for search_text in kinds:
            os_index = string.find(user_agent, search_text)
            if os_index >= 0:
                found = 1
                break
        if found: 
            operating_system = kinds[0]
            break  # Take the first match
    else:
        operating_system = 'Unknown'
        os_index = len(user_agent)

    # Special cases
    if user_agent == 'Mozilla' or user_agent == 'Mozilla/4.0':
        return 'Bogus Mozilla', 0, 'Unknown'
    
    # We try to handle the common case of Netscape browsers by looking
    # to see if there are any periods (usually meaning a version
    # number) anywhere after the Mozilla/ version number. Ew.  This
    # hack doesn't always work because inside the parens could be the
    # operating system's version number.  Oh well.
    found_opera = string.find(user_agent, 'Opera') >= 0
    if (user_agent[:8] == 'Mozilla/' and
        not (0 <=
             string.find(user_agent, '.', 1+string.find(user_agent, '(') or 12)
             <= os_index)):
        # This doesn't work for WebTV, Opera
        if (string.find(user_agent, 'WebTV') < 0 and
            not found_opera and
            string.find(user_agent, 'Mozilla', 8) < 0 and
            string.find(user_agent, 'SavvySearch') < 0):
            # Return Netscape right here, and don't perform the really expensive test
            try: version = float(user_agent[8:11])
            except ValueError:
                #warning('Warning: Mozilla version unparsable:', `user_agent`)
                version = 0
            return 'Netscape', version, operating_system
        
    # Figure out what browser type the user has by going through
    # them all.  Unfortunately we can't handle the other common
    # case (Netscape/Navigator, Netscape/Communicator) because a
    # lot of sites were doing browser detection by looking at the
    # user agent, so MSIE, Opera, etc., started to lie and claim
    # they were Mozilla.  So now we can only tell if it's Mozilla
    # by looking at all the oddball cases first.  Slow.  Ew.
    i = string.find(user_agent, ')')
    if i < 0 or found_opera: user_agent_initial = user_agent
    else: user_agent_initial = user_agent[:i]

    for kinds in _BROWSER_TYPES:
        found = 0
        for i in range(2, len(kinds)):
            j = string.find(user_agent_initial, kinds[i])
            if j >= 0:
                browser, version = kinds[:2]
                found = 1
                if version == 0:
                    # Figure out the version from the string
                    m = re.match(r'[/\s]*(\d\d?\.?\d?)',
                                 user_agent_initial[j+len(kinds[i]):])
                    if m: version = float(m.group(1))
                break
        if found: break
    else:
        browser, version = 'Unknown', 0
        # We've gone through the expensive test and now we're back to
        # thinking it might be Netscape.
        if user_agent[:8] == 'Mozilla/':
            browser = 'Netscape'
            try: version = float(user_agent[8:11])
            except ValueError: pass
            
    return browser, version, operating_system

def parse_cookie(cookie):
    # TODO: this function hasn't really been written
    if 16 <= len(cookie) <= 17:
        # GWS has stripped out the ID= from the cookie
        cookie = 'ID=' + cookie
        # 14-Mar-2000: Ben S and Amit have agreed that the cookie
        # should have additional fields, comma separated.

    # TODO: parse out the comma separated fields and store a parsed
    # cookie somewhere, OR just have functions for parsing the cookie
    # later, so that we save time when we don't need this information.
    return cookie


# Try importing the C utilities module and using its faster functions.
# If that doesn't work, use the Python fallbacks.
try:
    import _libgwslog
    is_valid_accept_language   = _libgwslog.is_valid_accept_language
    is_valid_language_restrict = _libgwslog.is_valid_language_restrict
    parse_accept_language      = _libgwslog.parse_accept_language
    parse_query_string         = _libgwslog.parse_query_string
    unquote                    = _libgwslog.unescape
    parse_logline_basic        = _libgwslog.parse_logline_basic
except ImportError:
    is_valid_accept_language   = fallback_is_valid_accept_language
    is_valid_language_restrict = fallback_is_valid_language_restrict
    parse_accept_language      = fallback_parse_accept_language
    parse_query_string         = fallback_parse_query_string
    unquote                    = urllib.unquote
    parse_logline_basic        = fallback_parse_logline_basic
