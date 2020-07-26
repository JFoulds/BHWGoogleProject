#!/usr/bin/python2.4
#
# Copyright 2002 onwards Google Inc
#
# This file contains private members for servertype.py.
# It is separated for easy editing.
# Do not use these directly but use the accessor methods
# in servertype.py.
#
# A new server can be registered with the system by the following steps.
#
# 1) Make sure you have registered ports in //depot/eng/ports.
# 2) Add the servertype to the _SERVER_TYPE_PORTS_ below.
# 3) Complete configuration in _SERVER_TYPE_PROPERTIES_ below.
#    See the defaults below for documentation on flags.
# 4) Look at other data structures and see if you need to add the server
#    to any of the data structures below.
# 5) Add restart functions to servertype_{prod,crawl}.py.
# 6) Add your default variables to enterprise/legacy/config/config.default
# 7) Customize your variables at run-time in
#    enterprise/legacy/adminrunner/entconfig.py
# 8) Add your server to the constraint_general dictionary in entconfig.py
#
# This is a configuration file - global constants only.

#
# Mapping from server type name to min and max ports.
#

_SERVER_TYPE_PORTS_ = {

  #'name' :  (minport, maxport+1)
  'hosting_server':          (3300, 3301),
  'mysql':                   (3306, 3307),
  'circadia':                (3310, 3319),
  'imagedoc':                (3500, 3800),
  # the following ports for the GFS components are stil needed for
  # the GSAs and cannot be reused.
  'gfs_main':              (3830, 3836),
  'gfs_main_shadow':       (3836, 3838),
  'gfs_main_replica':      (3838, 3840), # temporary hack
  'gfs_chunkserver':         (3840, 3850),
  'rfserver':                (3851, 3900),
  # Don't reuse concentrator ports until configurator.RemoveLegacyComponents()
  # is removed.
  'concentrator':            (3901, 3902),
  'tcp_monitor':             (3906, 3907),
  'ispmon':                  (3908, 3909),
  'indexing_status_server':  (3909, 3910),
  'tcp_aggregator':          (3910, 3911),
  'netmon' :                 (3920, 3921),
  'netgraph' :               (3921, 3922),
  'snmpcon':                 (3923, 3924),
  'keycollector':            (3929, 3930),
  'gkeyd':                   (3930, 3931),
  'keyserver':               (3931, 3932),
  'eval_monitor':            (3932, 3933),
  'ssh_port_forwarder':      (9209, 9210),
  'am_latency_monitor':      (3950, 3951),
  # Don't reuse GEMS ports until configurator.RemoveLegacyComponents()
  # is removed.
  'gemsreporter':            (3960, 3965),
  'gemsalerter':             (3965, 3970),
  'gemscollector':           (3970, 3980),
  'monitor':                 (3990, 3992), # NOT SERVERTYPE, just to reserve port
  'svs':                     (3999, 4000),
  'index':                   (4000, 4300),
  'doc':                     (5000, 5300),
 #'docserver':               (5000, 5300), # runcrawler wants mapname==binaryname
  'link':                    (5600, 5900),
  'lexserver':               (5900, 6200),
  # chubby 6200, 6201, 6202, 6203 replica port 6205, 6207 snapshot port 6206, 6208
  'chubby':                  (6200, 6209),
  'cache':                   (6600, 6900),
  'related':                 (6900, 7200),

  'entfrontend':             (7800, 7810),
  'enttableserver':          (7880, 7882),
  'authzchecker':            (7882, 7886),
  'connectormgr':            (7886, 7890),
  'content_ad_shard':        (7900, 8000),
  'apache':                  (8000, 8001),
  'tomcat':                  (8005, 8010),
  'web':                     (8082, 9000), # some services (i.e. tomcat/rexd are below this number), web also takes port 80.
  'toolbar':                 (9000, 9001),
  'forwardmap':              (9010, 9020),
  'delivery_status_update':  (9031, 9081),
  'sremote_server':          (9081, 9083),
  'onebox':                  (9300, 9320),
  'spellmixer':              (9328, 9330),
  'stocksdaemon':            (9340, 9350),
  'odpcat':                  (9350, 9354),
  'mixer':                   (9400, 9402), # enterprise needs two ports for this
  'directory':               (9404, 9405),
  'directorydoc':            (9405, 9406),
  'forwardlogserver':        (9406, 9407),
  'categoryserver':          (9408, 9409),
  'anchorserver':            (9409, 9410),
  'ancestordupsserver':      (9410, 9411),
  'ffe':                     (9412, 9413), # and also port 80
  'workqueue-main' :       (9413, 9414),
  'workqueue-subordinate' :        (9414, 9415),
  'evaldupidserver':         (9415, 9416),
  'mergeserver_status':      (9417, 9418),
  'simple_httpd':            (9418, 9420), # web server for testing
  'balancer':                (9420, 9430),
  'transbal':                (9430, 9440),
  'vmwebserver':             (9440, 9443), # enterprise version-manager webserver
  'workschedulerserver':     (9443, 9446),
  'gvps':                    (9447, 9448), # google viewer proxy server; also port 80
  'qrewrite':                (9448, 9450), # enterprise needs two ports for this
  #'irarchiver':              (9449, 9450), # this one stolen for qrewrite
  'headrequestor':           (9450, 9453),
  'named':                   (9479, 9480), # named stats
  'pyserverizer':            (9486, 9490),
  # 9990 - 9999:   automated unit/regression tests
  'ent_fedroot':             (9999, 10001),
  'oneboxdefinition':        (10080, 10081),
  'oneboxdefinitionstubby':  (10081, 10082),
  # Enterprise Onebox backend server
  'oneboxenterprise':        (10094, 10096),
  'prmapsgenerator':         (10100, 10110), # convert prvectors to prmaps
  'prconsole':               (10110, 10111), # lookup pr history, top urls, etc
  'historytable_generator':  (10111, 10112), # generate history tables
  'api':                     (10113, 10114),
  'clustering_server':       (10200, 10202), # enterpise clustering server
  'registryserver':          (12345, 12347),
  'index2':                  (14000, 14300),
  # Ports for crawler and indexing components servers
  'supergsa_main':           (18000, 18100), # crawl + index binary for supergsa
  'prserver':                (19600, 19700), # For pagerank lookups
  'urlscheduler':            (19700, 19780),
  'config_manager':          (19780, 19790),
  # Don't reused fixer ports until configurator.RemoveLegacyComponents()
  # is no longer necessary.
  'fixer':                   (19790, 19800),
  'feeder':                  (19800, 19900),
  'feedergate':              (19900, 19930),
  'hlserver':                (19930, 19950),
  'urlfiledataserver':       (19950, 20000),
  'urlmanager':              (20000, 20500),
  'urlserver':               (20500, 20600),
  'global_lca_link':         (20600, 20650),
  'global_hostid2ip':        (20650, 20660),
  'hostid2ip_server':        (20660, 20670),
  'siteid2data_server':      (20670, 20680),
  'linkdrop_server':         (20700, 20750),
  'urlfp2siteid_server':     (20750, 20800),
  'bot':                     (21000, 21100),
  'cookieserver':            (21100, 21200),
  'fsgw':                    (21200, 21300),
  'contentfilter':           (21500, 21600),
  'lca_resharder':           (21660, 21670),
  'directorydatabuilder':    (21670, 21680),
  'urlmanager_log_rewriter': (22500, 22600),
  'urllog_hoststats_collector': (22602, 22603),
  'crawldiagnostics_fe':     (22603, 22604),
  'pageranker':              (23000, 23500),
  'pr_main':                 (23500, 23800),
  'dnscache':                (24000, 24100),
  'dupserver':               (24500, 24600),
  'rtdupserver':             (24600, 24700),
  'docidserver':             (25000, 25200),
  'historyserver':           (29000, 29500), # history for reuse crawl
  'urltracker_server':       (30000, 30100),
  'tracker_gatherer':        (30100, 30200),
  'base_indexer' :           (30700, 30800),
  'daily_indexer' :          (30800, 30900),
  'rt_indexer' :             (30900, 31000),
  'rtmain':                (31000, 31300),
  'rtsubordinate':                 (31300, 31600),
  'global_link' :            (32000, 32100),
  'global_anchor' :          (32100, 32200),
  'microsharder':            (32400, 32500),
  'urlhistory_processor' :   (32500, 32600),
  'rtmap_resharder':         (32600, 32700),
  'caanchor_server':         (32700, 32750),
  #####
  # WARNING! ports over 32768 can also be used by kernel for ephemeral ports!
  #####
  'microsharder_splitter':   (32800, 32900),
  'microsharder_merger':     (32900, 33000),
  'urltracker_indexlogs':    (33100, 33200),
  'gatherer_indexlogs':      (33200, 33300),
  'bigindexfilterbuilder':   (33300, 33400),
  'bigindexfiltermerger':    (33400, 33500),

  #
  # Virtual servers - they use no real ports
  #
  # Production scripts:
  'jobrunner'   :            (80000, 80001),
  'fixer_prod'  :            (80001, 80002),
  'babysitter'  :            (80002, 80003),
  'mcp'         :            (80003, 80004),
  'coloc_main' :           (80004, 80005),
  'gemsrelay'   :            (80005, 80006),

  'crawlchecker'  :          (90000, 90500),
  'crawlbabysitter':         (90500, 90501),
  'indexer'       :          (100000, 100500),
  'lexicon'       :          (100500, 101000),
  'sorter'        :          (101000, 101500),
  'genurl'        :          (101500, 102000),


  # rippersubordinates need a very big port range
  'rippersubordinate'   :          (200000, 202000), # For distributed ripping

  # history info for enterprise
  'enthist'               :  (325500, 326000),
  # process urls logs for use with siteinfo
  'indexlogs'    :           (327500, 327600),
  # historytable generator
  'genhistorytable'       :  (327600, 327700),
  'historytablearchive'   :  (327700, 327800),

  # the next three are temporary - till we get GFS up
  'rfserver_bank':           (328000, 328500),
  'rfserver_replica_bank' :  (328500, 329000),

  # TODO clean the next two if they are not necessary
  # (when BART is live)
  # backup repository used to store pristine copy of storeservers
  'repository_backup'     :  (333000, 333500), # storeserver double-replicas
  # backup data generated by rippers
  'ripper_backup'         :  (333500, 334000),

}


