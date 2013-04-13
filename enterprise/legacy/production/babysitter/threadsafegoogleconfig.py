#!/usr/bin/python2.4
#
# Copyright 2002 onwards Google Inc
#
# Implements ThreadsafeConfig class that overrides the lock / release
# functions from googleconfig.Config. Use this only if you enjoy threading
# module which some people say is bad because of some personal experience
# from ancient times. (We don't agree with them :) but be advised)
#
import threading
from google3.enterprise.legacy.production.babysitter import googleconfig

class ThreadsafeConfig(googleconfig.Config):

  #
  # We override this to provide make the locks be actual implemented locks
  #
  # Here init all the locks your way. There are four locks thar are used
  # -- lock for params_ (*reentrant*)
  # -- lock for to_distribute_
  # -- lock for invalid_params_
  # -- lock for config_manager_id_
  #
  def init_locks(self):
    self.params_lock_         = threading.RLock() # locks params_
    self.distr_lock_          = threading.Lock()  # locks to_distribute_
    self.invalid_params_lock_ = threading.Lock()  # locks invalid_params_
    self.config_manager_lock_ = threading.Lock()  # locks config_manager_id_
