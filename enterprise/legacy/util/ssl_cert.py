#!/usr/bin/python2.4

"""
An SUID root script that manages SSL certificates.
The SSL host key is only readable by root, so we need to put all the code
that accesses it in this script. This prevents someone from hacking in as
nobody from being able to read the SSL key.

Usage:
ssl_cert.py getcertinfo {staging | installed} <enthome>
ssl_cert.py gencert <enthome> <hostname> <|organizational unit|>
  <|organization|> <|locality|> <|state|> <|country|> <email address>
ssl_cert.py getcsr <enthome>
ssl_cert.py verifystagingcert <enthome>
ssl_cert.py installcert <enthome>
ssl_cert.py verifystagingkey <enthome>
ssl_cert.py installkey <enthome>
ssl_cert.py generatekey <enthome>

where |text| means URL-encoded text

More usage (pn): To work with Certificate Authorities and Certificate Revocation Lists.
ssl_cert.py getcommonnames <cadir>
ssl_cert.py importcas <cadatafile> <cadir>
ssl_cert.py removeca  <subject hash> <cadir> <crldir>
ssl_cert.py importcrl <crlfile> <cadir> <crldir>
ssl_cert.py hascrl <subject hash> <crldir>
ssl_cert.py removecrl <subject hash> <crldir>

"""

import sys
import commands
import tempfile
import urllib
import os
import types
import time
import glob

CERT_FILENAME = '%s/local/conf/certs/server.crt'
STAGINGCERT_FILENAME = '%s/local/conf/staging.crt'
KEY_FILENAME = '%s/local/conf/certs/server.key'
STAGINGKEY_FILENAME = "%s/local/conf/staging.key"
JKS_FILENAME = '%s/local/conf/server.p12'
ORGUNIT_LINE = 'OU = %s'
CONFIG_TEMPLATE = """
[ req ]
distinguished_name     = req_distinguished_name
prompt                 = no
extensions             =
utf8                   = yes

[ req_distinguished_name ]
CN = %(CN)s
%(ORGUNIT)s
O = %(O)s
L = %(L)s
ST = %(ST)s
C = %(C)s
emailAddress = %(emailAddress)s
"""

OPENSSL_BIN = '/usr/bin/openssl'
RM_BIN = '/bin/rm'
CP_BIN = '/bin/cp'
CAT_BIN = '/bin/cat'
CHMOD_BIN = '/bin/chmod'
SERVICE_BIN = '/sbin/service'
CERT_LIFETIME_IN_DAYS = 730
CA_CERT_EXT = '.0'
CRL_EXT = '.r0'

def GetCertInfo(whichcert, enthome):
  """
  Writes a bunch of information about the currently installed certificate
  to stdout. output is
  hostname, organizational unit, organization, locality, state, country, email,
  notValidBeforeDate, notValidAfterDate (each on a newline) on success
  or an error message on failure (so the admin runner client can log the msg).
  Returns value of this function is 0 on success, 1 on failure
  """

  if whichcert == 'installed':
    filename = CERT_FILENAME % enthome
  elif whichcert == 'staging':
    filename = STAGINGCERT_FILENAME % enthome
  else:
    print 'Argument to GetCertInfo must be "installed" or "staging" '
    return 1

  subjcode, subjresult = commands.getstatusoutput(
    '%s x509 -in %s -subject -noout -nameopt multiline -nameopt sname '
    '-nameopt utf8' % (OPENSSL_BIN, filename))
  datecode, dateresult = commands.getstatusoutput(
    '%s x509 -in %s -dates -noout' % (OPENSSL_BIN, filename))

  if subjcode != 0 or datecode != 0:
    print "Couldn't read certificate [%s] info [%s] [%s]" % (filename,
                                                             subjresult,
                                                             dateresult)
    return 1

  lines = subjresult.split('\n')
  lines.extend(dateresult.split('\n'))
  # all the certificate fields are optional, so give the map default values
  res = { 'CN' : '', 'OU' : '', 'O' : '', 'L' : '', 'ST' : '',
          'C' : '', 'emailAddress' : '', 'notBefore' : '', 'notAfter' : '',
         }
  for line in lines:
    pos = line.find('=')
    if pos > 0:
      res[line[:pos].strip()] = line[pos+1:].strip()

  print '%(CN)s\n%(OU)s\n%(O)s\n%(L)s\n%(ST)s\n%(C)s\n%(emailAddress)s\n' \
        '%(notBefore)s\n%(notAfter)s\n' % res

  return 0

