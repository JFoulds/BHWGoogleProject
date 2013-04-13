#!/usr/bin/python2.4
#
# Copyright (c) 2004 and onwards Google, Inc.
#
# Author: Colin Smith <colins@google.com>
# Modified by: Mark D. Roth <roth@google.com>

import datetime
import math
import re
import socket
import time

from google3.chubby.python.public import pychubbyutil
from google3.net.proto import ProtocolBuffer
from google3.net.rpc.python import pywraprpc
from google3.borg.monitoring.base import monitoring_pb
from google3.borg.monitoring.borgmon import monitor_pb


class BorgmonEvalError(Exception):
  """Base class for all borgmon_eval_lib errors."""


class BorgmonUnreachableError(BorgmonEvalError):
  """An error occurred while trying to talk to the borgmon instance."""


class BorgmonExpressionError(BorgmonEvalError):
  """The borgmon could not evaluate the expression."""


class BorgmonEvalLibError(BorgmonEvalError):
  """A utility function failed within this library."""


_last_server = None
_clientrpc_client = None

def BorgmonEval(server, expression, return_as_list=False):
  """
  THIS INTERFACE IS DEPRECATED!  You should be using the
  StubbyBorgmonEvalClient class below instead.

  Asks the specified server to evaluate the specified expression.
  By default, returns the result as a dict of the following form:

    { 'label' : [ (timestamp, value), ... ], ... }

  If the optional argument return_as_list is set to true, returns the
  result as a list of the following form:

    [ ( 'label', [ (timestamp, value), ... ] ), ... ]

  Raises BorgmonEvalError on error.

  The timestamp in the data series has no timezone
  and is thus printed in the local timezone where the invoking
  program is running.  Consider setting the timezone to PDT:
    os.environ['TZ'] = 'US/Pacific'
    time.tzset()
  """
  global _last_server
  global _clientrpc_client

  if server != _last_server:
    _clientrpc_client = ClientRPCBorgmonEvalClient(server)
    _last_server = server

  return _clientrpc_client.Eval(expression, return_as_list=return_as_list)


class AbstractBorgmonEvalClient(object):
  """An interface for remote evaluation clients."""

  def __init__(self, server):
    self.CheckAndSetServer(server)

  def Server(self):
    """Returns the current server."""
    return self._server

  def _SetServer(self, server):
    """Sets the server.  For use by subclasses."""
    self._server = server

  def _SeriesValue(self, series):
    """Return the "value" portion of the series pb as a Python object.

    If the series has points, we convert series.point_list() to a Python list
    of tuples (time, value) where each value is either a float or a string.
    If the series has no points, we return an empty list.
    """
    points = series.point_list()
    result = []
    if series.stringvalue_size() == 0:
      # Not a string-valued series
      return [(p.time(), p.value()) for p in points]
    else:
      # String-valued points
      strings = [s.value() for s in series.stringvalue_list()]
      return [(p.time(), strings[int(p.value())]) for p in points]

  def _MungeResult(self, resp, return_as_list=True):
    """Munges the response into the expected result.

    The return_as_list parameter is used by the deprecated
    BorgmonEval() interface.  No other caller should use it.
    """
    if return_as_list:
      result = [(s.name(), self._SeriesValue(s)) for s in resp.series_list()]
    else:
      result = {}
      for series in resp.series_list():
        result[series.name()] = self._SeriesValue(series)
    return result

  def CheckAndSetServer(self, server):
    """Check the validity of the server, and if valid, switch to it.

    This must be implemented by subclasses.  If the server is valid, the
    subclass must call self._SetServer() to set the server; otherwise, a
    BorgmonEvalError exception must be raised.
    """
    raise NotImplementedError

  def Eval(self, expression):
    """Evaluate an expression.

    This must be implemented by subclasses.
    """
    return NotImplementedError


