# This program is free software; you can redistribute it and/or modify
# it under the terms of the (LGPL) GNU Lesser General Public License as
# published by the Free Software Foundation; either version 3 of the 
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Library Lesser General Public License for more details at
# ( http://www.gnu.org/licenses/lgpl.html ).
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
# written by: Jeff Ortel ( jortel@redhat.com )

"""
Contains NTLM transport implementation for windows authenticated HTTP.
"""

import urllib2 as u2
from suds.transport import *
from suds.transport.https import HttpAuthenticated
from logging import getLogger

log = getLogger(__name__)


class WindowsHttpAuthenticated(HttpAuthenticated):
    """
    Provides Windows (NTLM) http authentication.
    @ivar pm: The password manager.
    @ivar handler: The authentication handler.
    @author: Christopher Bess
    """
    
    def __init__(self, **kwargs):
        # try to import ntlm support
        try:
            from ntlm import HTTPNtlmAuthHandler
        except ImportError:
            raise Exception("Cannot import python-ntlm module")    
        HttpTransport.__init__(self, **kwargs)
        self.pm = u2.HTTPPasswordMgrWithDefaultRealm()
        self.handler = u2.HTTPNtlmAuthHandler.HTTPNtlmAuthHandler(self.pm)
        self.urlopener = u2.build_opener(self.handler)