def GenConfigFile(hostname, orgunit, organization, locality, state, country,
                  email_address):
  """ Creates an SSL config file, which is then used to generate a
  certificate, or a certificate signing request
  the hostname is written to this config file
  Returns the filename that the configuration was saved in
  """
  configFile = tempfile.mktemp()
  config = open(configFile, 'w')
  orgunit_line = ''
  if orgunit:
    orgunit_line = ORGUNIT_LINE % orgunit
  config.write(CONFIG_TEMPLATE % {'CN':hostname, 'ORGUNIT':orgunit_line,
                                  'O':organization, 'L':locality, 'ST':state,
                                  'C':country, 'emailAddress':email_address})
  config.close()
  return configFile

def MakeJavaCert(enthome):
  """ Generates the Java PKCS#12 format certificate from the Apache PEM
  encoded certificate. this should be called every time the Apache
  cert changes, to keep things in sync.
  Returns the return code that the program should have
  """
  jks_filename = JKS_FILENAME % enthome
  # removing -noiter and -nomaciter increases security but breaks IE4.0
  retcode, result = commands.getstatusoutput(
    '%s %s %s | %s pkcs12 -export -out %s -noiter -nomaciter '
    '-password "pass:gsa"' %
    ( CAT_BIN, KEY_FILENAME % enthome, CERT_FILENAME % enthome, OPENSSL_BIN, jks_filename ))

  if retcode != 0:
    print("Couldn't create PKCS#12 format keystore: %s" % result)
    return 1

  return 0

def GenCert(enthome, hostname, orgunit, organization, locality, state, country,
            email_address):
  """Generates a staging certificate.
  Returns the return code that the program should have.
  """

  configFile = GenConfigFile(hostname, orgunit, organization, locality, state,
                             country, email_address)
  retcode, result = commands.getstatusoutput(
    '%s req -x509 -new -key %s -out %s -days %d -config %s ' %
    (OPENSSL_BIN, ChooseKey(enthome), STAGINGCERT_FILENAME % enthome,
     CERT_LIFETIME_IN_DAYS, configFile))
  rmcode, rmstatus = commands.getstatusoutput('%s %s' % (RM_BIN, configFile))

  if retcode != 0 or rmcode != 0:
    print("Couldn't generate certificate: %s" % result)
    return 1
  return 0

def GetDataFromCert(enthome):
  subjcode, subjresult = commands.getstatusoutput(
    '%s x509 -in %s -subject -noout -nameopt multiline -nameopt sname '
    '-nameopt utf8' % (OPENSSL_BIN, CERT_FILENAME % enthome))
  datecode, dateresult = commands.getstatusoutput(
    '%s x509 -in %s -dates -noout' % (OPENSSL_BIN, CERT_FILENAME % enthome))

  if subjcode != 0 or datecode != 0:
    return None

  lines = subjresult.split('\n')
  lines.extend(dateresult.split('\n'))

  hostname = None
  orgunit = None
  organization = None
  locality = None
  state = None
  country = None
  email_address = None

  for line in lines:
    pos = line.find('=')
    if pos > 0:
      key = line[:pos].strip()
      if key  == 'CN':
        hostname = line[pos+1:].strip()
      elif key == 'OU':
        orgunit = line[pos+1:].strip()
      elif key == 'O':
        organization = line[pos+1:].strip()
      elif key == 'L':
        locality = line[pos+1:].strip()
      elif key == 'ST':
        state = line[pos+1:].strip()
      elif key == 'C':
        country = line[pos+1:].strip()
      elif key == 'emailAddress':
        email_address = line[pos+1:].strip()

  return hostname, orgunit, organization, locality, state, country, \
         email_address

def GetCSR(enthome):
  """ Returns a CSR for the given hostname. This CSR can then be
  signed by a root CA.
  Returns the return code that the program should have
  """
  hostname, orgunit, organization, locality, state, country, email_address = \
            GetDataFromCert(enthome)
  configFile = GenConfigFile(hostname, orgunit, organization, locality, state,
                             country, email_address)
  retcode, result = commands.getstatusoutput(
    '%s req -new -key %s -days %d -config %s 2> /dev/null' %
    (OPENSSL_BIN, KEY_FILENAME % enthome, CERT_LIFETIME_IN_DAYS, configFile))

  rmcode, rmstats = commands.getstatusoutput('%s %s' % (RM_BIN, configFile))

  if retcode != 0 or rmcode != 0:
    print "Couldn't generate CSR: %s" % result
    return 1
  else:
    print result
    return 0

# if the staging key appears valid (exists and non zero) return it's file name
# otherwise return the key file name
def ChooseKey(enthome):
  try:
    staging_key_size = len(open(STAGINGKEY_FILENAME % enthome, "r").read())
  except Exception:
    staging_key_size = 0
  if staging_key_size > 0:
    return STAGINGKEY_FILENAME % enthome
  else:
    return KEY_FILENAME % enthome

