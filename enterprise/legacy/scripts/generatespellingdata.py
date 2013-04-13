#!/usr/bin/python2.4
#
# Copyright 2008 Google Inc. All Rights Reserved.

"""Generate custom spelling data from output of enterprise crawl pipeline.

This script converts the data for spell server.

The generated spelling data is copied to a runtime directory named with an
ever-increasing index(e.g. /export/hda3/5.1.15/spelling/spell-N). When all has
completed successfully AdminRunner is notified of the new index, and an attempt
is made to delete previous versions. For example if the current index is 46, we
will increment the index to 47 and try to delete versions <= 45.
We cannot delete 46 yet, because spellserver is still using it. Eventually
fixer should notice the change and restart spellserver using the new index.
Yes, this script sucks. But you should have seen it before!

This script also rotates and consolidates the raw spelling data in /bigfile.
We keep the spelling data of the current day as-is. The data from yesterday or
older will be consolidated into one file per day (per language per n-gram
type). So if the script is run once per day and spelling data is written every
10 minutes by supergsa_main, there will not be more than 24 * 6 + 30 raw files
in /bigfile (per language per n-gram type).

Docs:
  http://wiki.corp.google.com/twiki/bin/view/Main/ESQSpelling

Usage:
  export TMPDIR=/export/hda3/tmp/
  $0 --enthome=/export/hda3/5.x.y/ --alsologtostderr
"""

__author__ = 'hotti@google.com (Daniel Hottinger)'

import glob
import os
import re
import tempfile
import time

from google3.pyglib import app
from google3.pyglib import flags
from google3.pyglib import logging

from google3.enterprise.legacy.adminrunner import entconfig
from google3.enterprise.legacy.adminrunner import adminrunner_client

flags.DEFINE_list('langs', 'en', 'Comma separated list of language tags to '
                  'generate spelling data for')

flags.DEFINE_string('enthome', None,
                    'ENTHOME: the full path to the enterprise home directory')

flags.DEFINE_integer('keep_spellingdata_for_days', 30,
                     'Keep spelling data for number of days')

flags.DEFINE_integer('consolidate_spellingdata_interval', 24 * 60 * 60,
                     'Files written between this interval will be consolidated '
                     'into one single file. In seconds.')

FLAGS = flags.FLAGS

# Used to extract unix timestamp from file names.
ENTSPELLING_TIME_RE = re.compile(r'([^0-9]+-)([0-9]+)$')


class Error(Exception):
  pass


class CommandError(Error):
  pass


class FilenameError(Error):
  pass


def RunCommand(command):
  """Simple command wrapper that checks exit status and logs/raises error
     if the command fails.  Logs and times commands that succeed.
  Args: command - string holding a command to run
  Returns: None
  """
  start_time = time.time()
  if os.system(command):
    logging.error('Command failure:    %s' % command)
    raise CommandError, 'cannot complete command: %s' % command
  logging.info('Command successful (took %f sec): %s' %
                                      ((time.time()-start_time), command))
  logging.flush()


def ClassifySpellingData(file_list):
  """Returns a list of files to be deleted, consolidated and left untouched.

  Args:
    file_list: e.g. [ '/bigfile/entspelling-unigrams-1213339913', ... ]
               File names must end with '-' and a unix time stamp.

  Returns: (to_delete, to_consolidate, to_keep)
    to_delete: List of filenames older than FLAGS.keep_spellingdata_for_days
               days.
    to_consolidate: { 'new_filename': [ 'old_file1', 'old_file2', ... ], ... }
                    These files should be consolidated into one file.
    to_keep: List of filenames that cannot be consolidated yet.
  """
  now = time.time()
  current_interval = now - now % FLAGS.consolidate_spellingdata_interval
  delete_cutoff = current_interval - FLAGS.keep_spellingdata_for_days * 24 * 60 * 60

  to_delete = []
  to_consolidate = {}
  to_keep = []
  for fn in file_list:
    res = ENTSPELLING_TIME_RE.match(fn)
    if res is None:
      raise FilenameError('%s does not match' % fn)
    fn_prefix = res.group(1)
    unix_time = int(res.group(2))

    if unix_time < delete_cutoff:
      to_delete.append(fn)
    elif unix_time >= current_interval:
      to_keep.append(fn)
    else:
      consolidated_time = unix_time - (
          unix_time % FLAGS.consolidate_spellingdata_interval)
      consolidated_filename = '%s%d' % (fn_prefix, consolidated_time)
      to_consolidate.setdefault(consolidated_filename, []).append(fn)

  # For easy unit testing.
  to_delete.sort()
  to_keep.sort()
  for x in to_consolidate.values():
    x.sort()

  return to_delete, to_consolidate, to_keep