class ClientRPCBorgmonEvalClient(AbstractBorgmonEvalClient):
  """A ClientRPC remote evaluation client.

  THIS INTERFACE IS DEPRECATED!  You should be using the
  StubbyBorgmonEvalClient class below instead.
  """

  def __init__(self, server, dns_resolver=socket.gethostbyname,
               bns_resolver=pychubbyutil.ResolveBNSName):
    self._dns_resolver = dns_resolver
    self._bns_resolver = bns_resolver
    super(ClientRPCBorgmonEvalClient, self).__init__(server)

  def _ResolveBNSName(self, server):
    try:
      ip_port = self._bns_resolver(server)
    except pychubbyutil.Error, e:
      raise BorgmonUnreachableError('%s: %s' % (server, e))
    return '%s:%d' % ip_port

  def CheckAndSetServer(self, server):
    if server.startswith('/bns/'):
      self._ResolveBNSName(server)
      # if the /bns name could not be resolved, an exception would be
      # raised, so if we got here we know that the /bns name is valid
      self._SetServer(server)
    else:  # not /bns
      # strip off ":port" suffix
      idx = server.find(':')
      if idx >= 0:
        dns_name = server[:idx]
      else:
        dns_name = server
      # do DNS lookup
      try:
        self._dns_resolver(dns_name)
      except socket.gaierror, e:
        raise BorgmonUnreachableError('%s: %s' % (dns_name, e[1]))
      self._SetServer(server)

  def Eval(self, expression, return_as_list=True):
    """The return_as_list parameter is used by the deprecated
    BorgmonEval() interface.  No other caller should use it."""
    req = monitor_pb.EvaluateRequest()
    req.set_expression(expression)
    resp = monitor_pb.Value()

    server = self.Server()
    if server.startswith('/bns/'):
      server = self._ResolveBNSName(server)

    try:
      req.sendCommand(server, '/evalproto', resp)
    except socket.error, e:
      raise BorgmonUnreachableError('socket error: %s' % e)
    except ProtocolBuffer.ProtocolBufferReturnError, e:
      raise BorgmonExpressionError('protocol buffer return error: %s' % e)
    except ProtocolBuffer.ProtocolBufferDecodeError, e:
      raise BorgmonExpressionError('protocol buffer decode error: %s' % e)

    return self._MungeResult(resp, return_as_list=return_as_list)


class StubbyBorgmonEvalClient(AbstractBorgmonEvalClient):
  """A Stubby remote evaluation client."""

  def __init__(self, server, resolver_timeout=10, request_deadline=10,
               stub_params=pywraprpc.BalancedStubParameters.NewNonEmpty,
               new_stub=monitor_pb.RuleEvaluator.NewStub,
               lookupserver_integration=False,
               downsampling_res=0,
               downsampling_type=monitoring_pb.DownsamplingSpec.AVG):
    """
    Args:
      server: The name of the server.
      resolver_timeout: Timeout for name resolution (seconds).
      request_deadline: Deadline for request RPCs (seconds).
      lookupserver_integration: Whether or the consult_lookupserver bit in
        the request pb is set. (only applicable if the target server is a
        borgmon version 1.5 or newer).
    """
    self._resolver_timeout = resolver_timeout
    self._request_deadline = request_deadline
    self._stub_params = stub_params
    self._new_stub = new_stub
    self._lookupserver_integration = lookupserver_integration
    self._downsampling_res = downsampling_res
    self._downsampling_type = downsampling_type
    super(StubbyBorgmonEvalClient, self).__init__(server)

  def LookupserverIntegration(self):
    return self._lookupserver_integration

  def SetLookupserverIntegration(self, lookupserver_integration):
    self._lookupserver_integration = lookupserver_integration

  def DownsamplingRes(self):
    return self._downsampling_res

  def SetDownsamplingRes(self, downsampling_res):
    self._downsampling_res = downsampling_res

  def DownsamplingType(self):
    return self._downsampling_type

  def SetDownsamplingType(self, downsampling_type):
    self._downsampling_type = downsampling_type

  def CheckAndSetServer(self, server):
    # TODO(roth): This will actually return success if you pass it a
    # clearly bogus server name like "/moom", because the underlying
    # LoadBalancerMonitor code is only checking whether an RPC channel
    # has been created, not whether that channel is for a valid server.
    params = self._stub_params(
        'RoundRobin', server, timeout=self._resolver_timeout,
        security_protocol='loas')
    # Check that the call didn't timeout populating the list of servers.
    if not params.GetNumServers():
      raise BorgmonUnreachableError('no servers available for %s' % server)

    self._SetServer(server)
    self._evaluator = self._new_stub(params)
    self._rpc = pywraprpc.RPC()
    self._rpc.set_deadline(self._request_deadline)

  def Eval(self, expression, return_errors=False):
    """Evaluate an expression.

    Args:
      expression: The expression to evaluate.
      return_errors: Boolean.  If True, will return fatal and non-fatal
                     errors along with the result.

    Returns:
      If return_errors is True, we return:
        (result, fatal_errors, non_fatal_errors)
      where fatal_errors and non_fatal_errors are strings.
      Otherwise, we return only the result.

    Raises:
      BorgmonExpressionError: if unable to properly evaluate the expression
      BorgmonUnreachableError: if unable to properly communicate with the
          borgmon
    """
    req = monitor_pb.EvaluateManyRequest()
    req.add_requests().set_expression(expression)
    # Lookupserver options:
    req.set_consult_lookupserver(self._lookupserver_integration)
    downsampling_spec = req.mutable_downsampling()
    downsampling_spec.set_resolution(self._downsampling_res)
    downsampling_spec.add_aggregation(self._downsampling_type)

    try:
      resp = self._evaluator.EvaluateMany(req, rpc=self._rpc)
    except pywraprpc.RPCException, e:
      raise BorgmonUnreachableError(
          'stubby error: %s (status=%s, application_error=%s)' %
          (e, e.status, e.application_error))
    if resp.values_size() > 1:
      raise BorgmonExpressionError('server returned multiple results')
    if resp.values_size():
      retval = self._MungeResult(resp.values(0))
    else:
      # this can happen if we get back a fatal error
      retval = []
    if return_errors:
      return (retval, resp.fatal_errors(), resp.non_fatal_errors())
    else:
      return retval