def VerifyStagingCert(enthome):
  """ Tries to construct a PKCS#12 file from the staging certificate
  we do this so if the staging certificate is invalid, or doesn't correspond
  with this host's key, we will detect it here.
  Returns the return code of this program, which is 1 on failure
  0 on success.
  """
  # removing -noiter and -nomaciter increases security but breaks IE4.0
  retcode, result = commands.getstatusoutput(
    '%s %s %s | %s pkcs12 -export -noiter -nomaciter -password "pass:"'
    % (CAT_BIN, ChooseKey(enthome), STAGINGCERT_FILENAME % enthome,
       OPENSSL_BIN))
  if retcode != 0:
    print "Couldn't verify certificate: %s" % result
    return 1

  return 0


def InstallCert(enthome):
  """ Copies the staging certificate over to the installed certificate
  this is installed in 2 places, so both Apache and the entfrontend
  can find it. returns the return code that this program should have
  namely, 0 on success, 1 on failure.
  """
  retcode, result = commands.getstatusoutput(
    '%s %s %s && %s 600 %s' % (CP_BIN, STAGINGCERT_FILENAME % enthome,
                               CERT_FILENAME % enthome, CHMOD_BIN,
                               CERT_FILENAME % enthome))
  if retcode != 0:
    print result
    return 1

  retcode, result = commands.getstatusoutput('%s %s' %
                                             (RM_BIN, STAGINGCERT_FILENAME %
                                              enthome))
  if retcode != 0:
    print result
    return 1

  return MakeJavaCert(enthome)

def VerifyStagingKey(enthome):
  """ Checks if the staging key is valid
  Returns the return code of this program, which is 1 on failure
  0 on success.
  """
  # removing -noiter and -nomaciter increases security but breaks IE4.0
  retcode, result = commands.getstatusoutput(
    '%s rsa -in %s' % (OPENSSL_BIN, STAGINGKEY_FILENAME % enthome))
  if retcode != 0:
    print "Couldn't verify key: %s" % result
    return 1

  return 0

def GenerateStagingKey(enthome):
  """ Generates a staging key """

  retcode, result = commands.getstatusoutput(
    '%s genrsa -out %s 1024' % (OPENSSL_BIN, STAGINGKEY_FILENAME % enthome))

  if retcode != 0:
    print "Couldn't generate RSA private key: %s" % result
    return 1

  return 0

def InstallKey(enthome):
  """ Copies the staging key to the proper location.
  returns 0 on success, 1 on failure.
  """
  retcode, result = commands.getstatusoutput(
    '%s %s %s && %s 600 %s' % (CP_BIN, STAGINGKEY_FILENAME % enthome,
                               KEY_FILENAME % enthome, CHMOD_BIN,
                               KEY_FILENAME % enthome))
  if retcode != 0:
    print result
    return 1

  retcode, result = commands.getstatusoutput('%s %s' %
                                             (RM_BIN, STAGINGKEY_FILENAME %
                                              enthome))
  if retcode != 0:
    print result
    return 1

  return 0


# Write data to a file, data can be a list or a string.
def writeToFile(data, filename, overwrite=1):
  try:
    if os.path.exists(filename) and not overwrite:
      return 1

    f = open(filename, 'w')
    if isinstance(data, types.ListType):
      f.writelines(data)
    else:
      f.write(data)
    f.close()
  except IOError:
    return 1
  return 0

# Read and return content of a file.
def readFromFile(filename):
  try:
    if not os.path.exists(filename):
      return None
    f = open(filename, 'r')
    lines = f.readlines()
    return ''.join(lines)
  except IOError:
    return None

def _IsStructTmGreaterThan(t1, t2):
  """Compare two tuples representing 'struct tm' and return true if
  the first one has a larger date than the second one.

  We assume both tuples have the same timezone, as in our normal use
  case they'll both be GMT."""
  return t1 > t2 # qed