class SpellingDataGenerator:
  def __init__(self, enthome, ec, current_dir, next_dir, lang):
    self.cutoff_freq_ = ec.var('SPELL_FREQ_CUTOFF')

    fsargs = []
    datadir = ec.var('DATADIR')
    gfs_aliases = ec.var('GFS_ALIASES')
    if datadir:
      fsargs.append('--datadir=%s' % datadir)
    if gfs_aliases:
      fsargs.append('--bnsresolver_use_svelte=false')
      fsargs.append("--gfs_aliases='%s'" % gfs_aliases)
    fsargs = ' '.join(fsargs)

    self._opts = {
      'lang': lang,
      'enthome': enthome,
      'filter_size': ec.var('SPELL_FILTER_SIZE'),
      'namespace_prefix': ec.var('NAMESPACE_PREFIX'),
      'current_dir': current_dir,
      'next_dir': next_dir,
      'tmp': '%s/spell-%s' % (ec.var('TMPDIR'), lang),
      'bin': '%s/local/google2/bin' % enthome,
      'fsargs': fsargs,
      'logdir': ec.var('TMPDIR'),
      'tmpdir': ec.var('TMPDIR'),
      'verbosity': 0,
    }
    self._opts.update({
      'fileutil': '%(bin)s/fileutil %(fsargs)s' % self._opts,
      'buildrtspelling': ('%%(bin)s/buildruntimespelling'
                          ' --enable_localized_filters=false'
                          ' --log_dir=%%(logdir)s'
                          ' --datadir=%%(tmp)s'
                          ' --cutoff_freq=%d'
                          ' --language=%%(lang)s'
                          ' --spellingdatafactorytype=enterprise ' %
                            self.cutoff_freq_) % self._opts,
      'out': '%(tmp)s/%(lang)s.spelling' % self._opts,
    })

  def Run(self, command):
    """Simple command wrapper that checks exit status and logs/raises error
       if the command fails.  Logs and times commands that succeed.
    Args:
      command: String holding a format string of command to run.
               The string is expanded with self._opts.
    Returns:
      None
    """
    RunCommand(command % self._opts)

  def sortUnigramsByFrequency(self, input_path, output_path):
    # use sortdict to merge multiple instances of the same unigram
    tmp_path = '%(tmp)s/merged-spelling-unigrams'
    self.Run('%%(bin)s/sortdict %%(fsargs)s --log_dir=%%(logdir)s --output=%s '
             '--v=%%(verbosity)d %s' % (tmp_path, input_path))
    # use g2sort to sort merged unigrams by frequency
    self.Run('%%(bin)s/g2sort -T %%(tmpdir)s -nr %s > %s' % (tmp_path, output_path))
    self.Run('rm %s' % tmp_path)

  # TODO(hotti) refactor the following three methods into one:
  def customizeUnigrams(self, web_unigrams_path, ent_unigrams_path):
    self.Run("awk '{if ($1 > 100) print \"%d\t\" $2}' < %s > %s-adj" % (
               (self.cutoff_freq_ + 1), web_unigrams_path, web_unigrams_path))
    self.Run('mv %s %s' % (ent_unigrams_path, web_unigrams_path))
    self.Run('%%(fileutil)s --log_dir=%%(logdir)s append %s-adj %s' % (
               web_unigrams_path, web_unigrams_path))

  def customizeBigrams(self, web_bigrams_path, ent_bigrams_path):
    self.Run("awk '{if ($1 > 100) print \"%d\t\" $2 \" \" $3}' < %s > %s-adj" %
               ((self.cutoff_freq_ + 1), web_bigrams_path, web_bigrams_path))
    self.Run('mv %s %s' % (ent_bigrams_path, web_bigrams_path))
    self.Run('%%(fileutil)s --log_dir=%%(logdir)s append %s-adj %s' % (
               web_bigrams_path, web_bigrams_path))

  def customizeTrigrams(self, web_trigrams_path):
    self.Run("awk '{if ($1 > 10) print \"%d\t\" $2 \" \" $3 \" \" $4}' < %s"
             " > %s-adj" % ((self.cutoff_freq_ + 1),
                            web_trigrams_path,
                            web_trigrams_path))
    self.Run('mv %s-adj %s' % (web_trigrams_path, web_trigrams_path))

  def GenerateAll(self):
    """Creates spelling data for a single language."""

    self.Run('rm -rf %(tmp)s')
    self.Run('mkdir -p %(tmp)s')

    # remove old merged files to prevent appending to them
    for ngram in ('unigrams', 'bigrams'):
      dest = '%(namespace_prefix)s/entspelling-%(lang)s-all-' + ngram
      self.Run('%%(fileutil)s -f rm %s' % dest)

      file_list = tempfile.mktemp()
      src_pattern = ('%(namespace_prefix)s/entspelling-%(lang)s-' + ngram
                     + '-[0-9]*')
      self.Run('%%(fileutil)s ls %s > %s || true' % (src_pattern, file_list))
      # TODO(hotti): There must be some data or exit script here!

      spelling_files = [ l.strip() for l in open(file_list, 'r') ]
      to_delete, to_consolidate, to_keep = ClassifySpellingData(spelling_files)
      for f in to_delete:
        self.Run('%%(fileutil)s --log_dir=%%(logdir)s -f rm %s' % f)
      for f, fragments in to_consolidate.iteritems():
        logging.info('Consolidating: %s <- %s' % (f, fragments))
        for fragment in fragments:
          if fragment == f:
            continue
          # Note: append does an implicit rm of its first argument.
          self.Run('%%(fileutil)s --log_dir=%%(logdir)s append %s %s' % (
                   fragment, f))
      for src in to_keep + to_consolidate.keys():
        # Note: we still want to keep the data around. Since append deletes the 
        # source file we have to make a copy.
        self.Run('%%(fileutil)s --log_dir=%%(logdir)s cp %s %s-fsck-append'
            % (src, src))
        self.Run('%%(fileutil)s --log_dir=%%(logdir)s append %s-fsck-append %s'
            % (src, dest))
        # That append deletes the source file does not seem to work all the
        # time. So we remove it here manually again, just in case.
        self.Run('%%(fileutil)s --log_dir=%%(logdir)s rm -f %s-fsck-append'
            % src)
      self.Run('rm %s' % file_list)

    for ngram in ('unigrams', 'bigrams'):
      cmd = ('%(fileutil)s --log_dir=%(logdir)s ls -l '
             '%(namespace_prefix)s/entspelling-%(lang)s-all-' + ngram)
      try:
        self.Run(cmd + ' > /dev/null 2>&1')                  # Does file exist?
        self.Run(cmd + " | awk '{ if ($5 == 0) exit 1; }'")  # Is its size > 0?
      except CommandError:
        logging.info('No new spelling data found for "%(lang)s." '
                     'Using default data instead.' % self._opts)
        self.Run('cp %(enthome)s/../spelling-data/runtime/%(lang)s.spelling.* '
                 '%(next_dir)s')
        return

    # copy the preexisting standard spelling runtime data to the datadir
    self.Run('cp %(enthome)s/../spelling-data/runtime/%(lang)s.spelling.*'
             ' %(tmp)s')

    self.sortUnigramsByFrequency(
        '%(namespace_prefix)s/entspelling-%(lang)s-all-unigrams',
        '%(tmp)s/ent-unigrams')

    # use sortdict to merge multiple instances of the same bigram
    self.Run('%(bin)s/sortdict %(fsargs)s --log_dir=%(logdir)s'
             ' --output=%(tmp)s/merged-spelling-bigrams --v=%(verbosity)d'
             ' %(namespace_prefix)s/entspelling-%(lang)s-all-bigrams')
    # strip semicolons from enterprise bigrams
    self.Run('sed "s/;/ /g" %(tmp)s/merged-spelling-bigrams >'
             ' %(tmp)s/ent-bigrams')
    self.Run('%(fileutil)s -f rm %(tmp)s/merged-spelling-bigrams')

    for ngram in ('unigrams', 'bigrams'):
      self.Run('%(fileutil)s -f rm %(namespace_prefix)s/'
               'entspelling-%(lang)s-all-' + ngram)

    self.Run('%(buildrtspelling)s'
             ' --command=filtermisspellings'
             ' --runtimedb_prefix=%(out)s'
             ' --misspellings_filter=%(tmp)s/ent-'
             ' --dump_to_files=%(tmp)s/ent-')

    # generate raw data from preexisting runtime data
    self.Run('%(buildrtspelling)s --command=dumptofiles'
             ' --runtimedb_prefix=%(out)s'
             ' --dump_to_files=%(tmp)s/'
             ' --language=%(lang)s')
    self.Run('cp %(tmp)s/ent-clean-unigrams %(tmp)s/docs.words.1')

    # customize query unigrams, bigrams and trigrams
    self.customizeUnigrams('%(tmp)s/query.words.1',
                           '%(tmp)s/ent-clean-unigrams')
    self.customizeBigrams('%(tmp)s/query.words.2',
                          '%(tmp)s/ent-clean-bigrams')
    self.customizeTrigrams('%(tmp)s/query.words.3')

    # customize original query unigrams
    self.customizeUnigrams('%(tmp)s/query.words.original.1',
                           '%(tmp)s/ent-unigrams')

    # sort original query unigrams by frequency
    self.sortUnigramsByFrequency('%(tmp)s/query.words.original.1',
                                 '%(tmp)s/query.words.original.1')


    # Build the spelling data structures from cleaned input.
    self.Run('%(buildrtspelling)s --command=makewordcodemap'
             ' --ngram_frequencies=%(tmp)s/query.words.original.1'
             ' --wordcodemap_prefix=%(tmp)s/%(lang)s.spelling.words')
    self.Run('%(buildrtspelling)s --command=addfrequencies'
             ' --ngram_frequencies=%(tmp)s/query.words.original.1'
             ' --wordcodemap_prefix=%(tmp)s/%(lang)s.spelling.words'
             ' --wordcodemap_freq_prefix=%(tmp)s/%(lang)s.spelling.words'
             ' --frequency_type=original')
    self.Run('%(buildrtspelling)s --command=addfrequencies'
             ' --ngram_frequencies=%(tmp)s/query.words.1'
             ' --wordcodemap_prefix=%(tmp)s/%(lang)s.spelling.words'
             ' --wordcodemap_freq_prefix=%(tmp)s/%(lang)s.spelling.words'
             ' --frequency_type=query')
    self.Run('%(buildrtspelling)s --command=addfrequencies'
             ' --ngram_frequencies=%(tmp)s/docs.words.1'
             ' --wordcodemap_prefix=%(tmp)s/%(lang)s.spelling.words'
             ' --wordcodemap_freq_prefix=%(tmp)s/%(lang)s.spelling.words'
             ' --frequency_type=document')
    self.Run('%(buildrtspelling)s --command=createconsonantindex'
             ' --wordcodemap_prefix=%(tmp)s/%(lang)s.spelling.words'
             ' --consonantindex_prefix=%(tmp)s/%(lang)s.spelling.ci')
    self.Run('%(buildrtspelling)s --command=makehashfilters'
             ' --wordcodemap_prefix=%(out)s.words'
             ' --wordcodemap_hashfilter=%(out)s.hash.words'
             ' --consonantindex_hashfilter=%(out)s.hash.canonicalizations'
             ' --hashfilter_size=%(filter_size)d')
    self.Run('%(buildrtspelling)s --command=makepairdb'
             ' --wordcodemap_prefix=%(out)s.words'
             ' --ngram_frequencies=%(tmp)s/query.words.2'
             ' --pairdb_prefix=%(out)s.pairs')
    self.Run('%(buildrtspelling)s --command=maketripledb'
             ' --wordcodemap_prefix=%(out)s.words'
             ' --ngram_frequencies=%(tmp)s/query.words.3'
             ' --tripledb_prefix=%(out)s.triples')
    self.Run('%(buildrtspelling)s --command=makemisspelldb'
             ' --wordcodemap_prefix=%(out)s.words'
             ' --misspell_edits_and_merges=%(tmp)s/misspell.1'
             ' --misspell_splits=%(tmp)s/misspell.2'
             ' --misspelldb_prefix=%(out)s.misspell')

    for suffix in ('bigrammodel', 'editmodel', 'contractions',
                   'filter.dirty.utf8', 'filter.equivalent.utf8'):
      # currently we just copy the existing bigram model file
      src = '%(enthome)s/../spelling-data/runtime/%(lang)s.spelling.' + suffix
      src %= self._opts
      if os.path.exists(src):
        self.Run('cp %s %%(out)s.%s' % (src, suffix))

    # remove temporary intermediate files
    for pattern_to_remove in ('docs.words.*', 'query.words.*', 'misspell.*',
                              'ent-*'):
      self.Run('%%(fileutil)s -f rm %%(tmp)s/%s' % pattern_to_remove)

    self.Run('mv -f %(tmp)s/*.spelling.* %(next_dir)s')
    self.Run('rmdir %(tmp)s')


