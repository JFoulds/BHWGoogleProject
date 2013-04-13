#!/usr/bin/python2.4
#
# Very simple script that writes out in which install state we are
import sys
from google3.enterprise.legacy.install import install_utilities

if __name__ == '__main__':
  print install_utilities.install_state(sys.argv[1])
