#!/usr/bin/python2.4
#
# Copyright 2008 Google Inc. All Rights Reserved.

"""Utility Classes to read and use the federation network configuration."""

__author__ = 'tvsriram@google.com (Sriram Viswanathan)'

import xml.dom
import xml.dom.minidom

from google3.pyglib import logging


class FederationConfigException(Exception):
  """Exception for error in configuration or an unexpected query."""
  
  def __init__(self, message):
    Exception.__init__(self)
    self.message = message
    

class CorpusRootConfig(object):
  """Corpus root configuration of any appliance."""
  
  def __init__(self, node):
    self.__id = node.getAttribute('id')
    self.__tunnel_ip = node.getAttribute('tunnel-ip')
    self.__tunnel_port = node.getAttribute('tunnel-port')
    self.__ppp_ip = node.getAttribute('ppp-ip')
    self.__secret = node.getAttribute('secret')
    logging.debug('%s' % self.GetConfigString())
    
  def GetId(self):
    """Return the appliance ID of the corpus root."""
    return self.__id
  
  def GetTunnelIp(self):
    """Return the ip address that the superroot need to connect to."""
    return self.__tunnel_ip
  
  def GetTunnelPort(self):
    """Get the port at which the Stunnel will be listening on."""
    return self.__tunnel_port
  
  def GetPppIp(self):
    """Get the ip that is to be used as the PPP ip address."""
    return self.__ppp_ip

  def GetSecret(self):
    """Get the secret that will be used for authenticating using PPP."""
    return self.__secret
  
  def GetConfigString(self):
    """Get the string that will summarize the corpus root configuration."""
    return ('ID - %s, tunnel-ip %s, tunnel-port %s, ppp-ip %s, secret %s' %
            (self.__id, self.__tunnel_ip, self.__tunnel_port, self.__ppp_ip,
             self.__secret))


class SuperRootConfig(object):
  """The superroot configuration of any appliance."""
  
  def __init__(self, node, tunnel_config):
    """Initialize the Superrootconfig with all the attributes of a Superroot.
    
    Args:
      node: The XML Node that has configuration information about the superroot.
      tunnel_config: The federation configuration for the tunnels.
      
    Raises:
      FederationConfigException: Invalid federation configuration. Missing Id.
    """
    self.__id = node.getAttribute('id')
    if self.__id is None:
      raise FederationConfigException('Missing Id')
    self.__user = node.getAttribute('user')
    self.__secret = node.getAttribute('secret')
    self.__ppp_ip = node.getAttribute('ppp-ip')
    self.__corpus_roots = []
    self.__tunnel_config = tunnel_config
    self._ParseCorpusRoots(node)
    logging.debug('ID - %s, User %s, secret %s, Corpus %s' %
                  (self.__id, self.__user, self.__secret,
                   str(self.__corpus_roots)))
  
  def _ParseCorpusRoots(self, node):
    """Parse the corpus root elements from XML.
    
    Args:
      node: The xml node which has information on the corpus root
    """
    for child in node.childNodes:
      if child.nodeType == xml.dom.Node.ELEMENT_NODE:
        appliance_id = child.getAttribute('id')
        corpus = self.__tunnel_config.GetCorpusRootConfig(appliance_id)
        if corpus is not None:
          self.__corpus_roots.append(corpus)
      
  def GetId(self):
    """Get the Appliance ID of the Superroot."""
    return self.__id
  
  def GetUserName(self):
    """Get the username that should be used as PPP user."""
    return self.__user
  
  def GetSecret(self):
    """Get the secret that should be used to authenticate."""
    return self.__secret
  
  def GetCorpusRoots(self):
    """Get the corpus root configurations.
    
    Returns:
      A list of CorpusRootConfig that is used by the Superroot.
    """
    return self.__corpus_roots
  
  def GetCorpusRoot(self, appliance_id):
    """Get the corpus root for the specified id.
    
    Args:
      appliance_id: The appliance id of the corpus root.
      
    Returns:
      The CorpusRootConfig object of the specified id, None if invalid.
    
    Raises:
      FederationConfigException: Invalid Corpus Root Id.
    """
    for corpus in self.__corpus_roots:
      logging.debug('Match id %s with corpus %s' %
                    (appliance_id, corpus.GetId()))
      if corpus.GetId() == appliance_id:
        return corpus
    raise FederationConfigException('Invalid Corpus Root Id')
  
  def GetPppIp(self):
    """Get the IP that need to be used as the ppp address in superroot."""
    return self.__ppp_ip
    

