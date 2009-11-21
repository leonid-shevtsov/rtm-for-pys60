# Python library for Remember The Milk API
#
# Ported to PyS60 by Leonid Shevtsov
#
# Notable changes:
# * simplejson is required

__author__ = 'Sridhar Ratnakumar <http://nearfar.org/>'
__all__ = (
  'API',
  'createRTM',
  'set_log_level',
    )


import new
import warnings
import urllib
import logging
from md5 import md5

warnings.simplefilter('default', ImportWarning)

import simplejson
simplejson_instance = simplejson.simplejson()

logging.basicConfig()
LOG = logging.getLogger(__name__)
LOG.setLevel(logging.INFO)

SERVICE_URL = 'http://api.rememberthemilk.com/services/rest/'
AUTH_SERVICE_URL = 'http://www.rememberthemilk.com/services/auth/'

class RTMError(Exception): pass

class RTMAPIError(RTMError): pass

class RTM(object):

  def __init__(self, apiKey, secret, token=None):
    self.apiKey = apiKey
    self.secret = secret
    self.token = token

    # this enables one to do 'rtm.tasks.getList()', for example
    for prefix, methods in API.items():
      setattr(self, prefix,
          RTMAPICategory(self, prefix, methods))

  def _sign(self, params):
    "Sign the parameters with MD5 hash"
    pairs = ''.join(['%s%s' % (k,v) for k,v in sortedItems(params)])
    return md5(self.secret+pairs).hexdigest()

  def get(self, **params):
    "Get the XML response for the passed `params`."
    params['api_key'] = self.apiKey
    params['format'] = 'json'
    params['api_sig'] = self._sign(params)

    json = openURL(SERVICE_URL, params).read()

    LOG.debug("JSON response: \n%s" % json)

    data = dottedDict('ROOT', simplejson_instance.loads(json))
    
    rsp = data.rsp

    if rsp.stat == 'fail':
      raise RTMAPIError, 'API call failed - %s (%s)' % (rsp.err.msg, rsp.err.code)
    else:
      return rsp

  def getNewFrob(self):
    rsp = self.get(method='rtm.auth.getFrob')
    self.frob = rsp.frob
    return self.frob

  def getAuthURL(self):
    if not self.frob:
      frob = self.getNewFrob()

    params = {
      'api_key': self.apiKey,
      'perms'  : 'delete',
      'frob'   : self.frob
      }
    params['api_sig'] = self._sign(params)
    return AUTH_SERVICE_URL + '?' + urllib.urlencode(params)

  def getToken(self):
    rsp = self.get(method='rtm.auth.getToken', frob=self.frob)
    self.token = rsp.auth.token
    return self.token

  def checkToken(self):
    rsp = self.get(method='rtm.auth.checkToken', auth_token=self.token)
    return rsp.auth.user

class RTMAPICategory:
  "See the `API` structure and `RTM.__init__`"

  def __init__(self, rtm, prefix, methods):
    self.rtm = rtm
    self.prefix = prefix
    self.methods = methods

  def __getattr__(self, attr):
    if attr in self.methods:
      rargs, oargs = self.methods[attr]
      if self.prefix == 'tasksNotes':
        aname = 'rtm.tasks.notes.%s' % attr
      else:
        aname = 'rtm.%s.%s' % (self.prefix, attr)
      return lambda **params: self.callMethod(
        aname, rargs, oargs, **params)
    else:
      raise AttributeError, 'No such attribute: %s' % attr

  def callMethod(self, aname, rargs, oargs, **params):
    # Sanity checks
    for requiredArg in rargs:
      if requiredArg not in params:
        raise TypeError, 'Required parameter (%s) missing' % requiredArg

    for param in params:
      if param not in rargs + oargs:
        warnings.warn('Invalid parameter (%s)' % param)

    return self.rtm.get(method=aname,
              auth_token=self.rtm.token,
              **params)


# Utility functions

def sortedItems(dictionary):
  "Return a list of (key, value) sorted based on keys"
  keys = dictionary.keys()
  keys.sort()
  for key in keys:
    yield key, dictionary[key]

def openURL(url, queryArgs=None):
  if queryArgs:
    url = url + '?' + urllib.urlencode(queryArgs)
  print url
  LOG.debug("URL> %s", url)
  return urllib.urlopen(url)

class dottedDict(object):
  "Make dictionary items accessible via the object-dot notation."

  def __init__(self, name, dictionary):
    self._name = name

    if type(dictionary) is dict:
      for key, value in dictionary.items():
        if type(value) is dict:
          value = dottedDict(key, value)
        elif type(value) in (list, tuple) and key != 'tag':
          value = [dottedDict('%s_%d' % (key, i), item)
               for i, item in indexed(value)]
        setattr(self, key, value)

  def __repr__(self):
    children = [c for c in dir(self) if not c.startswith('_')]
    return 'dotted <%s> : %s' % (
      self._name,
      ', '.join(children))