def DeltaSeconds(d):
  """Convert a datetime timerange object back into seconds"""
  return d.seconds + d.days * 86400


def Integrate(time_value_list):
  """
  Takes a list of timestamp/value pairs (as produced by BorgmonEval()
  and "integrates" the values over the time-span to produce a total
  area under the line.  Usefull to convert a rate type expression into
  a total sum
  """
  time_prev = None
  time_cur = None
  data_prev = None
  count = 0.0
  for timestamp, data_cur in time_value_list:
    time_cur = datetime.datetime.fromtimestamp(timestamp)
    if time_prev is not None:
      count += (DeltaSeconds(time_cur - time_prev) *
        (data_prev + ((data_cur - data_prev) / 2)))
    time_prev = time_cur
    data_prev = data_cur
  return count


def median(values):
  values.sort()
  if len(values) == 0:
    return None
  elif (len(values) % 2) == 1:
    return values[len(values)//2]
  else:
    return float(values[len(values)//2-1] + values[len(values)//2]) / 2


class TimeSeriesBin(object):
  """
  An object for matching data across timeseries, by seperating data into
  bins that can be compared 1:1

  Args:
    bin_time_delta : the width of each bin
    start_time     : the start time of the first bin
    end_time       : the end time of all bins.
                     If (end_time - start_time) % bin_time_delta is non-zero,
                     end_time will be greater than the end time of the last
                     bin.
    bin_alg        : when multiple values fall within a single bin, this
                     function is applied to determine the appropriate value to
                     assign to the bin
  """

  def __init__(self, bin_time_delta, start_time, end_time=None,
               bin_alg=median):
    self._enum = {}
    self._bin_time_delta = bin_time_delta
    self._start_time = start_time
    self._end_time = end_time
    if end_time is None:
      end_time = time.time()
    self._bin_alg = bin_alg
    self._num_bins = int(math.ceil(float(end_time-start_time) / bin_time_delta))
    # maps timeseries to values in each bin, e.g.
    # { timeseries1 : [ value0, value1, ...],
    #   timeseries2 : [ value0, value1, ...],
    #   ... }
    self._contents = {}

  def _AssignToBin(self, name, bin, values, bin_alg=None):
    """
    Sets the value of a timeseries in a given bin.

    Args:
      name    : name of the timeseries to set value for
      bin     : index of the bin to set value for
      values  : values that fall within the bin (to which bin_alg is applied)
      bin_alg : (see explanation in class-level comments above)
    """
    if bin_alg is None:
      bin_alg = self._bin_alg
    self._contents[name][bin] = apply(bin_alg, [values])

  def Get(self, name, bin):
    return self._contents[name][bin]

  def GetAllTimeSeries(self):
    return self._contents

  def GetTimeSeries(self, name):
    return self._contents[name]

  def Keys(self):
    return self._contents.keys()

  def NumBins(self):
    return self._num_bins

  def BinStartTime(self, bin):
    return self._start_time + bin * self._bin_time_delta

  def PackTimeseries(self, name, ts, bin_alg=None):
    """
    Loads a timeseries into this object

    Args:
      name    : name of the timeseries to insert
      ts      : list of (timestamp, value) pairs for this timeseries.
                NOTE: we assume that the pairs belonging to this tuple are
                sorted by timestamps.  Violating this assumption will result
                in missing data.
      bin_alg : (see explanation in class-level comments above)
    """
    self._contents[name] = [None] * self._num_bins
    bin = 0
    bin_values = []
    for timestamp, value in ts:
      if timestamp > self._end_time:
        break
      if timestamp > self.BinStartTime(bin+1):
        if len(bin_values) > 0:
          self._AssignToBin(name, bin, bin_values, bin_alg=bin_alg)
          bin_values = []
        bin += 1
        while timestamp > self.BinStartTime(bin+1):
          bin += 1
      bin_values.append(value)
    if (bin < self._num_bins and len(bin_values) > 0):
      self._AssignToBin(name, bin, bin_values, bin_alg=bin_alg)
      bin += 1

  def PackBorgmonQuery(self, data_source, expr, bin_alg=None):
    """
    Loads timeseries from a borgmon query into this object

    Args:
      data_source : the borgmon/tslookupserver to query
      expr        : expression to send to data_source
      bin_alg : (see explanation in class-level comments above)
    """
    result = BorgmonEval(data_source, expr)
    for name, ts in result.items():
      self.PackTimeseries(name, ts, bin_alg)


def ParseDuration(fmt):
  """
  Converts a string such as '3h' into seconds

  Definitions are stored in time_units[] struct of
  //depot/google3/borg/monitoring/base/duration.cc
  """
  num = fmt[:-1]
  try:
    if fmt.endswith('s'):
      return float(num)
    if fmt.endswith('m'):
      return float(num) * 60.0
    if fmt.endswith('h'):
      return float(num) * 60.0 * 60.0
    if fmt.endswith('d'):
      return float(num) * 24.0 * 60.0 * 60.0
    # no units, default to seconds
    return float(fmt)
  except ValueError:
    raise BorgmonEvalLibError('invalid duration syntax: %s' % fmt)


def ConstructQueryFromLabels(labels):
  """Reconstruct a borgmon query from a dictionary of labels.

  No special quoting is performed; it is assumed that the values of the labels
  are already quoted or escaped as necessary.

  See http://wiki/Main/BorgmonVariableReferences for full details of the
  borgmon variable reference syntax.

  Args:
    labels: dict of labels in the query.

  Returns:
    string containing the reconstructed borgmon query, in the format:
      myvar{label1=value1,label2=value2}
  """
  var = labels.get('var', '')
  pairs = []
  # sorted() is only for determinism in unittesting. Doesn't harm anything.
  for k,v in sorted(labels.items()):
    if k == 'var':
      # We handled this already.
      continue
    pairs.append('%s=%s' % (k,v))
  if not pairs:
    return var
  return '%s{%s}' % (var, ','.join(pairs))


def ParseLabels(query, for_tslookup=False):
  """Parse a borgmon query into its label sets.

  This does not support any special escaping or quoting; values that are
  quoted, escaped or contain commas are potential hazards. Use at your own
  risk.

  See http://wiki/Main/BorgmonVariableReferences for full details of the
  borgmon variable reference syntax.

  Args:
    query: borgmon query to dissect
    for_tslookup: set true if parsing a TSLookup query (dot-notation parsing
                  differs; see the ParseDotNotation* methods).

  Returns:
    a dict of labels mapped to values.

  Raises:
    BorgmonEvalLibError: if syntax of query was incorrect
  """
  labels = {}

  if '{' in query:
    stem, labelstr = query.split('{', 1)
    if labelstr[-1] != '}':
      raise BorgmonEvalLibError('invalid query syntax: %s' % query)
    labelstr = labelstr[:-1]

    components = re.split(r'\s*,\s*', labelstr)
    for c in components:
      (key, value) = c.split('=', 1)
      key = key.strip()
      labels[key] = value
  else:
    stem = query

  if for_tslookup:
    labels.update(ParseDotNotationForTSLookup(stem))
  else:
    labels.update(ParseDotNotationForBorgmon(stem))
  return labels


def ParseDotNotationForBorgmon(stem):
  """Parse dot-notation borgmon queries.

  Supports the following formats:
    var
    var.job
    var.shard.job
    var.shard.instance.job
    var.shard.job.service.zone
    var.shard.instance.job.service.zone

  Args:
    stem: stem of a borgmon query (containing no labelsets) to parse

  Returns:
    dict containing label value pairs.

  Raises:
    BorgmonEvalLibError: if syntax of stem was incorrect
  """
  labels = {}
  parts = stem.split('.')
  if not stem or not parts:
    return labels

  if len(parts) > 6:
    raise BorgmonEvalLibError('invalid query syntax: %s' % stem)

  if len(parts) == 6:
    # currently: var.shard.instance.job.service.zone
    labels['instance'] = parts[2]
    del parts[2]
    # now: var.shard.job.service.zone

  if len(parts) == 5:
    # currently: var.shard.job.service.zone
    labels['zone'] = parts[4]
    del parts[4]
    labels['service'] = parts[3]
    del parts[3]
    # now: var.shard.job

  if len(parts) == 4:
    # currently: var.shard.instance.job
    labels['instance'] = parts[2]
    del parts[2]
    # now: var.shard.job

  if len(parts) == 3:
    # currently: var.shard.job
    labels['shard'] = parts[1]
    del parts[1]
    # now: var.job

  if len(parts) == 2:
    # currently: var.job
    labels['job'] = parts[1]
    del parts[1]
    # now: var

  if len(parts) == 1:
    labels['var'] = parts[0]

  # Remove any unspecified labels.
  for k,v in labels.items():
    if not v:
      del labels[k]

  return labels


def ParseDotNotationForTSLookup(stem):
  """Parse dot-notation tslookup queries.

  Supports the following formats:
    var
    var.job
    var.service.zone
    var.job.service.zone
    var.shard.job.service.zone
    var.shard.instance.job.service.zone

  Args:
    stem: stem of a borgmon query (containing no labelsets) to parse

  Returns:
    dict containing label value pairs.

  Raises:
    BorgmonEvalLibError: if syntax of stem was incorrect
  """
  labels = {}
  parts = stem.split('.')
  if not stem or not parts:
    return labels

  if len(parts) > 6:
    raise BorgmonEvalLibError('invalid query syntax: %s' % stem)

  if len(parts) == 6:
    # currently: var.shard.instance.job.service.zone
    labels['instance'] = parts[2]
    del parts[2]
    # now: var.shard.job.service.zone

  if len(parts) == 5:
    # currently: var.shard.job.service.zone
    labels['shard'] = parts[1]
    del parts[1]
    # now: var.job.service.zone

  if len(parts) == 4:
    # currently: var.job.service.zone
    labels['job'] = parts[1]
    del parts[1]
    # now: var.service.zone

  if len(parts) == 3:
    # currently: var.service.zone
    labels['zone'] = parts[2]
    del parts[2]
    labels['service'] = parts[1]
    del parts[1]
    # now: var

  if len(parts) == 2:
    # currently: var.job
    labels['job'] = parts[1]
    del parts[1]
    # now: var

  if len(parts) == 1:
    labels['var'] = parts[0]

  # Remove any unspecified labels.
  for k, v in labels.items():
    if not v:
      del labels[k]

  return labels
