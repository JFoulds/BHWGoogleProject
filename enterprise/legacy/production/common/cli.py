#!/usr/bin/python2.4
# Author: Oscar Stiffelman, oscar@google.com
# Copyright (C) 2002, Google Inc.


"""
This module abtracts the concept of a command line to enable
structured command line argument construction and validation.
Although it does not yet perform any validation or sophisticated
processing, it is believed that using this class to construct long
command lines is safer than performing unstructured string
concatenation.  In addition, it introduces a substantial amount of
consistency in the command line construction which makes code written
by many developers easier to understand.

The general use case is as follows:

cl = cli.CommandLine()
cl.add("binaryName")
cl.add("--foo1=bar1")
cl.add("--foo2")
cl.add("-foo3")

cl.toString()  # this generates binaryName --foo1=bar1 --foo2 -foo3



Note that parameter/value delimiters (-,--,=, etc) are not processed
by this class.  The client can use them for any application-specific
meaning.  This design decision was made to enable greater transparency
to the user and to the reader of the code .

As more intelligence is added to this class, it is likely that the
interface will also become more structured to accept object
representations of the parameter tuples, rather than opaque strings.
The primary long-term objective is to minimize the unstructured string
manipulation that has to be performed in client code.

"""



import string


class CommandLine:

  # Empty constructor that initializes
  # the storage for the individual command line arguments
  def __init__(self):
    self.args=[]

  # Joins the arguments that have already been
  # provided through the "Add" method.
  # It addes whitespace between the arguments
  # So {"binName", "--foo=bar", "--baz"} becomes
  # "binName --foo=bar --baz"
  def arg_join(self, *args):
    return string.join(map(lambda x: "%s" % x, args))

  # Returns the internal array of arguments
  def Args(self):
    return self.args

  # This adds a parameter to the command line.
  # The parameter can be any application-specific setting
  # and can contain any internal structure. For example
  # --foo=bar or -foo or bar
  # are all reasonal options.  The general idea is that this
  # should be a single, failure independent application setting
  #
  # Note that leading and trailing whitespace will be stripped from
  # the parameter.
  def Add(self, commandLineParameter):
    self.args.append(string.strip("%s" % commandLineParameter))


  # This builds the string representation
  # of the command line arguments.
  # Each parameter that was passed to the Add
  # method will be combined into a single string
  # with whitespacer separators.  The order
  # of the parameters in the combined string
  # will be the same as the order that they were passed to the
  # Add method.
  def ToString(self):
    return apply(self.arg_join, self.args)
