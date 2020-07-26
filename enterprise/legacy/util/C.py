#!/usr/bin/python2.4
# This file contains some constants

import sys
from google3.enterprise.tools.C_base import *

###########################################################################
#
# Misc constants
#
RUNCONFIGDIR_DIRNAME = "config"
RECONFIGURE_COMMAND = "%s/local/google/bin/secure_script_wrapper -p2 "\
                      + "/usr/local/sbin/reconfigure_net.py";

# serve service command template with ignore_init_state
SERVE_SERVICE_COMMAND = ('. %(bashrc)s && '
        'cd %(home)s/local/google3/enterprise/legacy/scripts/ && '
        '%(home)s/local/google/bin/secure_script_wrapper -p2 '
        '%(home)s/local/google3/enterprise/legacy/scripts/serve_service.py '
        '%(home)s %(action)s --ignore_init_state ')

# serve service command suffix
SERVE_SERVICE_COMPONENTS = '--components=%s'
GFS_COMPONENTS = 'gfs_main,gfs_chunkserver,sremote_server'

# From LogHandler.java:
SEARCH_ALL_COLLECTIONS = 'all.collections'
# For those queries without site parameter.
# We use '#' as it is not allowed in a collection name and
# is not a valid collection parameter (. and | being the only two)
# so the special name won't conflict with a real collection.
NO_COLLECTION = 'no#collection'

###########################################################################
#
# Init States
#
FRESH = "FRESH"
CONFIG_FILES_INITIALIZED = "CONFIG_FILES_INITIALIZED"
INITIALIZED = "INITIALIZED"

###############################################################################
#
# License information keys
#
UNEXPECTED_ERROR         = "UNEXPECTED_ERROR";
WRONG_LICENSE_FORMAT     = "WRONG_LICENSE_FORMAT";
WRONG_BOX_ID             = "WRONG_BOX_ID";

LICENSE_PARSING_ERRORS   = [UNEXPECTED_ERROR,
                            WRONG_LICENSE_FORMAT,
                            WRONG_BOX_ID,
                            ]

# license status code
LIC_OK =                   0

LIC_OTHERS =               1
LIC_PARSE =                2
LIC_OUTDATED =             3
LIC_INVALID =              4
LIC_WRONG_FORMAT =         5
LIC_WRONG_BOX_ID =         6
LIC_TOOMANYCOLLECTIONS=    7
# warning but OK
LIC_WARNING_SMALLER_THAN_LIMIT= 8
LIC_WARNING_LESS_PAGE_NEW_LIC = 9

# within these many days, show left serving time in red
ENT_LICNESE_WARINING_DAYS = 10

###############################################################################
# The constants in this section must match with the ones in C.java.

# Query expansion status codes
QUERY_EXP_STATUS_OK          = 0
QUERY_EXP_STATUS_NEEDS_APPLY = 1
QUERY_EXP_STATUS_PROCESSING  = 2
QUERY_EXP_STATUS_ERROR       = 3

# Query expansion file types
QUERY_EXP_FILETYPE_SYNONYMS  = 0
QUERY_EXP_FILETYPE_BLACKLIST = 1

# Query expansion validation error codes
# Make sure these correspond to the values in ValidationErrorCode.java
QUERYEXP_ENTRY_EXISTS            = 439
QUERYEXP_UNABLE_TO_CREATE_ENTRY  = 440
QUERYEXP_ENTRY_BAD_NAME          = 441
QUERYEXP_LICENSE_LIMIT           = 442
QUERY_EXP_VALIDATION_WHITESPACE  = 443
QUERY_EXP_VALIDATION_OPERATOR    = 444
QUERY_EXP_VALIDATION_EMPTY_LEFT  = 445
QUERY_EXP_VALIDATION_EMPTY_RIGHT = 446
QUERY_EXP_VALIDATION_SET_SYNTAX  = 447
QUERY_EXP_VALIDATION_SET_TOO_BIG = 448
QUERY_EXP_VALIDATION_INVALID_CHAR = 449
QUERY_EXP_VALIDATION_FILE_EMPTY = 451