def main(argv):
  if FLAGS.enthome is None:
    raise SystemExit('--enthome must be set')

  ec = entconfig.EntConfig(FLAGS.enthome)
  ec.Load()

  # ensure that the new serving directory exists and is empty
  idx_config_name = 'ENT_SPELL_SERVING_ID'
  current_idx = ec.var(idx_config_name)
  next_idx = current_idx + 1
  spell_path_pattern_prefix = '%s/spell-' % ec.var('ENT_SPELL_ROOT_DIR')
  current_dir = spell_path_pattern_prefix + str(current_idx)
  next_dir = spell_path_pattern_prefix + str(next_idx)

  RunCommand('rm -rf %s' % next_dir)
  RunCommand('mkdir -p -m 777 %s' % next_dir)  # TODO(mgp): check permissions

  # generate all spelling data, placing it in the new serving directory
  for lang in FLAGS.langs:
    sdg = SpellingDataGenerator(FLAGS.enthome, ec, current_dir, next_dir, lang)
    sdg.GenerateAll()

  # tell adminrunner about new serving directory and restart spellmixer
  ar = adminrunner_client.AdminRunnerClient(ec.var('MASTER'), 2100)
  ar.SetParam(idx_config_name, next_idx)
  ar.RestartServer('spellmixer')

  # remove older, unused spelling data directories, if they exist
  prefix_len = len(spell_path_pattern_prefix)
  for path in glob.glob(spell_path_pattern_prefix + '*'):
    # get integer suffix
    suffix = path[prefix_len:len(path)]
    # note: don't delete currently used data
    if int(suffix) < current_idx:
      RunCommand('rm -rf %s' % path)


if __name__ == '__main__':
  app.run()
