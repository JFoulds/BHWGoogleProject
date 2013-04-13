#!/usr/bin/python2.4
#
# Copyright 2004 Google Inc.

import sys
import time
from google3.base import pywrapbase
from google3.pyglib import gfile
from google3.pyglib import logging
from google3.enterprise.legacy.adminrunner import configurator
from google3.enterprise.legacy.adminrunner import config_xml_serialization
from google3.enterprise.legacy.adminrunner import entconfig

from google3.pyglib import flags
FLAGS = flags.FLAGS

flags.DEFINE_string('enthome', None, 'Enterprise home')
flags.DEFINE_string('xml_path', None, 'Path to XML configuration')
flags.DEFINE_boolean('do_export', 0, 'Export configuration')
flags.DEFINE_boolean('do_import', 0, 'Import configuration')

logging.set_googlestyle_logfile(log_dir = '/export/hda3/logs')

def main(argv):
  try:
    argv = FLAGS(argv) # parse flags
  except flags.FlagsError, e:
    sys.exit('%s\nUsage: %s ARGS\n%s' % (e, argv[0], FLAGS))

  if not FLAGS.enthome:
    sys.exit('Must specify --enthome')

  if not FLAGS.xml_path:
    sys.exit('Must specify --xml_path')

  if not (FLAGS.do_import or FLAGS.do_export):
    sys.exit('Must specify --do_import or --do_export')

  ent_config = entconfig.EntConfig(FLAGS.enthome)
  if not ent_config.Load():
    sys.exit('Cannot load configuration.')

  pywrapbase.InitGoogleScript('', ['foo',
          '--gfs_aliases=%s' % ent_config.var('GFS_ALIASES'),
          '--bnsresolver_use_svelte=false',
          '--logtostderr', '--minloglevel=1'], 0)
  gfile.Init()

  begin = time.time()
  cfg = configurator.configurator(FLAGS.enthome)

  if FLAGS.do_import:
    logging.info("initializing global default files")
    if not cfg.globalParams.InitGlobalDefaultFiles(overwrite=0):
      logging.fatal("failed to initialize global default files")

    config_xml_serialization.ImportConfiguration(cfg, open(FLAGS.xml_path))

  if FLAGS.do_export:
    f = open(FLAGS.xml_path, 'w')
    f.write(config_xml_serialization.ExportConfiguration(cfg))
    f.close()

  diff = (time.time() - begin ) / 60
  logging.info('Migration operation took %.2f minutes.' % diff)

if __name__ == '__main__':
  main(sys.argv)
