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
Indirect parametrization pytest plugin.

Allows tests parametrization data to be generated using a function instead of
having to be explicitly specified as is the case when using the builtin
pytest.mark.parametrize functionality.

Interface is similar to the builtin pytest.mark.parametrize implementation,
except that it takes an indirect parametrization function as an additional
initial positional argument. All the other arguments parameters are forwarded
onto this indirect parametrization function which then calculates and returns
the actual parametrization data. The return values are a standard Python
positional argument list and keyword argument dictionary to be used for the
underlying metafunc.parametrize() call.

May be used as either:
  1. pytest.indirect_parametrizer() or
  2. pytest.mark.indirect_parametrizer().

The two usages are equivalent except that the first one may be used with any
indirect parametrization function while the second one can not be used with
indirect parametrization functions taking no input parameters (with pytest
versions prior to 2.5.2 it also can not be used with functions taking only
keyword arguments). This is a technical restriction based on an underlying
pytest.mark implementation detail. See the indirect_parametrize() function
doc-string for more detailed information.

Usage example making the following test_example() test function calls after
calculating them from a much shorter definition:
 * test_example("Fritula", 1)
 * test_example("Fritula", 2)
 * test_example("Fritula", 3)
 * test_example("Fritula", 4)
 * test_example("Fritula", 5)
 * test_example("Fritula", 6)
 * test_example("Fritula", 7)
 * test_example("Fritula", 8)
 * test_example("Fritula", 9)
 * test_example("Madagascar", 10)
 * test_example("Madagascar", 20)
 * test_example("Madagascar", 30)
 * test_example("Rumpelstilskin", 20)
 * test_example("Rumpelstilskin", 40)

def custom_parametrization(param_names, param_value_defs):
    param_values = []
    for uno, due_values in param_value_defs:
        for due in due_values:
            param_values.append((uno, due))
    return (param_names, param_values), {}

@pytest.indirect_parametrize(custom_parametrization, ("uno", "due"), (
    ("Fritula", (1, 2, 3, 4, 5, 6, 7, 8, 9)),
    ("Madagascar", (10, 30, 50)),
    ("Rumpelstilskin", (20, 40))))
def test_example(uno, due):
    assert False

"""

import pytest


def indirect_parametrize(func, *args, **kwargs):
    """
    Decorator registering a custom parametrization function for a pytest test.

    This pytest.mark.indirect_parametrize() replacement allows the use of
    indirect parametrization functions taking no input parameters or, with
    pytest versions prior to 2.5.2, functions taking only keyword arguments.

    If a pytest.mark.indirect_parametrize() call is made with such an indirect
    parametrization function, it decorates the given function instead of
    storing and using it to decorate the intended function later on.

    """
    # In pytest versions prior to 2.5.2 pytest.mark.indirect_parametrize()
    # special handling occurs even when passing it additional keyword arguments
    # so we have to make sure we are passing it at least one additional
    # positional argument.
    def wrapper(func, *args, **kwargs):
        return func(*args, **kwargs)
    return pytest.mark.indirect_parametrize(wrapper, func, *args, **kwargs)


def pytest_configure(config):
    """Describe the new pytest marker in the --markers output."""
    config.addinivalue_line("markers",
        "indirect_parametrize(function, argnames, argvalues): similar to the "
        "builtin pytest.mark.parametrize implementation, except that it takes "
        "an indirect parametrization function as an additional initial "
        "positional argument. All the other parameters are forwarded to the "
        "indirect parametrization function which then returns the actual "
        "metafunc.parametrize() parameters (standard Python positional "
        "argument list and keyword argument dictionary) based on the received "
        "input data. For more detailed information see the "
        "indirect_parametrize pytest plugin implementation module.")


def pytest_generate_tests(metafunc):
    """pytest hook called for all detected test functions."""
    func = metafunc.function
    try:
        mark = func.indirect_parametrize
    except AttributeError:
        return
    args, kwargs = mark.args[0](*mark.args[1:], **mark.kwargs)
    metafunc.parametrize(*args, **kwargs)


def pytest_namespace():
    """pytest hook publishing references in the toplevel pytest namespace."""
    return {'indirect_parametrize': indirect_parametrize}