# Return subject common name of a given certificate.
def GetCertCommonName(cadir, certfile):
  subjcode, subjresult = commands.getstatusoutput(
  '%s x509 -in %s -hash -enddate -subject -noout -nameopt oneline -nameopt sname '
  '-nameopt utf8' % (OPENSSL_BIN, os.path.join(cadir,certfile)))

  if subjcode != 0:
    return None
  lines = subjresult.split('\n')

  if lines[0] != certfile[0:-2]:
    return None

  line = lines[1]
  pos = line.find('=')
  if pos <= 0 or line[:pos].strip() != 'notAfter':
    return None

  line = line[pos+1:-4].strip()  # drop 'GMT' suffix
  expiredTime = time.strptime(line, '%b %d %H:%M:%S %Y')
  currentTime = time.gmtime()
  if _IsStructTmGreaterThan(currentTime, expiredTime):
    expiry = 1
  else:
    expiry = 0

  # Expecting a line like
  # "subject= C = US, ST = California, L = Mountain View"
  subj = lines[2]
  if subj:
    # And our goal is to strip off the 'subject=' prefix
    goal = 'subject='
    if subj.startswith(goal):
      subj = subj[len(goal):]
    return (expiry, subj.strip())
  else:
    # Can't happen but since it did and the cert was apparently somehow imported
    # let's assume the cert is otherwise valid and return something so that the
    # admin can at least get at it on the admin console. If we return None then
    # the problem is invisible.
    return (expiry, "no subject") 


# Return list of common names from all trusted CAs in given directory
# Each CA cert is stored in a file with filename be its subject hash
# appened with .0
# Return: <subject hash> <commonName>
def getCommonNames(cadir):
  """Read all common names from given directory of trusted CAs"""
  if not os.path.exists(cadir) or not os.path.isdir(cadir):
    print 'There is no trusted CAs.'
    return 1

  result = []
  for filename in glob.glob(cadir + '/*' +CA_CERT_EXT):
    (filepath, filename) = os.path.split(filename)
    line = GetCertCommonName(cadir, filename)
    if line != None:
      result.append('%s %s %d' % (line[1], filename[0:-2], line[0]))
  result.sort()

  # switch filename (subject hash) to front.
  for line in result:
    pos = line.rindex(' ', 0, line.rindex(' '))
    line = '%s %s' % (line[pos+1:], line[:pos])
    print line
  return 0


# Import trusted CAs to separated files into directory cadir.
# Filenames are <subject hash>.0 of those CAs.
# Return 0 on success; 1 on error, error code is printed in output.
# TODO(meghna) : Add multiple certs for the same CA as <hash>.1, <hash>.2 etc.
def importCAs(cafile, cadir):
  errorcode = 0
  newfiles = []
  hashes = {}
  try:
    if not os.path.exists(cadir):
      os.mkdir(cadir)

    lines = open(cafile, 'r').readlines()
    while len(lines) > 2:
      path = os.path.join(cadir, 'ssl_cert.tmp')
      consumed = extractOneRecord(lines, path, '-----', '-----')

      if consumed == -1:
        # Cannot parse the file
        os.remove(path)
        errorcode = -2
        break
      lines = lines[consumed:]

      # verify the cert and get the subject hash
      subjhashcode, subjhashresult = commands.getstatusoutput(
        '%s x509 -inform PEM -in %s -noout -hash' % (OPENSSL_BIN, path))

      subjhashcode = subjhashcode / 256
      if subjhashcode != 0:
        os.remove(path)
        errorcode = -3
        break
      elif hashes.has_key(subjhashresult):
        print ("Subject hash %s has already existed in this CA file" %
               subjhashresult)
        errorcode = -5
        break
      else:
        newfile = os.path.join(cadir, '%s.new' % subjhashresult)
        os.rename(path, newfile)
        hashes[subjhashresult] = subjhashresult
        newfiles.append(newfile)

  except IOError, e:
    print str(e)
    errorcode = -4


  if errorcode != 0:
    print '%d' % errorcode
    for file in newfiles:
      os.remove(file)
    if os.path.exists(path):
      os.remove(path)
    return 1

  # so far so good, accept those new CAs
  retcode = 0
  for file in newfiles:
    try:
      os.rename(file, file[0:-3] + '0')
    except OSError,e :
      print "File: %s, Error %s" % (file, e)
      retcode = 1

  return retcode


# Remove a trusted CA, given subject hash.
# Return 0 on success; 1 otherwise.
def removeCA(hash, cadir):
  path = os.path.join(cadir, hash + CA_CERT_EXT)
  if not os.path.exists(path):
    return 0

  try:
    os.remove(path)
  except Exception:
    return 1
  return 0

