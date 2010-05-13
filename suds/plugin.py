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
The plugin module provides classes for implementation
of suds plugins.
"""

from suds import *
from logging import getLogger

log = getLogger(__name__)


class Context(object):
    """
    Plugin context.
    """
    pass


class InitContext(Context):
    """
    Init Context.
    @ivar wsdl: The wsdl.
    @type wsdl: L{wsdl.Definitions}
    """
    pass


class LoadContext(Context):
    """
    The XSD load context.
    @ivar root: The loaded xsd document root.
    @type root: L{sax.Element}
    """
    pass
        
        
class SendContext(Context):
    """
    The context for sending the soap envelope.
    @ivar envelope: The soap envelope I{root} element to be sent.
    @type envelope: L{sax.Element}
    """
    pass
        
        
class ReplyContext(Context):
    """
    The context for the text received as a reply
    to method invocation.
    @ivar reply: The received text.
    @type reply: unicode
    """
    pass
    


class Plugin:
    """
    The base class for suds plugins.
    All plugins should implement this interface.
    """
    
    def initialized(self, context):
        """
        Suds initialization.
        Called after wsdl the has been loaded.  Provides the plugin
        with the opportunity to inspect/modify the WSDL.
        @param context: The init context.
        @type context: L{InitContext}
        """
        pass
    
    def loaded(self, context):
        """
        Suds has loaded an XSD document.  Provides the plugin
        with an opportunity to inspect/modify the loaded XSD.
        Called after each XSD document is loaded.
        @param context: The XSD load context.
        @type context: L{LoadContext}
        """
        pass
    
    def sending(self, context):
        """
        Suds will send the specified soap envelope.
        Provides the plugin with the opportunity to inspect/modify
        the message before it is sent.
        @param context: The send context.
        @type context: L{SendContext}
        """
        pass
    
    def received(self, context):
        """
        Suds has received the specified reply.
        Provides the plugin with the opportunity to inspect/modify
        the received XML.
        @param context: The reply context.
        @type context: L{ReplyContext}
        """
        pass
   
    
class PluginContainer:
    """
    Plugin container provides easy method invocation.
    @ivar plugins: A list of plugin objects.
    @type plugins: [L{Plugin},]
    @cvar ctxclass: A dict of plugin method / context classes.
    @type ctxclass: dict
    """
    
    ctxclass = {\
        'initialized':InitContext,
        'loaded':LoadContext,
        'sending':SendContext,
        'received':ReplyContext,
    }
    
    def __init__(self, plugins):
        """
        @param plugins: A list of plugin objects.
        @type plugins: [L{Plugin},]
        """
        self.plugins = plugins
    
    def __getattr__(self, name):
        ctx = self.ctxclass.get(name)
        if ctx:
            return Method(name, ctx, self.plugins)
        else:
            raise AttributeError(name)


class Method:
    """
    Plugin method.
    @ivar name: The method name.
    @type name: str
    @ivar ctx: A context.
    @type ctx: L{Context}
    @ivar plugins: A list of plugins (targets).
    @type plugins: list
    """

    def __init__(self, name, ctx, plugins):
        """
        @param name: The method name.
        @type name: str
        @param ctx: A context.
        @type ctx: L{Context}
        @param plugins: A list of plugins (targets).
        @type plugins: list
        """
        self.name = name
        self.ctx = ctx()
        self.plugins = plugins
            
    def __call__(self, **kwargs):
        self.ctx.__dict__.update(kwargs)
        for plugin in self.plugins:
            try:
                method = getattr(plugin, self.name, None)
                if method:
                    method(self.ctx)
            except Exception, pe:
                log.exception(pe)
        return self.ctx