#
# Default Server Type Properties.  If you do not set a servertype
# property, it will default to what is specified below.
#

_ACK_LEN_ = len('ACKGoogle')
_AD_TIMEOUTS_ = (20, 20, 45, 60)

_SERVER_TYPE_DEFAULTS_ = {

  # Set to 1 if this server supports multiple shards.
  'is_sharded' : 0,

  # Set to 1 if this server supports multiple levels (each level takes
  # up to 'level_size' ports - i.e. level1 = portbase + level_size).
  #
  # WARNING: We are trying to deprecate the use of levels COMPLETELY.
  # If you are adding a new type and feel you need levels or
  # you are changing a type from not leveled to leveled, please speak
  # to a production team member first.
  'is_leveled' : 0,

  # port distance between 2 levels. Normally, levels on any type use
  # 100 ports, with the exception of a few, very special (and very
  # rare) types that use a different value (eg. balancers).
  #
  # WARNING: Changing this once a servertype is in use requires
  # ensuring that all configs are properly updated.   Also, we're
  # trying to deprecate the use of levels.
  'level_size' : 100,

  # Does this server support google2 arguments?
  # TODO: this is only used by servertype_crawl.py.
  'supports_google2_args' : 1,

  # Directory where the binary resides, relative to MAINDIR.  The default
  # value is appropriate for binaries that live in //depot/google2/bin.
  # TODO: this is only used by servertype_crawl.py.
  'relative_bin_dir' : 'bin',

  # The name of the binary for this server.  Defaults to the
  # server name if not specified.  Only specify if different.
  'binary_name' : None,

  # The names of binary files that this server requires to run.
  # Defaults to the binary name if not specified.  Only specify if different.
  'binary_files' : None,

  # If the binary files of this servertype are always the same as another
  # servertype's binary files, that servertype may be specified below.
  # Note that it is an error to specify both binary_files and
  # binary_files_inherit. Format: 'mtype'
  'binary_files_inherit' : None,

  # To distribute the binary files of an additional server type
  # along with this server type's binary files, specify the names
  # of the additional servertypes in a list. Format: ['mtype', ... ]
  'binary_files_addl' : None,

  # Directory to locate binary.  If set to None, defaults to /root/google/bin.
  'bin_dir' : None,

  # Run directory for the binary.  If set to None, defaults to /root/google/bin.
  'run_dir' : None,

  # User to run binary as.  If set to None, defaults to root.
  'binary_user' : None,

  # Group to run binary as.  If set to None, defaults to primary group of user.
  'binary_group' : None,

  # User that babysitter sshes to machine as.
  'ssh_user' : None,

  # This is a function that returns a shell command that starts
  # up the server.  The function prototype should be:
  #   cmd restart(config, host, port)
  'restart_function' : None,

  # This is a function that returns a shell command that kills
  # the server.  Generally you shouldn't specify this
  # since we'll use the standard kill by binary name and port
  # (GetKillSigOnPortDelay).  The function prototype should be:
  #   cmd kill(port, delay, signal_type)
  'kill_function' : None,

  # If the default kill function is used, this specifies the delay
  # between the kill -SIG and the kill -9 used to make sure the
  # server is dead.
  'kill_delay' : 1,

  # If the default kill function is used, this specifies the type
  # of signal to used to kill server.
  'kill_signal' : 'TERM',

  # Some servers from crawl want to use the killall which is
  # dangerous since it kills all servers with binary name regardless
  # of port.  This should be taken out eventually so ignore this flag.
  'kill_noport' : 0,

  # The names of binaries that need to be killed on restart. Defaults
  # to 'binary_name' if not specified Only specify if different.
  'kill_binaries' : None,

  # This is the command to send to a server to cause it to checkpoint.
  # If this is present, a kill in the babysitter will generally
  # ask for a checkpoint from the server first.
  'checkpoint_info' : None,

  # Set to 0 if server type does not have a datadir.
  'has_datadir' : 1,

  # Set to 0 if server type does not support data versions.  This
  # results in not setting the dataversion field in the shardinfo specs
  # when this servertype serves as a backend.  Note that dataversions
  # are also not set if the servertype does not have a datadir.
  'supports_dataversion' : 1,

  # Whether the server supports an HTTP status page or not.
  'supports_http_statusz' : 0,

  # statusz port, if special. We default to base port otherwise or to
  # balancer port (if balancer type)
  'statusz_port' : 0,

  # The port base of this server when it serves as a backend.
  # For example, mixers are at 9400 but they serve on 4000 to gws.
  # DO NOT USE THIS!
  'backend_port_base' : None,

  # Backend server sets that this server should talk to by default.
  # This should be a list in the format:
  #
  # [ { 'set' : <backend set name>,
  #     'tag' : <tag name>,
  #     'per_shard' : [0|1],
  #     'serve_as' : <servertype for rtservers to masquerade>,
  #     'numconn' : <number of connections to use>,
  #     'schedtype' : <type of scheduling to use>,
  #     'protocol' : <type of protocol to use>,
  #     'port_shift' : <shift port by this amount> }, ...
  #     'port_base' : <set port base to this value> }, ...
  # ]
  #
  # This structure assists in tracking server dependencies and
  # constructing backend argument strings.
  #
  # The set name should be in the form [coloc:][service:]setname.
  # For default backends generally the coloc and service should
  # be omitted.
  #
  # The tag name is an identifier that can be used to identify
  # backends of the same type that serve different purposes.
  # See config.indexindep for an example of this.
  #
  # Per_shard indicates that only servers of a corresponding
  # shard will be returned as backends (i.e. index -> hostid).
  #
  # Serve_as is for serves which masquerade as other types
  # such as rtsubordinates and rtmains.  When referenced as a backend
  # the server_as type will be used in constructing the backend
  # argument string.  Serve_as can also be used to masquerade
  # as another C++ servertype defined in serverflags.py but not
  # a true babysitter servertype.  For historical reasons, the
  # effect of these two is distinct with respect to the ports passed.
  # TODO: Make them consistent with respect to ports.  For the
  # gory details see serverlib._BackendPortOffset.  In a nutshell,
  # if you use a real servertype to 'serve_as', the ports will
  # be changed to the servertype's port range.  If it is not a real
  # servertype, the ports will remain the same as the original
  # servertype.
  #
  # Number of connections and scheduling policy can be set with
  # the 'numconn' and 'schedtype' fields to override any defaults
  # set below with the 'numconns' and 'schedtypes' maps.
  #
  # Protocol can be set to 'http' for servers that support this.
  #
  # This structure can be overriden in the SERVER_SETS dictionary.
  #
  'backends' : [],

  # Number of connections to backends specified by type.
  #
  # This map is of the form:
  #
  # { 'mtype' : num_conns, ... }
  #
  # It specifies the number of connections to use for a backend
  # of a particular type.
  #
  'numconns' : {},

  # Default number of connections to backend if not specified in above map.
  'dflt_numconn' : 3,

  # Scheduling policies specified by type to backends.
  #
  # This map is of the form:
  #
  # { 'mtype' : sched_policy, ... }
  #
  # It specifies the scheduling policy to use for a backend
  # of a particular type.  If mtype is 'default', then types
  # not found in the map will default to the value specified under 'default'.
  # Note that this may be overriden explicitly in the backends set
  # specifications with 'schedtype'.
  #
  'schedtypes' : {},

  # Default protocol to use for frontends to connect to this servertype.
  # This can be overriden using the backend set specification.
  'protocol' : None,

  # The interpreter to execute in order to start a server. For example, java
  # binaries (.jar files) may be executed by "/usr/bin/java" while python
  # binaries (.py files) may be executed by "/usr/bin/python" or
  # "/usr/bin/python2.4". Absolute path to the interpreter is required.
  #
  # You have to specify this if your server is executed by an interpreter. This
  # property is used by the function InterpretedServerExecutablePrefix and its
  # various wrapper functions, and they need this to contruct the correct
  # command prefix.
  #
  'interpreter' : None,

  # Tell the babysitter to frequently push files to this machine
  # Be careful, this will blow away /root/google
  'sync_from_babysitter' : 0,

  # Whether the datadir contains the port name.
  'datadir_has_port' : 0,

  #----------------------------------------------------------------------------
  # MONITORING SETTINGS
  #----------------------------------------------------------------------------

  # The string sent by the babysitter process to check that a server is alive.
  'request_info' : "",

  # For the babysitter, if response_len is set to 0, the server is
  # expected to return ACKgoogle, i.e. a NACKgoogle won't be accepted.
  # otherwise, server is considered good if its reply has
  # at least response_len characters.
  # NOTE: If you are setting response_len to 0, you shouldn't use
  # python event loop. Use --subprocess=monitor flag.
  'response_len' : 0,

  # Timeouts for each babysitter attempt to test server's liveness. We try to
  # get an answer from the server for as many times as we have
  # timeouts in this list (and obeying each timeout in turn). When
  # we run out of timeout values (and still did not get an
  # answer), the server is restarted.
  # This goes like this:
  # Send a query, wait for 20 seconds. If timeout, send the query
  # again and wait for 20 seconds. And if still timeout, send a
  # query and wait for 45 seconds. The total timeout before restart
  # is 85.
  'test_timeouts' : (20, 20, 45),

  # Some crawler servers cannot be babysat because of huge times off, even
  # when the server is fine (e.g. urlmanager). Override this property if
  # you don't want to have your server babysat in your config
  # ** NOTE: use with absolute care **
  'skip_babysitting' : None,

  # Connection method to find server data from server.
  # This is used by the concentrator to gather status info - valid
  # types are 'v', 'http', 'direct', 'connectonly'.
  # If you specify an unknown type the concentrator will default to
  # using the 'v' command.
  #
  # v : connects & issues a 'v' command, reads data ('ACKGoogle' terminated)
  #   and issues a 'c' command to close.
  #
  # http: connects and GETS /varz?output=text.
  #
  # direct : connects and expects data to be immediately read and then
  #   the connection closed.
  #
  # connectonly: only connects to the specified host/port - a connection
  #   by itself is considered success.
  #
  # NOTE: IF YOU CHANGE this for an existing servertype, please request
  # a concentrator restart to pick up the change.
  # Second NOTE: The concentrator needs a babysitter restart, not merely
  # a killall.
  'var_info_connection_type' : 'v',

  # Alert email addresses - comma separated string.  Used for GEMS.
  'alert_email' : None,

  # Alert pager addresses - comma separated string.  Used for GEMS.
  'alert_pager' : None,

  # whether this server should be monitored from another datacenter by GEMS.
  'external_monitor': 0,

  #----------------------------------------------------------------------------
  # SETUP SETTINGS
  #----------------------------------------------------------------------------

  # The setup operations that are to be performed on this server. Ops are:
  #
  #   'datadir' : only setup empty datadir (i.e. filesyncer, rtsubordinate, cache)
  #   'setup_prod' : run setup production (i.e. mixer, onebox)
  #
  # These can be set together in a list variable if more than one op is desired.
  # Right now these are mututally exclusive but this is for future expansion.
  'setup_ops' : None,

  # The type of kernel that this server uses.  Possible settings are:
  #
  #  None or 'default': any smp kernel.
  #  'prod24': 2.4 smp kernel.
  #  'index': require the index kernel on the machine.
  #  'web': require the web kernel on the machine.
  #
  # If kernels for servers on same host conflict (both not None and
  # not equal), server setup will fail for all servers on that host.
  'kernel' : None,

  # Server-specific script for install (if setup-production.py doesn't work)
  # this script should be in the form:
  # <scriptname> <config file> <server_spec>
  'setup_script' : None,

  # Free pool to pull from.  This is a list of owners.  Machines in the
  # free state owned by the given owner will be candidate replacements.
  # 'global' indicates the global free pool.
  'free_pool' : ['global'],

  # who to change the ownership to for the replaced machine
  # - if set to None, ownership is relinquished
  # - if set to 1, ownership of the config file is maintained
  # - if set to a string, ownership is attempted to be transfered to the
  #   specified owner.
  'replaced_machine_owner': None,

  # when a machine is replaced, state it is assigned to, the options are
  # free, freetest, suspect
  'replaced_machine_target_state' : 'freetest',

  # Files that need to be localized for each server type.
  #
  # This is of the form
  # [ { 'srcpath'    : <src path>
  #     'targetpath' : <target path>
  #     'files'      : <list of files relative to srcpath/targetpath>
  #   },
  #   ...
  # ]
  #
  # where,
  #    'srcpath':     relative source path for the main.  Default value ''.
  #                   This path is relative to GOOGLEBASE
  #    'targetpath':  relative destination path for servers. Default value ''.
  #                   For crawl, this path is relative to DATADIR.
  #    'files':       List of files relative to srcpath/targetpath.
  #                   Default ['*'] => everything in the source directory
  #
  # NOTE:
  #   - if a file is needed in multiple servers, they all must have
  #     the same srcpath and targetpath.
  #   - only crawl config is currently supported.
  #
  # TODO: need to extend to production world
  #
  'local_data_files' : [],

  # Data push paths (relative to googledata).
  'data_push_paths' : None,

  # Test to check whether data on the machine is acceptable.
  # TODO: gwsdatapusher currently doesn't respect this property.
  # so we'll need to merge this concept into that when it is
  # revamped.  Currently, gwsdatapusher hard-codes testing
  # only gwsen.  Do not augment use of this property until
  # gws datapusher is updated to respect it.
  'data_push_test': None,

  #----------------------------------------------------------------------------
  # RESTARTER SETTINGS
  #----------------------------------------------------------------------------

  # The following parameters control if and when restarts are triggered
  # by the restarter based on changes made to config files.
  #
  # Note that replacements that aren't reflected in replacement_data
  # entries will not be restarted - these config changes will be pushed
  # automatically without triggering any restarts.
  #
  # We expect:
  #
  #    0.0 <= percent_restart_max < 1.0
  #    0.0 <= percent_restart_min < 1.0
  #
  # if the % of removals/replacements on any shard is > % restart max,
  # the replacement is considered unsafe and is not performed.
  #
  # else if the % of removals/replacements on any shard is > % restart min,
  # then the restarts are triggered immediately.
  #
  # else the restarts will be triggered as long as no restarts have
  # been performed in the config or any of its dependent configs within
  # the minimum restart interval set for that config.
  #
  # If percent_restart_max is None, all restarts will be considered unsafe.
  # If percent_restart_min is None, all triggering will only be done
  #   based on expiration of the restart interval.
  'percent_restart_max'  : 0.35,
  'percent_restart_min'  : None,

  # This is the inter-set delay in secs. and is used by the restarter to space
  # outset restarts. This should be computes such that there is enough time
  # for the previous set to come up before the next is killed, but if you
  # can have more than one server down at a time, can be less. For example,
  # if the mixer takes 30 secs to come up, but you can have 5 mixers down
  # at one time (because we have lots of mixers in total), this value should be
  # 30/5 = 6
  # We set here a paranoid value, you should override this in the per-type
  # settings below, or in your config file for your particular service.
  # Keep as short as possible, but without causing too many servers to go down
  # at one time
  'inter_set_delay' : 300,

  # Next parameter is used solely by the restarter, and should be enabled
  # for the server types that supports '/varz?output=text&var=uptime-in-ms'
  # to get the time since they started in ms.
  # We use this to check if the probe starts actually started recently.
  # TODO: now this is enabled just for the critical ones: web, mixer,
  #  doc, index, balancer and cache. To fill up this list..
  'supports_uptime_check' : 0,

  # By default, the restarter will check that new servers are
  # actually alive before kicking off the entire restart process.
  # This obviously is the right thing to do.  We provide this option
  # only for certain special situations such as BART where we know
  # the push process will eventually happen and setup the servers
  # completely.
  'restarter_check_new_servers' : 1,

  # if set to 1, this will allow the restarter to ignore if new
  # servers don't start properly. This is useful for cases where it is
  # OK for the new server to be not setup properly. For example: if
  # indexservers are not setup properly by setup-production, BART will
  # eventually set them up properly, so it is not BAD for the
  # restarter to try to start the index server.
  'restarter_besteffort_start_new_servers' : 0,

  # For some types we actually do not need to have two servers in order to
  # choose a probe because there just one server per shard (this is the
  # case with crawl servers). Override this if your server is like this..
  'restarter_no_probe_check' : 0,

  # if set to 1, restarter won't restart the dependent servers when a
  # server is added or removed
  'restarter_no_dependent_restarts': 0,
}

