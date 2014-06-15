# -*- coding: utf-8 -*-

# This program is free software; you can redistribute it and/or modify it under
# the terms of the (LGPL) GNU Lesser General Public License as published by the
# Free Software Foundation; either version 3 of the License, or (at your
# option) any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU Library Lesser General Public License
# for more details at ( http://www.gnu.org/licenses/lgpl.html ).
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
# written by: Jurko Gospodnetić ( jurko.gospodnetic@pke.hr )

"""
Suds Python library plugin unit tests.

Implemented using the 'pytest' testing framework.

"""

import testutils
if __name__ == "__main__":
    testutils.run_using_pytest(globals())

import pytest

from suds.plugin import (DocumentContext, DocumentPlugin, InitContext,
    InitPlugin, MessageContext, MessagePlugin, Plugin, PluginContainer,
    PluginDomain)


class MyDocumentPlugin(DocumentPlugin):
    """Local 'document' plugin class used in the tests in this module."""
    pass


class MyInitPlugin(InitPlugin):
    """Local 'init' plugin class used in the tests in this module."""
    pass


class MyMessagePlugin(MessagePlugin):
    """Local 'message' plugin class used in the tests in this module."""
    pass


@pytest.mark.parametrize("domain, expected_context", (
    ("document", DocumentContext),
    ("init", InitContext),
    ("message", MessageContext)))
def test_collecting_plugins_and_context_per_empty_domain(domain,
        expected_context):
    container = PluginContainer([])
    result = getattr(container, domain)
    assert result.__class__ is PluginDomain
    assert result.ctx is expected_context
    assert result.plugins == []


@pytest.mark.parametrize("domain, plugin_class", (
    ("document", DocumentPlugin),
    ("init", InitPlugin),
    ("message", MessagePlugin)))
def test_collecting_plugins_per_domain(domain, plugin_class):
    plugins = [
        MyDocumentPlugin(),
        MyDocumentPlugin(),
        MyMessagePlugin(),
        MyDocumentPlugin(),
        MyInitPlugin(),
        MyInitPlugin(),
        MyMessagePlugin(),
        InitPlugin(),
        MyMessagePlugin(),
        MyMessagePlugin(),
        None,
        MessagePlugin(),
        DocumentPlugin(),
        MyMessagePlugin(),
        MyDocumentPlugin(),
        InitPlugin(),
        InitPlugin(),
        MyInitPlugin(),
        MyInitPlugin(),
        None,
        MyDocumentPlugin(),
        DocumentPlugin(),
        MessagePlugin(),
        DocumentPlugin(),
        MessagePlugin(),
        DocumentPlugin(),
        InitPlugin(),
        MessagePlugin(),
        object(),
        DocumentPlugin(),
        MessagePlugin(),
        object(),
        InitPlugin(),
        Plugin(),
        Plugin(),
        MyInitPlugin()]
    container = PluginContainer(plugins)
    expected_plugins = [p for p in plugins if isinstance(p, plugin_class)]
    result = getattr(container, domain).plugins
    assert result == expected_plugins


def test_exception_passing():
    class FailingPluginException(Exception):
        pass

    class FailingPlugin(MessagePlugin):
        def marshalled(self, context):
            raise FailingPluginException

    container = PluginContainer([FailingPlugin()])
    pytest.raises(FailingPluginException, container.message.marshalled)


def test_invalid_plugin_domain():
    container = PluginContainer([])
    domain = "invalid_domain_name"
    e = pytest.raises(Exception, getattr, container, domain)
    try:
        e = e.value
        assert e.__class__ is Exception
        assert str(e) == "plugin domain (%s), invalid" % (domain,)
    finally:
        del e  # explicitly break circular reference chain in Python 3