# Import a CRL of a known trusted CA.
# The CRL issuer subject hash is checked against that of those trusted CAs
# known by the system. CRL name if of the form <hash>.r0
# Return 0 on success; 1 on error, error code is printed in output.
# TODO(meghna) : Add multiple CRLs for the same CA as <hash>.r1, <hash>.r2 etc.
def importCRL(crlfile, cadir, crldir):
  try:
    errorcode = 0
    if not os.path.exists(crldir):
      os.mkdir(crldir)

    cmdcode, cmdresult = commands.getstatusoutput(
      '%s crl -inform PEM -in %s -noout -hash'
      % (OPENSSL_BIN, crlfile))
    cmdcode = cmdcode / 256

    if cmdresult.find('unable to load CRL') == 0:
      errorcode = -2
    else:
      lines = cmdresult.split('\n')
      if (len(lines) != 1):
        errorcode = -1   ## unexpected, make it unknown error
      else:
        hash = lines[0]

        # check for existing trusted CA
        capath = os.path.join(cadir, hash + CA_CERT_EXT)
        if not os.path.exists(capath):
          # The CRL has unknown issuer
          os.remove(crlfile)
          errorcode = -3
        else:
          # has known issuer. Take the CRL.
          os.rename(crlfile, os.path.join(crldir, hash + CRL_EXT))

  except IOError: ## any command throws this??
    errorcode = -4

  if errorcode != 0:
    print '%d' % errorcode
    return 1

  return 0

# Return true if there is a CRL with given subject hash in the crl directory
def hasCRL(hash, crlDir):
  if os.path.exists(os.path.join(crlDir, hash + CRL_EXT)):
    return 1
  else:
    return 0

# Remove the CRL with given subject hash in the crl directory
def removeCRL(hash, crlDir):
  path = os.path.join(crlDir, hash + CRL_EXT)
  if not os.path.exists(path):
    return 0

  try:
    os.remove(path)
  except IOError, e:
    print str(e)
    return 1
  return 0

# Extract a number of lines from startline signal until it reaches lastline signal
# and write that to @toFile
# Return (index of lastline)+1 on success; -1 otherwise.
def extractOneRecord(lines, toFile, startline, lastline):
  started = 0
  extracted = []
  count = 0
  for line in lines:
    count = count + 1
    if not started and not line.find(startline) == 0:
      continue
    extracted.append(line)
    if started and line.find(lastline) == 0:
      break
    elif line.find(startline) == 0:
      started = 1

  if len(extracted) != 0 and 0 == writeToFile(extracted, toFile):
    return count
  return -1


if __name__ == '__main__':

  if (len(sys.argv) == 4 and sys.argv[1] == 'getcertinfo'):
    sys.exit(GetCertInfo(sys.argv[2], sys.argv[3]))
  elif (len(sys.argv) == 10 and sys.argv[1] == 'gencert'):
    sys.exit(GenCert(sys.argv[2], sys.argv[3],
                      urllib.unquote_plus(sys.argv[4]),
                      urllib.unquote_plus(sys.argv[5]),
                      urllib.unquote_plus(sys.argv[6]),
                      urllib.unquote_plus(sys.argv[7]),
                      urllib.unquote_plus(sys.argv[8]), sys.argv[9]))
  elif (len(sys.argv) == 3 and sys.argv[1] == 'getcsr'):
    sys.exit(GetCSR(sys.argv[2]))
  elif (len(sys.argv) == 3 and sys.argv[1] == 'verifystagingcert'):
    sys.exit(VerifyStagingCert(sys.argv[2]))
  elif (len(sys.argv) == 3 and sys.argv[1] == 'installcert'):
    sys.exit(InstallCert(sys.argv[2]))
  elif (len(sys.argv) == 3 and sys.argv[1] == 'verifystagingkey'):
    sys.exit(VerifyStagingKey(sys.argv[2]))
  elif (len(sys.argv) == 3 and sys.argv[1] == 'installkey'):
    sys.exit(InstallKey(sys.argv[2]))
  elif (len(sys.argv) == 3 and sys.argv[1] == 'generatekey'):
    sys.exit(GenerateStagingKey(sys.argv[2]))

  elif len(sys.argv) == 3 and sys.argv[1] == 'getcommonnames':
    sys.exit(getCommonNames(sys.argv[2]))
  elif len(sys.argv) == 4 and sys.argv[1] == 'importcas':
    sys.exit(importCAs(sys.argv[2], sys.argv[3]))
  elif len(sys.argv) == 4 and sys.argv[1] == 'removeca':
    sys.exit(removeCA(sys.argv[2], sys.argv[3]))
  elif len(sys.argv) == 5 and sys.argv[1] == 'importcrl':
    sys.exit(importCRL(sys.argv[2], sys.argv[3], sys.argv[4]))
  elif len(sys.argv) == 4 and sys.argv[1] == 'hascrl':
    sys.exit(hasCRL(sys.argv[2], sys.argv[3]))
  elif len(sys.argv) == 4 and sys.argv[1] == 'removecrl':
    sys.exit(removeCRL(sys.argv[2], sys.argv[3]))

  else:
    sys.exit(__doc__)
