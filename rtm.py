import appuifw
app_path=appuifw.app.full_name()[0]+u':\\data\\python\\'
data_path=app_path

import sys
sys.path.append(app_path+u'lib')

import pyrtm
import db
import options
import e32

# App configuration
apiKey = 'e8f0dd71d905f815af42b4752de411b5' 
secret = 'd64c0294efd97ddd'

#token='c620b829b667a3e8c828dd28bb7cc132017029fc'


if not db.init(app_path + u"rtm.db"):
  options.init()
  #TODO more db initialization

rtm = pyrtm.RTM(apiKey, secret)

rtm.token = options.get_option('token')

if not rtm.token:
  frob = options.get_option('frob')
  if frob:
    rtm.frob = frob
    try:
      rtm.getToken()
      options.set_option('token',rtm.token)
    except RTMAPIError:   
      frob = rtm.getNewFrob()
  else:
    frob = rtm.getNewFrob()

  if not token: # we did not get token by frob
    options.set_option('frob',frob)
    if appuifw.query(u"I'll now open the browser so you can give me access at RTM.",'query'):
      e32.start_exe('BrowserNG.exe', ' "4 %s"' % rtm.getAuthURL(), 0)
    exit()

appuifw.note(u"Hi, %s" % rtm.checkToken().fullname)
exit()


# now we have an authorized session to RTM and can do whatever we want.
#
# at first it's logical to run a sync
# the first sync should download everything
#
# what needs a connection to RTM?
# * Smart Add
# * adding contacts 
# 
#
# probably we'd like to create a timeline