class FederationConfig(object):
  """Manage the federation configuration."""
  
  def __init__(self, xml_config=None, xml_buffer=None, sys_abstraction=None):
    """Initialize the federation configuration with contents of file.
    
    Args:
      xml_config: the file name that has the federation configuration.
      xml_buffer: the buffer that has the federation configuration.
      sys_abstraction: the object that provides all the required system methods.
    
    Raises:
      FederationConfigException: if the xml is invalid
    """
    self.__os = sys_abstraction
    if xml_config is not None:
      config_file = self.__os.OpenRead(xml_config)
      try:
        self.__doc = xml.dom.minidom.parse(config_file)
      except xml.parsers.expat.ExpatError, ex:
        raise FederationConfigException('Invalid xml')
      config_file.close()
    elif xml_buffer is not None:
      try:
        self.__doc = xml.dom.minidom.parseString(xml_buffer)
      except xml.parsers.expat.ExpatError, ex:
        raise FederationConfigException(str(ex))
    self.__doc.normalize()
    self.__corpus_roots = {}
    self.__super_roots = {}
    self._ParseConfigXml()
  
  def _ParseConfigXml(self):
    """Parse the federation configuration."""
    
    # Parse the corpus roots first, as superroots refer to them.
    corpus_root_elements = self.__doc.getElementsByTagName('corpus-root')
    for corpus_root_node in corpus_root_elements:
      corpus_root_config = CorpusRootConfig(corpus_root_node)
      self.__corpus_roots[corpus_root_config.GetId()] = corpus_root_config
      
    # Now parse the super roots and find the corresponding corpus roots
    super_root_elements = self.__doc.getElementsByTagName('super-root')
    for super_root_node in super_root_elements:
      super_root_config = SuperRootConfig(super_root_node, self)
      self.__super_roots[super_root_config.GetId()] = super_root_config
     
  def GetCorpusRootConfig(self, appliance_id):
    """Get the CorpusRootConfig object for the appliance.
    
    Args:
      appliance_id : The appliance, the corpus root configuration is required.
    
    Returns:
      the corpus root config object for the corresponding appliance.

    Raises:
      FederationConfigException: if the appliance id is invalid in config
    """
    corpus_root = self.__corpus_roots.get(appliance_id)
    if corpus_root is None:
      raise FederationConfigException('Invalid corpus root')
    return corpus_root
  
  def GetSuperRootConfig(self, appliance_id):
    """Get the SuperRootConfig object for the appliance.
    
    Args:
      appliance_id : The appliance, the super root configuration is required
    
    Returns:
      the SuperRootConfig object for the corresponding appliance

    Raises:
      FederationConfigException: if the appliance id is invalid in config
    """
    super_root = self.__super_roots.get(appliance_id)
    if super_root is None:
      raise FederationConfigException('Invalid superroot')
    return super_root

  def GetPapSecrets(self, appliance_id):
    """Get the pap secrets file that is used for authenticating the client.
    
    Args:
      appliance_id: The appliance id of the corpus root.
    
    Returns:
      A string with all the required records that can be appended to file.
    """
    corpus_root_config = self.__corpus_roots.get(appliance_id)
    super_roots_list = []
    pap_secrets = '\n'  # we will be appending to the file
    
    # Get all the super roots using the corpus root
    if corpus_root_config is not None:
      for super_root in self.__super_roots.itervalues():
        corpus_root_list = super_root.GetCorpusRoots()
        for corpus_root in corpus_root_list:
          if corpus_root.GetId() == corpus_root_config.GetId():
            super_roots_list.append(super_root)
            break
    for super_root in super_roots_list:
      pap_secrets_line = '%s %s %s %s\n' % (super_root.GetId(), '*',
                                            super_root.GetSecret(),
                                            super_root.GetPppIp())
      pap_secrets = '%s%s' % (pap_secrets, pap_secrets_line)
    return pap_secrets

  def GetChapSecrets(self, appliance_id, secrets_dict):
    """Get the pap secrets file that is used for authenticating the client.
    
    Args:
      appliance_id: The appliance id of the corpus root.
      secrets_dict: The existing secrets of chap-secrets file.
    
    Returns:
      A string with all the required records that can be appended to file.
      
    Raises:
      FederationConfigException: if the appliance id is invalid in config.
    """
    corpus_root_config = self.__corpus_roots.get(appliance_id)
    if corpus_root_config is None:
      raise FederationConfigException('Invalid Corpus Root Id')
    super_roots_list = []
    chap_secrets = '\n'
    
    # Get all the super roots using the corpus root
    if corpus_root_config is not None:
      for super_root in self.__super_roots.itervalues():
        corpus_root_list = super_root.GetCorpusRoots()
        for corpus_root in corpus_root_list:
          if corpus_root.GetId() == corpus_root_config.GetId():
            super_roots_list.append(super_root)
            break
          
    # Add the secret of the corpus root first for mutual authentication
    chap_secrets_line = '%s %s %s %s\n' % (corpus_root_config.GetId(), '*',
                                           corpus_root_config.GetSecret(),
                                           corpus_root_config.GetPppIp())
    if corpus_root_config.GetId() in secrets_dict:
      secrets_dict.pop(corpus_root_config.GetId())
    secrets_dict[corpus_root_config.GetId()] = chap_secrets_line
    
    # Now add the super root secrets into the file
    for super_root in super_roots_list:
      chap_secrets_line = '%s %s %s %s\n' % (super_root.GetId(), '*',
                                             super_root.GetSecret(),
                                             super_root.GetPppIp())
      if super_root.GetId() in secrets_dict:
        secrets_dict.pop(super_root.GetId())
      secrets_dict[super_root.GetId()] = chap_secrets_line
      
    # Iterate through all the values in the dict
    for line in secrets_dict.itervalues():
      chap_secrets = '%s%s' % (chap_secrets, line)
    return chap_secrets
  
  def GetChapSecretsInFile(self, appliance_id, file_name,
                           chap_secrets_dict=None):
    """Write down the CHAP configutation in a file.
    
    Args:
      appliance_id: The unique appliance ID.
      file_name: The name of the chap secret file, to be used by pppd.
      chap_secrets_dict: Dictionary of all appliances and secrets.
      
    Returns:
      (0, 'Success') on successful creation and (-1, 'Failed') on failure.

    Raises:
      FederationConfigException if the appliance id is invalid in config.
    """
    if chap_secrets_dict is None:
      chap_secrets_dict = {}
      if self.__os.ExistsPath(file_name):
        read_object = self.__os.OpenRead(file_name)
        if read_object:
          read_lines = read_object.readlines()
          for line in read_lines:
            fields = line.split()
            if fields is not None and len(fields):
              chap_secrets_dict[fields[0]] = line
          read_object.close()

    # now add the additional information
    chap_secrets = self.GetChapSecrets(appliance_id, chap_secrets_dict)
    write_object = self.__os.OpenWrite(file_name)
    if write_object:
      write_object.write(chap_secrets)
      write_object.close()
      return (0, 'success')
    return (-1, 'Failed')