def safeEval(string):
  return eval(string, {}, {})

def dottedJSON(json):
  return dottedDict('ROOT', safeEval(json))

def indexed(seq):
  index = 0
  for item in seq:
    yield index, item
    index += 1


# API spec

API = {
   'auth': {
     'checkToken':
       [('auth_token'), ()],
     'getFrob':
       [(), ()],
     'getToken':
       [('frob'), ()]
     },
  'contacts': {
    'add':
      [('timeline', 'contact'), ()],
    'delete':
      [('timeline', 'contact_id'), ()],
    'getList':
      [(), ()]
    },
  'groups': {
    'add':
      [('timeline', 'group'), ()],
    'addContact':
      [('timeline', 'group_id', 'contact_id'), ()],
    'delete':
      [('timeline', 'group_id'), ()],
    'getList':
      [(), ()],
    'removeContact':
      [('timeline', 'group_id', 'contact_id'), ()],
    },
  'lists': {
    'add':
      [('timeline', 'name'), ('filter'), ()],
    'archive':
      [('timeline', 'list_id'), ()],
    'delete':
      [('timeline', 'list_id'), ()],
    'getList':
      [(), ()],
    'setDefaultList':
      [('timeline'), ('list_id'), ()],
    'setName':
      [('timeline', 'list_id', 'name'), ()],
    'unarchive':
      [('timeline'), ('list_id'), ()],
    },
  'locations': {
    'getList':
      [(), ()]
    },
  'reflection': {
    'getMethodInfo':
      [('methodName',), ()],
    'getMethods':
      [(), ()]
    },
  'settings': {
    'getList':
      [(), ()]
    },
  'tasks': {
    'add':
      [('timeline', 'name',), ('list_id', 'parse',)],
    'addTags':
      [('timeline', 'list_id', 'taskseries_id', 'task_id', 'tags'),
       ()],
    'complete':
      [('timeline', 'list_id', 'taskseries_id', 'task_id',), ()],
    'delete':
      [('timeline', 'list_id', 'taskseries_id', 'task_id'), ()],
    'getList':
      [(),
       ('list_id', 'filter', 'last_sync')],
    'movePriority':
      [('timeline', 'list_id', 'taskseries_id', 'task_id', 'direction'),
       ()],
    'moveTo':
      [('timeline', 'from_list_id', 'to_list_id', 'taskseries_id', 'task_id'),
       ()],
    'postpone':
      [('timeline', 'list_id', 'taskseries_id', 'task_id'),
       ()],
    'removeTags':
      [('timeline', 'list_id', 'taskseries_id', 'task_id', 'tags'),
       ()],
    'setDueDate':
      [('timeline', 'list_id', 'taskseries_id', 'task_id'),
       ('due', 'has_due_time', 'parse')],
    'setEstimate':
      [('timeline', 'list_id', 'taskseries_id', 'task_id'),
       ('estimate',)],
    'setLocation':
      [('timeline', 'list_id', 'taskseries_id', 'task_id'),
       ('location_id',)],
    'setName':
      [('timeline', 'list_id', 'taskseries_id', 'task_id', 'name'),
       ()],
    'setPriority':
      [('timeline', 'list_id', 'taskseries_id', 'task_id'),
       ('priority',)],
    'setRecurrence':
      [('timeline', 'list_id', 'taskseries_id', 'task_id'),
       ('repeat',)],
    'setTags':
      [('timeline', 'list_id', 'taskseries_id', 'task_id'),
       ('tags',)],
    'setURL':
      [('timeline', 'list_id', 'taskseries_id', 'task_id'),
       ('url',)],
    'uncomplete':
      [('timeline', 'list_id', 'taskseries_id', 'task_id'),
       ()],
    },
  'tasksNotes': {
    'add':
      [('timeline', 'list_id', 'taskseries_id', 'task_id', 'note_title', 'note_text'), ()],
    'delete':
      [('timeline', 'note_id'), ()],
    'edit':
      [('timeline', 'note_id', 'note_title', 'note_text'), ()]
    },
  'test': {
    'echo':
      [(), ()],
    'login':
      [(), ()]
    },
  'time': {
    'convert':
      [('to_timezone',), ('from_timezone', 'to_timezone', 'time')],
    'parse':
      [('text',), ('timezone', 'dateformat')]
    },
  'timelines': {
    'create':
      [(), ()]
    },
  'timezones': {
    'getList':
      [(), ()]
    },
  'transactions': {
    'undo':
      [('timeline', 'transaction_id'), ()]
    },
  }

def set_log_level(level):
  '''Sets the log level of the logger used by the module.
  
  >>> import rtm
  >>> import logging
  >>> rtm.set_log_level(logging.INFO)
  '''
  
  LOG.setLevel(level)