###############################################################################
CRAWLQUEUE_STATUS_UNKNOWN  = 0  # First initialized
CRAWLQUEUE_STATUS_PENDING  = 1  # Crawl Queue entry registered.
                                # Crawl Queue is being captured.
CRAWLQUEUE_STATUS_COMPLETE = 2  # Crawl Queue caption complete.
CRAWLQUEUE_STATUS_FAILURE  = 3  # Crawl Queue caption failed.

# return codes for crawlqueue_handler. Except CRAWLQUEUE_OK, all others should
# match with those constants with same name defined in ValidationErrorCode.
CRAWLQUEUE_OK = 0
CRAWLQUEUE_INTERNAL_ERROR = 286
CRAWLQUEUE_CAPTION_FAILED = 287
CRAWLQUEUE_NAME_NOT_FOUND = 288
CRAWLQUEUE_HOST_NOT_FOUND = 289
CRAWLQUEUE_PAGE_NOT_FOUND = 290
CRAWLQUEUE_NAME_EXISTS    = 291
CRAWLQUEUE_INCOMPLETE     = 292
CRAWLQUEUE_TOO_MANY       = 398
CRAWLQUEUE_IS_RUNNING     = 399

# return codes for log_handler. Except REPORT_OK, all others should match with
# those constant with same name defined in ValidationErrorCode.
REPORT_OK = 0
REPORT_INTERNAL_ERROR     = 265
REPORT_TYPE_UNKNOWN       = 266
REPORT_NAME_EXISTS        = 267
REPORT_NAME_NOT_FOUND     = 268
REPORT_INCOMPLETE         = 269
REPORT_ALREADY_FINAL      = 270
REPORT_GENERATION_FAILED  = 271
REPORT_LIST_TOO_MANY      = 272
REPORT_ALREADY_COMPLETE   = 402
CRAWLQUEUE_INVALID_HOST   = 403

# These constants are used for ContentTypeStats page, their values should be
# identical to those in C.java
CONTENT_TYPE_NO_SORTED = 'unsorted'
CONTENT_TYPE_MIME_TYPES = 'mimetypes'
CONTENT_TYPE_NUM_FILES = 'numfiles'
CONTENT_TYPE_AVERAGE_SIZE = 'avgsize'
CONTENT_TYPE_TOTAL_SIZE = 'totalsize'
CONTENT_TYPE_MIN_SIZE = 'minsize'
CONTENT_TYPE_MAX_SIZE = 'maxsize'

# Scoring adjustment error codes. The values must match the ones in
# ValidationErrorCode.
SCORING_ADJUST_BAD_URL_PATTERNS = 437
SCORING_ADJUST_DUPLICATE_PATTERNS = 450
SCORING_ADJUST_BAD_PAIRS = 463
SCORING_ADJUST_DUPLICATE_PAIRS = 464
SCORING_ADJUST_POLICY_MISSING = 465

# Error codes for scoring adjust policy creation. Values should be
# identical to those in C.java.
SCORING_ADJUST_POLICY_CREATE_OK = 0
SCORING_ADJUST_POLICY_EXISTS = 1
SCORING_ADJUST_POLICY_BAD_NAME = 2
SCORING_ADJUST_LICENSE_LIMIT = 3

###############################################################################

# Milliseconds in a day
DAY_MILLISECONDS = 24*60*60*1000

LONG_MIN_VALUE = -0xffffffffffffffffL

###############################################################################
#
# Email related
#
ENTERPRISE_MESSAGE_FROM = "enterprise@google.com"

###############################################################################
#
# The etc config file
#
ETC_SYSCONFIG = "/etc/sysconfig/enterprise_config"

# Default collection and frontend
DEFAULT_COLLECTION = "default_collection"
DEFAULT_FRONTEND = "default_frontend"

###############################################################################

if __name__ == "__main__":
  sys.exit("Import this module")