#
# Non-overridable properties.
#
# If you do not want a property to be overridable in the SERVER_SETS
# data structure, then add the property name into the list below.
# We disallow overriding of certain properties because there generally
# is no need to override these and doing so may mean that something
# else is amiss - i.e. binaries maybe not up to date.  To try and
# enforce consistency in our setup, we are trying not to be too
# flexible.
#
_SERVER_TYPE_PROPERTIES_NON_OVERRIDABLE_ = [
  'is_sharded', 'is_leveled', 'level_size', 'binary_name',
  'binary_files', 'restart_function', 'kill_function',
  'kill_signal', 'kill_noport', 'kill_binaries',
  'checkpoint_info', 'port_offset', 'interpreter'
]

#
# Server type properties.
#
_SERVER_TYPE_PROPERTIES_ = {

  'extensible_webserver' : {
  },

  'syntheticnamed' : {
  },

  'index' : {
    'inter_set_delay' : 300,
    'is_sharded' : 1,
    'is_leveled' : 1,
    'request_info' : 'd 5 foo\n',
    'response_len' : _ACK_LEN_+2,
    'binary_name' : 'indexserver',
    'binary_files' : ['indexserver', 'mapfiles'],
    'backends' : [
      { 'set' : 'hostid', 'per_shard' : 1 },
      { 'set' : 'lexserver', },
    ],
    'supports_uptime_check' : 1,
    'setup_ops' : ['setup_prod'],
  },

  'index2' : {
    'is_sharded' : 1,
  },

  'cache' : {
    'inter_set_delay' : 10,
    'is_sharded' : 1,
    'is_leveled' : 1,
    'request_info' : "l foo\n0 -1 0\n",
    'response_len' : _ACK_LEN_,
    'binary_name' : 'cacheserver',
    'supports_uptime_check' : 1,
    'setup_ops' : ['datadir'],
  },

  'clustering_server' : {
    'request_info' : "GET /healthz HTTP/1.0\r\n\r\n",
    'response_len' : 2,
    'binary_name' : 'clustering_server',
    'protocol' : 'http',
    'has_datadir': 0,
    'backends' : [
      { 'set' : 'web' },
    ],
  },

  'registryserver' : {
    'request_info' : "GET /healthz HTTP/1.0\r\n\r\n",
    'response_len' : len('ok'),
    'interpreter' : '/usr/lib/jvm/java-1.6.0-openjdk-1.6.0.0/jre/bin/java',
    'binary_name' : 'RegistryServer',
    'bin_dir' : 'com.google.enterprise.registryserver',
    'var_info_connection_type' : 'http',
    'test_timeouts' : (10, 15, 40),
  },

  'supergsa_main' : {
    'request_info' : "GET /healthz HTTP/1.0\r\n\r\n",
    'response_len' : 2,
    'binary_name' : 'supergsa_main',
    'protocol' : 'http',
    'restarter_no_probe_check' : 1,
    'kill_delay' : 3,  # how long to wait between kill and kill -9
  },

  'workqueue-main' : {
    'request_info' : "GET /healthz HTTP/1.0\r\n\r\n",
    'response_len' : 2,
    'has_datadir' : 1,
    'backends' : [
      { 'set' : 'workqueue-subordinate' },
    ],
  },

  'workqueue-subordinate' : {
    'request_info' : "GET /healthz HTTP/1.0\r\n\r\n",
    'response_len' : 2,
    'has_datadir' : 1,
    'backends' : [
      { 'set' : 'workqueue-main' },
    ],
  },

  'workschedulerserver' : {
    'request_info' : "GET /healthz HTTP/1.0\r\n\r\n",
    'response_len' : 2,
    'binary_files' : ["workschedulerserver", "logtweak",
                      "froogle_doc_collector"],
    'backends' : [
      { 'set' : 'workqueue-main' },
    ],
  },

  'doc' : {
    'inter_set_delay' : 120,
    'is_sharded' : 1,
    'is_leveled' : 1,
    'request_info' : "r foo\n1\n1000\n100000\n100000000\n0\n",
    'response_len' : _ACK_LEN_,
    'binary_name' : 'docserver',
    'supports_uptime_check' : 1,
    'setup_ops' : ['setup_prod'],
    'datadir_has_port' : 1,
  },

  'link' : {
    'is_leveled' : 1,
    'request_info' : "GET /healthz HTTP/1.0\r\n\r\n",
    'response_len' : 2,
    'binary_files' : ['linkserver', 'sorted-map-server'],
    'kill_binaries' : ['linkserver', 'sorted-map-server'],
    'setup_ops' : ['setup_prod'],
  },

  'onebox' : {
    'request_info' : "v\n",
    'response_len' : _ACK_LEN_,
    'binary_name' : 'oneboxserver',
    'supports_dataversion' : 0,
    'supports_http_statusz' : 1,
    'statusz_port' : 9416,
    'supports_uptime_check' : 1,
    'inter_set_delay' : 40,
    'backends' : [
      { 'tag' : 'rtnews_idx', 'set' : 'rtsubordinate', 'serve_as' : 'index' },
      { 'tag' : 'rtnews_doc', 'set' : 'rtsubordinate', 'serve_as' : 'doc' },
      { 'set' : 'oneboxenterprise', 'protocol' : 'rpc' },
      { 'set' : 'oneboxwpres' },
      { 'set' : 'oneboxwpbiz' },
      { 'set' : 'odpcat' },
    ],
    'numconns': {
      'index'       : 6, # rtnews index
      'doc'         : 6, # rtnews doc
      'oneboxenterprise' : 1,
      'odpcat'      : 10,
      'oneboxwpres' : 10, # qserver
      'oneboxwpbiz' : 10, # qserver
    },
    'dflt_num_conn' : 3,
    'setup_ops' : ['setup_prod', 'googledata_push'],
    'data_push_paths': ['onebox/quicklink/'],
  },

  'spellmixer' : {
    # The entspellmixer server provides corrections for all supported languages.
    'request_info' : "GET /healthz HTTP/1.0\r\n\r\n",
    'response_len' : _ACK_LEN_,
    'binary_name' : 'entspellmixer',
    'protocol'  : 'rpc',
    'var_info_connection_type' : 'rpc',
    'setup_ops' : ['setup_prod'],
  },

  'oneboxdefinition' : {
    'request_info' : "RQ=\"define foo\" definition\n",
    'response_len' : _ACK_LEN_,
    'binary_name' : 'definitionserver',
    'setup_ops' : ['setup_prod'],
    # use the stubby port for statusz
    'statusz_port' : 10081,
  },

  'oneboxenterprise' : {
    'request_info' : "GET /healthz HTTP/1.0\r\n\r\n",
    'response_len' : 2,
    'binary_name' : 'enterprise_onebox',
    'protocol' : 'rpc',
    'has_datadir': 0,
    'data_push_paths': [],
    # TODO (graceh): probably better to talk with mixer if possible.
  },

  'web' : {
    'inter_set_delay' : 40,
    # NOTE: When custom synonyms are uploaded, qrewrite must be restarted,
    #   to read the new compiled list of synonyms. After being restarted,
    #   the qrewrite server works fine, but gws seems to keep an old
    #   connection open to the defunct qrewrite, and gets timeout errors
    #   when it tries to send qrewrite requests.
    #   This modified query activates qrewrite, and causes gws to reset
    #   broken connections after a restart.
    'request_info' : "GET /search?num=5&entqr=1&q=foo+bar HTTP/1.0\r\n\r\n",
    'response_len' : 300,
    'binary_name' : 'gws',
    'kill_delay' : 11,
    'var_info_connection_type' : 'http',
    'supports_http_statusz' : 1,
    'backends' : [
      { 'set' : 'onebox' , 'protocol' : 'rpc' },
      { 'set' : 'admixer' },
      { 'set' : 'directory' },
      { 'set' : 'qrewrite', 'protocol' : 'rpc' },
      { 'set' : 'spellmixer', 'protocol' : 'rpc'  },
      { 'set' : 'ent_fedroot', 'protocol' : 'rpc'  },
      { 'set' : 'related' },
      { 'set' : 'mixer', 'protocol' : 'http' },
      { 'set' : 'authzchecker', 'protocol' : 'rpc' },
    ],
    # We increase the number of connections to 10 because in enterprise
    # we now support mulitple external and internal oneboxes.
    # See get_webargs() in servertype_prod.py for the 'numconns' property
    'setup_ops' : ['googledata_push'],
    'dflt_numconn' : 3,  # This is overridden in servertype_prod.py
    'supports_uptime_check' : 1,
    'kernel' : 'web',
    'schedtypes' : { 'default' : 'rr' },
    'data_push_paths': ['html/', 'gws/'],
    'data_push_test' : '/healthz?safe=data',
  },

  'mixer' : {
    'inter_set_delay' : 35,
    'request_info' : "GET /healthz HTTP/1.0\r\n\r\n",
    'response_len' : 2,
    'binary_name' : 'mixserver',
    'supports_http_statusz' : 1,
    'backend_port_base' : 4000,
    'backends' : [
      { 'set' : 'cache' },
      { 'set' : 'index', },
      { 'set' : 'doc', },
      { 'set' : 'link', },
      { 'set' : 'lcaserver', },
      { 'set' : 'forwardmap', },
      { 'set' : 'imagedoc', },
      { 'set' : 'rtsubordinate', 'serve_as' : 'index' },
      { 'set' : 'rtsubordinate', 'serve_as' : 'doc' },
      { 'set' : 'rtmain', 'serve_as' : 'index' },
      { 'set' : 'rtmain', 'serve_as' : 'doc' },
      { 'set' : 'base_indexer', 'serve_as' : 'index', 'level' : 0 },
      { 'set' : 'base_indexer', 'serve_as' : 'doc', 'level' : 0 },
      { 'set' : 'daily_indexer', 'serve_as' : 'index', 'level' : 1 },
      { 'set' : 'daily_indexer', 'serve_as' : 'doc', 'level' : 1 },
      { 'set' : 'rt_indexer', 'serve_as' : 'index', 'level' : 2 },
      { 'set' : 'rt_indexer', 'serve_as' : 'doc', 'level' : 2 },
    ],
    # overridden in servertype_prod.py
    'numconns' : { 'index' : 6, 'doc' : 6, 'cache' : 9, },
    'schedtypes' : { 'cache' : 'rr', 'lcaserver' : 'rr', 'forwardmap': 'rr' },
    'dflt_numconn' : 3,  # overriden in servertype_prod.py
    'supports_uptime_check' : 1,
    'setup_ops' : ['setup_prod'],
  },

  'ent_fedroot' : {
    'inter_set_delay' : 35,
    'request_info' : "GET /healthz HTTP/1.0\r\n\r\n",
    'response_len' : 2,
    'supports_http_statusz' : 1,
    'backend_port_base' : 9999,
    'backends' : [
      { 'set' : 'cache' },
      { 'set' : 'index', },
      { 'set' : 'doc', },
      { 'set' : 'link', },
      { 'set' : 'lcaserver', },
      { 'set' : 'forwardmap', },
      { 'set' : 'imagedoc', },
      { 'set' : 'rtsubordinate', 'serve_as' : 'index' },
      { 'set' : 'rtsubordinate', 'serve_as' : 'doc' },
      { 'set' : 'rtmain', 'serve_as' : 'index' },
      { 'set' : 'rtmain', 'serve_as' : 'doc' },
      { 'set' : 'base_indexer', 'serve_as' : 'index', 'level' : 0 },
      { 'set' : 'base_indexer', 'serve_as' : 'doc', 'level' : 0 },
      { 'set' : 'daily_indexer', 'serve_as' : 'index', 'level' : 1 },
      { 'set' : 'daily_indexer', 'serve_as' : 'doc', 'level' : 1 },
      { 'set' : 'rt_indexer', 'serve_as' : 'index', 'level' : 2 },
      { 'set' : 'rt_indexer', 'serve_as' : 'doc', 'level' : 2 },
    ],
    'numconns' : { 'index' : 6, 'doc' : 6, 'cache' : 9, },
    'schedtypes' : { 'cache' : 'rr', 'lcaserver' : 'rr', 'forwardmap': 'rr' },
    'dflt_numconn' : 1,
    'supports_uptime_check' : 1,
    'setup_ops' : ['setup_prod'],
  },

  'qrewrite' : {
    'request_info' : "GET /healthz HTTP/1.0\r\n\r\n",
    'response_len' : len("HTTP/1.0 200 OK\r\n\r\n"),
    'has_datadir' : 1,
    'supports_dataversion' : 0,
    'supports_http_statusz' : 1 ,
    'var_info_connection_type' : 'http',
    'protocol' : 'rpc',
    'setup_ops' : ['setup_prod'],
    'kernel' : 'index',
  },

  'twiddleserver' : {
    'request_info' : "GET /healthz HTTP/1.0\r\n\r\n",
    'response_len' : len("HTTP/1.0 200 OK\r\n\r\n"),
    'has_datadir' : 1,
    'supports_dataversion' : 0,
    'supports_http_statusz' : 1 ,
    'var_info_connection_type' : 'http',
    'protocol' : 'http',
    'setup_ops' : ['setup_prod'],
  },

  'entfrontend' : {
    'request_info' : "GET /proxy_healthz HTTP/1.0\r\n\r\n",
    'response_len' : 12,
    'interpreter' : '/usr/lib/jvm/java-1.6.0-openjdk-1.6.0.0/jre/bin/java',
    'binary_name' : 'EnterpriseFrontend',
    'bin_dir' : 'com.google.enterprise.frontend',
    'var_info_connection_type' : 'http',
    'backends' : [
      { 'set' : 'web' },
      { 'set' : 'feedergate' },
      { 'set' : 'enttableserver' },
      { 'set' : 'fsgw' },
      { 'set' : 'clustering_server' },
    ],
  },

  'enttableserver' : {
    'request_info' : "GET /healthz HTTP/1.0\r\n\r\n",
    'response_len' : len('ok'),
    'interpreter' : '/usr/lib/jvm/java-1.6.0-openjdk-1.6.0.0/jre/bin/java',
    'binary_name' : 'TableServer',
    'bin_dir' : 'com.google.enterprise.database',
    'var_info_connection_type' : 'http',
    'backends' : [
      { 'set' : 'web' },
    ],
  },

  'fsgw' : {
    'request_info' : "GET /healthz HTTP/1.0\r\n\r\n",
    'response_len' : len('ok'),
    'interpreter' : '/usr/lib/jvm/java-1.6.0-openjdk-1.6.0.0/jre/bin/java',
    'binary_name' : 'FileSystemGateway',
    'bin_dir' : 'com.google.enterprise.fsgw',
    'var_info_connection_type' : 'http',
  },

  'authzchecker' : {
    'request_info' : "GET /healthz HTTP/1.0\r\n\r\n",
    'response_len' : len('ok'),
    'interpreter' : '/usr/lib/jvm/java-1.6.0-openjdk-1.6.0.0/jre/bin/java',
    'binary_name' : 'AuthzChecker',
    'bin_dir' : 'com.google.enterprise.authzchecker',
    'var_info_connection_type' : 'http',
    'test_timeouts' : (10, 15, 40),
    'backends' : [
      { 'set' : 'headrequestor' },
      { 'set' : 'fsgw' },
    ],

  },

  'connectormgr' : {
    'request_info' : "GET /connector-manager/testConnectivity HTTP/1.0\r\n\r\n",
    'response_len' : len('<CmResponse>\r\n  <StatusId>0</StatusId>\r\n</CmResponse>\r\n'),
    'interpreter' : '/usr/lib/jvm/java-1.6.0-openjdk-1.6.0.0/jre/bin/java',
    'binary_name' : 'Bootstrap',
    'bin_dir' : 'org.apache.catalina.startup',
    'var_info_connection_type' : 'http',
    'test_timeouts' : (10, 15, 40),
  },

  'rtmain' : {
    'is_sharded' : 1,
    'is_leveled' : 1,
    'request_info' : "v\n",
    'response_len' : _ACK_LEN_ + 30,
    'binary_name' : 'rtserver',
    'datadir_has_port' : 1,
  },

  'rtsubordinate' : {
    'is_sharded' : 1,
    'is_leveled' : 1,
    'request_info' : "v\n",
    'response_len' : _ACK_LEN_ + 30,
    'binary_name' : 'rtserver',
    'setup_ops' : ['datadir'],
    'datadir_has_port' : 1,
  },

  'pyserverizer' : {
    'request_info'       : "GET /healthz\r\n\r\n",
    'response_len'       : 2,                  # ok
    'has_datadir'        : 0,
    'restarter_no_probe_check' : 1,
  },

  'feedergate' : {
    'request_info' : "GET /healthz HTTP/1.0\r\n\r\n",
    'response_len' : 2,
    'kill_delay' : 3,
    'var_info_connection_type' : 'http',
  },

  'feeder' : {
    'is_sharded' : 1,
    'request_info' : "GET /healthz HTTP/1.0\r\n\r\n",
    'response_len' : 2,
    'kill_delay' : 3,
    'var_info_connection_type' : 'http',
  },

  'urlserver' : {
    'request_info' : "DV=%(dataversion)s a\n",
    'response_len' : 0,
    'kill_delay' : 3,
    'restarter_no_probe_check' : 1,
  },

  'rfserver' : {
    'request_info' : "DV=%(dataversion)s a\n",
    'response_len' : 0,
    'kill_delay' : 3,
    'restarter_no_probe_check' : 1,
  },

  'rfserver_bank' : {
    'binary_name' : 'rfserver',
    'request_info' : "v\n",
    'response_len' : _ACK_LEN_ + 30,
    'kill_delay' : 3,
  },

  'rfserver_replica_bank' : {
    'binary_name' : 'rfserver',
    'request_info' : "v\n",
    'response_len' : _ACK_LEN_ + 30,
    'kill_delay' : 3,
  },

  # urlmanager AKA Enterprise crawlmanager
  'urlmanager' : {
    'is_sharded' : 1,
    'request_info' : "DV=%(dataversion)s a\n",
    'response_len' : 0,
    'kill_delay' : 3,
    'checkpoint_info' : "k\n",
    'restarter_no_probe_check' : 1,
    'binary_name'  : 'crawlmanager',
  },

  'dnscache' : {
    'is_sharded'   : 1,
    'request_info' : "a\n",
    'response_len' : _ACK_LEN_,
    'kill_delay' : 3,
    'binary_name'  : 'cacheserver',
  },

  'bot' : {
    'is_sharded'   : 1,
    'request_info' : "a\n",
    'response_len' : _ACK_LEN_,
    'kill_delay'   : 3,
    # For ims crawls, we talk to either docservers or mixservers
    'backends' : [
      { 'set' : 'doc' },
      { 'set' : 'mixer' },
      { 'set' : 'fsgw' },
    ],
    'local_data_files' : [
       { 'srcpath'    : 'googledata/googlebot/',
         'targetpath' : '/etc/google/',
         'files'      : ['blackhole'],
       },
    ],
  },

  'cookieserver' : {
    'request_info'       : "a\n",
    'response_len'       : _ACK_LEN_,
    'kill_delay'         : 3,
  },

  'rtdupserver' : {
    'request_info' : "DV=%(dataversion)s a\n",
    'response_len' : 0,
    'kill_delay' : 3,
    'checkpoint_info' : "k\n",
    'is_sharded' : 1,
    'restarter_no_probe_check' : 1,
    'restarter_check_new_servers' : 0,  # long startup
  },

  'contentfilter' : {
    'is_sharded' : 1,
    'request_info' : "DV=%(dataversion)s a\n",
    'response_len' : 0,
    'kill_delay' : 3,
    'binary_files' : ['contentfilter', 'convert_to_html'],
    'restarter_no_probe_check' : 1,
    'restarter_check_new_servers' : 0,  # long startup
    'local_data_files' : [
       { 'srcpath'    : 'googledata/crawl/',
         'files'      : [ "duphosts"],
  },
       { 'srcpath'    : 'googledata/googlebot/',
         'targetpath' : 'googlebot/',
         'files'      : [ "url_rewrites_crawl", "url_rewrites_crawl.qp.binary0"],
  },
       { 'srcpath'    : 'googledata/langid/',
         'targetpath' : 'langid/',
  },
       { 'srcpath'    : 'googledata/BasisTech/',
         'targetpath' : 'BasisTech/',
  },
       { 'srcpath'    : 'google2/third-party/Inso/',
         'targetpath' : 'Inso/',
  },
       { 'srcpath'    : 'googledata/googlebot/',
         'targetpath' : 'Inso/',
         'files'      : [ "inso.cfg", "inso_template.htm"],
  },
       { 'srcpath'    : 'google2/third-party/pdftohtml/',
         'targetpath' : 'pdftohtml/',
  },
       { 'srcpath'    : 'google2/converter/',
         'targetpath' : 'converter/',
  },
       { 'srcpath'    : 'google2/bin/',
         'files'      : ['magick-converter', 'swfparse'],
  },
       # NOTE: 1. ADD pdftotext if we still need it somehow
       #       2. all files get pushed even if we don't need it
       #          (e.g., pdf conversion, image-crawl)
    ],
  },

  'tracker_gatherer' : {
    'is_sharded' : 1,
    'request_info' : "DV=%(dataversion)s a\n",
    'response_len' : 0,
    'kill_delay' : 3,
  },

  'urltracker_server' : {
    'is_sharded' : 1,
    'request_info' : "DV=%(dataversion)s a\n",
    'response_len' : 0,
    'kill_delay' : 3,
  },

  'urlmanager_log_rewriter' : {
    'is_sharded' : 1,
    'request_info' : "v\n",
    'response_len' : _ACK_LEN_ + 30,
    'kill_delay' : 3,
    'checkpoint_info' : "k\n",
  },


  'pr_main' : {
    'is_sharded' : 1,
    'request_info' : "DV=%(dataversion)s a\n",
    'response_len' : 0,
    'kill_delay' : 3,
    'restarter_no_probe_check' : 1,
  },

  'pageranker' : {
    'is_sharded' : 1,
    'request_info' : "GET /healthz HTTP/1.0\r\n\r\n",
    'response_len' : 2,                  # ok
    'supports_http_statusz': 1,
    'statusz_port': 23000,
    'supports_uptime_check' : 1,
    'kill_delay' : 3,
    'restarter_no_probe_check' : 1,
    'backends' : [
        { 'set' : 'pageranker' },
      ],
    'supports_dataversion' : 0,
    'supports_google2_args' : 0, ## pageranker is google3 code without bigfiles
  },

  'base_indexer' : {
    'request_info' : "DV=%(dataversion)s a\n",
    'response_len' : 0,
    'is_sharded'   : 1,
    'kill_delay'   : 3,
    'binary_name'  : 'rtserver',
    'restarter_no_probe_check' : 1,
    'restarter_check_new_servers' : 0,  # long startup
    'local_data_files' : [
       { 'srcpath'    : 'googledata/BasisTech/',
         'targetpath' : 'BasisTech/', },
    ],
  },

  'daily_indexer' : {
    'request_info' : "DV=%(dataversion)s a\n",
    'response_len' : 0,
    'is_sharded'   : 1,
    'kill_delay'   : 3,
    'binary_name'  : 'rtserver',
    'kill_noport'  : 1, ## TODO: really ???
    'restarter_no_probe_check' : 1,
    'restarter_check_new_servers' : 0,  # long startup
    'local_data_files' : [
       { 'srcpath'    : 'googledata/BasisTech/',
         'targetpath' : 'BasisTech/', },
    ],
  },

  'rt_indexer' : {
    'request_info' : "DV=%(dataversion)s a\n",
    'response_len' : 0,
    'is_sharded'   : 1,
    'kill_delay'   : 3,
    'binary_name'  : 'rtserver',
    'restarter_no_probe_check' : 1,
    'restarter_check_new_servers' : 0,  # long startup
    'local_data_files' : [
       { 'srcpath'    : 'googledata/BasisTech/',
         'targetpath' : 'BasisTech/', },
    ],
  },

  'urlhistory_processor' : {
    'request_info' : "DV=%(dataversion)s a\n",
    'response_len' : 0,
    'is_sharded'   : 1,
    'kill_delay'   : 3,
    'binary_name'  : 'rtserver',
    'restarter_no_probe_check' : 1,
    'restarter_check_new_servers' : 0,  # long startup
    'local_data_files' : [
       { 'srcpath'    : 'googledata/BasisTech/',
         'targetpath' : 'BasisTech/', },
    ],
  },

  'urlhistory2log' : {
    'kill_delay' : 3,
    'kill_noport' : 3,
    'binary_name' : 'rtserver',
    'restarter_no_probe_check' : 1,
    'restarter_check_new_servers' : 0,  # long startup ???
  },

  # urlscheduler AKA Enterprise crawlscheduler
  'urlscheduler' : {
    'is_sharded' : 1,
    'request_info' : "a\n",
    'response_len' : _ACK_LEN_,
    'kill_delay' : 3,
    'binary_name' : 'crawlscheduler',
    'restarter_no_probe_check' : 1,
  },

  'indexer' : {
    'is_sharded' : 1,
  },

  'crawlbabysitter' : {
    'binary_name' : 'testserver.py',
  },

  'rippersubordinate' : {
    'is_sharded' : 1,
  },

  'vmwebserver' : {
    'request_info' : "GET / HTTP/1.0\r\n\r\n",
    'response_len' : 2,
  },

  'headrequestor' : {
    'request_info' : "v\n",
    'response_len' : _ACK_LEN_ + 20,
    'backends' : [
      { 'set' : 'authzchecker' },
    ],
  },

  'urlhistory_merger' : {
    'is_sharded' : 1,
  },

  'indexing_status_server' : {
    'request_info' : "v\n",
    'response_len' : _ACK_LEN_ + 30,
    'binary_name' : 'indexing_status_server.py',
  },

  'config_manager': {
    'request_info' : "GET /healthz HTTP/1.0\r\n\r\n",
    'response_len' : 2,
    'has_datadir' : 0,
    'interpreter' : '/usr/bin/python2.4',
    'binary_name': 'ent_configmgr.py',
  },

  'babysitter' : {
    'sync_from_babysitter' : 1,
    'has_datadir' : 0,
    'binary_name' : 'monitor',
    'binary_files' : ['monitor', 'fileutil'],
    'setup_script': 'setup_baby.py',
  },

  'bigindexfilterbuilder' : {
    'request_info' : "a\n",
    'response_len' : _ACK_LEN_,
    'is_sharded' : 1,
    'has_datadir': 0,
    'binary_name' : 'buildindexfilter',
    'var_info_connection_type' : 'http',
  },

  'bigindexfiltermerger' : {
    'request_info' : "a\n",
    'response_len' : _ACK_LEN_,
    'is_sharded' : 1,
    'has_datadir': 0,
    'binary_name' : 'embeddedlexmerge',
    'var_info_connection_type' : 'http',
  },

  'workflow-monitor' : {
    'has_datadir' : 0,
    'supports_dataversion' : 0,
    'supports_http_statusz': 1,
    'request_info' : "GET /healthz HTTP/1.0\r\n\r\n",
    'response_len' : 2,
    'var_info_connection_type' : 'http',
  },

}

# Support binaries that are placed on every server.
_SUPPORT_BINARIES_ = ['filesum', 'fileutil', 'multicp']

#
# These mappings are used to automatically
# generate machine:port assignment for the key server types using
# the machines used by the servers specified as one of the attributes.
#
# possible attributes are:
# (use this     , use .. as primary, use .. as replica, from... , to..., run on)# ('server name', 'primary/replica', 'replica/primary', fraction, fraction/shard#, single port?)
# ('urlmanager',  'replica', None, 0.5, 1.0, 0)
#
_AUTOASSIGN_MAP_ = {
  'pr_main'        : ['urlmanager',  'replica', 'primary', 0,   1,   0],
  'dupserver'      : ['urlmanager',  'replica', 'primary', 0,   1,   0],
  'contentfilter'  : ['storeserver', 'replica', None,      0,   1,   1],
  }


#
# List of types that need rfservers.
#
_NEED_RFSERVER_TYPES_ = {
  'nogfs' : [
    'urlmanager', 'urlmanager_log_rewriter', 'pr_main', 'storeserver',
    'dupserver', 'tracker_gatherer',
    'rfserver_bank', 'rfserver_replica_bank',
    ],

  'gfs' : [
    'pr_main', # to store temporary data for all-to-all communication
    ]
  }

#
# Default rfserver port for types that need rfservers.
# We will create servers on this port for machines with above types.
#
_DEFAULT_RFSERVER_PORT_ = 3899


#
# Cross monthly index machine types
# This list is used by runcrawler.py, indexrun.py and probably others
# so that they don't accidentally mess with these machines
#
_CROSS_INDEX_STORE_DATA_TYPES_ = [
  'interindex',
  'anchordata',
  'partialanchordata',
  'dupdata',
  'forwardingdata',
  'logarchive',
  'interindexpr',
  'urlhistory_merger',
  'prperiodic',
  'historyserver',
  'goldendoc',
  'sorter',
  'genhistorytable',
  'historytablearchive'
]

# Properties that should be passed through
# from balanced servertypes to their balancers.
_BALANCER_PASS_THROUGH_PROPERTIES_ = [
  'protocol'
]
