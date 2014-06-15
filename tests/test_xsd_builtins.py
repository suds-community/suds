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
Suds library's built-in XSD type handling unit tests.

Implemented using the 'pytest' testing framework.

"""

import testutils
if __name__ == "__main__":
    testutils.run_using_pytest(globals())

import suds.client
import suds.sax.date
from suds.xsd.sxbuiltin import (Factory, XAny, XBoolean, XBuiltin, XDate,
    XDateTime, XDecimal, XFloat, XInteger, XLong, XString, XTime)
from testutils.compare_sax import CompareSAX

import pytest

import datetime
import decimal
import re
import sys

if sys.version_info >= (2, 6):
    import fractions
if sys.version_info >= (3,):
    long = int


class _Dummy:
    """Class for testing unknown object class handling."""
    pass


# Define mock MockXType classes (e.g. MockXDate, MockXInteger & MockXString)
# used to test translate() methods in different XSD data type model classes
# such as XDate, XInteger & XString.
def _def_mock_xsd_class(x_class_name):
    """
    Define a mock XType class and reference it globally as MockXType.

    XType classes (e.g. XDate, XInteger & XString), represent built-in XSD
    types. Their mock counterparts created here (e.g. MockXDate, MockXInteger &
    MockXString) may be used to test their translate() methods without having
    to connect them to an actual XSD schema.

    This is achieved by having their constructor call take no parameters and
    not call the parent class __init__() method.

    Rationale why these mock classes are used instead of actual XType classes:
      * XType instances need to be connected to an actual XSD schema element
        which would unnecessarily complicate our test code.
      * XType translate() implementations are not affected by whether the
        instance they have been called on has been connected to an actual XSD
        schema element.
      * XType translate() functions can not be called as unbound methods, e.g.
        XDate.translate(...). Such an implementation would fail if those
        methods are not defined exactly in the specified XType class but in one
        of its parent classes.

    """
    x_class = getattr(suds.xsd.sxbuiltin, x_class_name)
    assert issubclass(x_class, XBuiltin)
    mock_class_name = "Mock" + x_class_name
    mock_class = type(mock_class_name, (x_class,), {
        "__doc__": "Mock %s not connected to an XSD schema." % (x_class_name,),
        "__init__": lambda self: None})
    globals()[mock_class_name] = mock_class

for x in ("XAny", "XBoolean", "XDate", "XDateTime", "XDecimal", "XFloat",
        "XInteger", "XLong", "XString", "XTime"):
    _def_mock_xsd_class(x)


# Built-in XSD data types as defined in 'XML Schema Part 2: Datatypes Second
# Edition' (http://www.w3.org/TR/2004/REC-xmlschema-2-20041028). Each is paired
# with its respective suds library XSD type modeling class.
builtins = {
    "anySimpleType": XString,
    "anyType": XAny,
    "anyURI": XString,
    "base64Binary": XString,
    "boolean": XBoolean,
    "byte": XInteger,
    "date": XDate,
    "dateTime": XDateTime,
    "decimal": XDecimal,
    "double": XFloat,
    "duration": XString,
    "ENTITIES": XString,
    "ENTITY": XString,
    "float": XFloat,
    "gDay": XString,
    "gMonth": XString,
    "gMonthDay": XString,
    "gYear": XString,
    "gYearMonth": XString,
    "hexBinary": XString,
    "ID": XString,
    "IDREF": XString,
    "IDREFS": XString,
    "int": XInteger,
    "integer": XInteger,
    "language": XString,
    "long": XLong,
    "Name": XString,
    "NCName": XString,
    "negativeInteger": XInteger,
    "NMTOKEN": XString,
    "NMTOKENS": XString,
    "nonNegativeInteger": XInteger,
    "nonPositiveInteger": XInteger,
    "normalizedString": XString,
    "NOTATION": XString,
    "positiveInteger": XInteger,
    "QName": XString,
    "short": XInteger,
    "string": XString,
    "time": XTime,
    "token": XString,
    "unsignedByte": XInteger,
    "unsignedInt": XInteger,
    "unsignedLong": XLong,
    "unsignedShort": XInteger}

# XML namespaces where all the built-in type names live, as defined in 'XML
# Schema Part 2: Datatypes Second Edition'
# (http://www.w3.org/TR/2004/REC-xmlschema-2-20041028).
builtin_namespaces = [
    "http://www.w3.org/2001/XMLSchema",
    "http://www.w3.org/2001/XMLSchema-datatypes"]


class TestXBoolean:
    """suds.xsd.sxbuiltin.XBoolean.translate() tests."""

    @pytest.mark.parametrize(("source", "expected"), (
        (0, "false"),
        (1, "true"),
        (False, "false"),
        (True, "true")))
    def test_from_python_object(self, source, expected):
        translated = MockXBoolean().translate(source, topython=False)
        assert translated.__class__ is str
        assert translated == expected

    @pytest.mark.parametrize("source", (
        None,
        pytest.mark.skipif(sys.version_info >= (3,),
            reason="int == long since Python 3.0")(long(0)),
        pytest.mark.skipif(sys.version_info >= (3,),
            reason="int == long since Python 3.0")(long(1)),
        "x",
        "True",
        "False",
        object(),
        _Dummy(),
        datetime.date(2101, 1, 1)))
    def test_from_python_object__invalid(self, source):
        assert MockXBoolean().translate(source, topython=False) is source

    @pytest.mark.parametrize("source", (-1, 2, 5, 100))
    def test_from_python_object__invalid_integer(self, source):
        #TODO: See if this special integer handling is really desired.
        assert MockXBoolean().translate(source, topython=False) is None

    @pytest.mark.parametrize(("source", "expected"), (
        ("0", False),
        ("1", True),
        ("false", False),
        ("true", True)))
    def test_to_python_object(self, source, expected):
        assert MockXBoolean().translate(source) is expected

    @pytest.mark.parametrize("source",
        (0, 1, "", "True", "False", "2", "Z", "-1", "00", "x", "poppycock"))
    def test_to_python_object__invalid(self, source):
        assert MockXBoolean().translate(source) is None


class TestXDate:
    """
    suds.xsd.sxbuiltin.XDate.translate() tests.

    Related Python object <--> string conversion details are tested in a
    separate date/time related test module. These tests are only concerned with
    basic translate() functionality.

    """

    def test_from_python_object__date(self):
        date = datetime.date(2013, 7, 24)
        translated = MockXDate().translate(date, topython=False)
        assert translated.__class__ is suds.sax.date.Date
        assert str(translated) == "2013-07-24"

    def test_from_python_object__datetime(self):
        dt = datetime.datetime(2013, 7, 24, 11, 59, 4)
        translated = MockXDate().translate(dt, topython=False)
        assert translated.__class__ is suds.sax.date.Date
        assert str(translated) == "2013-07-24"

    @pytest.mark.parametrize("source", (
        None,
        object(),
        _Dummy(),
        datetime.time()))
    def test_from_python_object__invalid(self, source):
        assert MockXDate().translate(source, topython=False) is source

    def test_to_python_object(self):
        assert MockXDate().translate("1941-12-7") == datetime.date(1941, 12, 7)

    def test_to_python_object__empty_string(self):
        assert MockXDate().translate("") == None


class TestXDateTime:
    """
    suds.xsd.sxbuiltin.XDateTime.translate() tests.

    Related Python object <--> string conversion details are tested in a
    separate date/time related test module. These tests are only concerned with
    basic translate() functionality.

    """

    def test_from_python_object(self):
        dt = datetime.datetime(2021, 12, 31, 11, 25)
        translated = MockXDateTime().translate(dt, topython=False)
        assert translated.__class__ is suds.sax.date.DateTime
        assert str(translated) == "2021-12-31T11:25:00"

    @pytest.mark.parametrize("source", (
        None,
        object(),
        _Dummy(),
        datetime.time(22, 47, 9, 981),
        datetime.date(2101, 1, 1)))
    def test_from_python_object__invalid(self, source):
        assert MockXDateTime().translate(source, topython=False) is source

    def test_to_python_object(self):
        dt = datetime.datetime(1941, 12, 7, 10, 30, 22, 454000)
        assert MockXDateTime().translate("1941-12-7T10:30:22.454") == dt

    def test_to_python_object__empty_string(self):
        assert MockXDateTime().translate("") == None


class TestXDecimal:
    """suds.xsd.sxbuiltin.XDecimal.translate() tests."""

    @pytest.mark.parametrize(("source", "expected"), (
        # Zeros.
        (decimal.Decimal("0"), "0"),
        (decimal.Decimal("-0"), "-0"),
        # Positive integral.
        (decimal.Decimal("1"), "1"),
        (decimal.Decimal("1000"), "1000"),
        (decimal.Decimal("1E500"), "1" + "0" * 500),
        # Negative integral.
        (decimal.Decimal("-1"), "-1"),
        (decimal.Decimal("-1000"), "-1000"),
        (decimal.Decimal("-1E500"), "-1" + "0" * 500),
        # Simple fractional.
        (decimal.Decimal("0.1"), "0.1"),
        (decimal.Decimal("-0.1"), "-0.1"),
        (decimal.Decimal("0." + "0123456789" * 9), "0." + "0123456789" * 9),
        (decimal.Decimal("-0." + "0123456789" * 9), "-0." + "0123456789" * 9),
        # Zero with extra fractional digits.
        (decimal.Decimal("0.0000"), "0"),
        (decimal.Decimal("-0.0000"), "-0"),
        # Only 0s as fractional digits.
        (decimal.Decimal("5.000000000000000000"), "5"),
        (decimal.Decimal("-5.000000000000000000"), "-5"),
        # Trailing fractional 0 digits.
        (decimal.Decimal("5.000000123000000000000"), "5.000000123"),
        (decimal.Decimal("-5.000000123000000000000"), "-5.000000123"),
        # Very small fractional part.
        (decimal.Decimal("9E-100"), "0." + "0" * 99 + "9"),
        (decimal.Decimal("-9E-100"), "-0." + "0" * 99 + "9")))
    def test_decimal_to_xsd_value_representation(self, source, expected):
        assert source.__class__ is decimal.Decimal
        string = MockXDecimal()._decimal_to_xsd_format(source)
        assert string.__class__ is str
        assert string == expected

    @pytest.mark.parametrize("source", (
        decimal.Decimal(0),
        decimal.Decimal("0.1") + decimal.Decimal("0.2"),
        decimal.Decimal("5.781963")))
    def test_from_python_object(self, source):
        assert source.__class__ is decimal.Decimal, "bad test data"
        translated = MockXDecimal().translate(source, topython=False)
        expected = MockXDecimal()._decimal_to_xsd_format(source)
        assert translated.__class__ is str
        assert translated == expected

    extra_test_data = ()
    if sys.version_info >= (2, 6):
        extra_test_data = (
            # fraction.Fraction
            fractions.Fraction(10, 4),
            fractions.Fraction(1, 3))
    @pytest.mark.parametrize("source", (
        None,
        # bool
        True,
        False,
        # float
        -50.2,
        1.9623e-26,
        0.1 + 0.2,
        0.7,
        1.0,
        50.99999,
        # int
        0,
        1,
        -55566,
        # str
        "0.1",
        "0.2",
        "x",
        # other
        object(),
        _Dummy(),
        datetime.date(2101, 1, 1)) + extra_test_data)
    def test_from_python_object__no_translation(self, source):
        assert MockXDecimal().translate(source, topython=False) is source

    @pytest.mark.parametrize("source", (
        "-500.0",
        "0",
        "0.0",
        "0.00000000000000000000001",
        "000",
        "1.78123875",
        "-1.78123875",
        "1",
        "01",
        "100"))
    def test_to_python_object(self, source):
        translated = MockXDecimal().translate(source)
        assert translated.__class__ is decimal.Decimal
        assert translated == decimal.Decimal(source)

    @pytest.mark.parametrize("source",
        ("", 0, 1, 1.5, True, False, 500, _Dummy(), object()))
    def test_to_python_object__invalid_class_or_empty_string(self, source):
        assert MockXDecimal().translate(source) is None

    @pytest.mark.parametrize("src", (" ", "0,0", "0-0", "x", "poppycock"))
    def test_to_python_object__invalid_string(self, src):
        """
        Suds raises raw Python exceptions when it fails to convert received
        response element data to its mapped Python decimal.Decimal data type,
        according to the used WSDL schema.

        """
        pytest.raises(decimal.InvalidOperation, MockXDecimal().translate, src)


class TestXFloat:
    """suds.xsd.sxbuiltin.XFloat.translate() tests."""

    extra_test_data = ()
    if sys.version_info >= (2, 6):
        extra_test_data = (
            # fraction.Fraction
            fractions.Fraction(10, 4),
            fractions.Fraction(1, 3))
    @pytest.mark.parametrize("source", (
        None,
        # bool
        True,
        False,
        # decimal.Decimal
        decimal.Decimal(0),
        decimal.Decimal("0.1") + decimal.Decimal("0.2"),
        decimal.Decimal("5.781963"),
        # float
        -50.2,
        0.1 + 0.2,
        0.7,
        1.0,
        50.99999,
        # int
        0,
        1,
        -55566,
        # str
        "0.1",
        "0.2",
        "x",
        # other
        object(),
        _Dummy(),
        datetime.date(2101, 1, 1)) + extra_test_data)
    def test_from_python_object(self, source):
        assert MockXFloat().translate(source, topython=False) is source

    @pytest.mark.parametrize("source", (
        "-500.0",
        "0",
        "0.0",
        "0.00000000000000000000001",
        "000",
        "1.78123875",
        "-1.78123875",
        "1",
        "01",
        "100"))
    def test_to_python_object(self, source):
        translated = MockXFloat().translate(source)
        assert translated.__class__ is float
        assert translated == float(source)

    @pytest.mark.parametrize("source",
        ("", 0, 1, 1.5, True, False, 500, _Dummy(), object()))
    def test_to_python_object__invalid_class_or_empty_string(self, source):
        assert MockXFloat().translate(source) is None

    @pytest.mark.parametrize("source", (" ", "0,0", "0-0", "x", "poppycock"))
    def test_to_python_object__invalid_string(self, source, monkeypatch):
        """
        Suds raises raw Python exceptions when it fails to convert received
        response element data to its mapped Python float data type, according
        to the used WSDL schema.

        """
        monkeypatch.delitem(locals(), "e", False)
        e = pytest.raises(ValueError, MockXFloat().translate, source).value
        try:
            # Using different Python interpreter versions and different source
            # strings results in different exception messages here.
            try:
                float(source)
                pytest.fail("Bad test data.")
            except ValueError:
                assert str(e) == str(sys.exc_info()[1])
        finally:
            del e  # explicitly break circular reference chain in Python 3


class TestXInteger:
    """suds.xsd.sxbuiltin.XInteger.translate() tests."""

    @pytest.mark.parametrize("source", (
        None,
        # bool
        False,
        True,
        # int
        -50,
        0,
        1,
        50,
        # long
        long(-50),
        long(0),
        long(1),
        long(50),
        # str
        "x",
        # other
        object(),
        _Dummy(),
        datetime.date(2101, 1, 1)))
    def test_from_python_object(self, source):
        assert MockXInteger().translate(source, topython=False) is source

    @pytest.mark.parametrize("source", ("-500", "0", "000", "1", "01", "100"))
    def test_to_python_object(self, source):
        translated = MockXInteger().translate(source)
        assert translated.__class__ is int
        assert translated == int(source)

    @pytest.mark.parametrize("source",
        ("", 0, 1, True, False, 500, _Dummy(), object()))
    def test_to_python_object__invalid_class_or_empty_string(self, source):
        assert MockXInteger().translate(source) is None

    @pytest.mark.parametrize("source", (" ", "0-0", "x", "poppycock"))
    def test_to_python_object__invalid_string(self, source, monkeypatch):
        """
        Suds raises raw Python exceptions when it fails to convert received
        response element data to its mapped Python integer data type, according
        to the used WSDL schema.

        """
        monkeypatch.delitem(locals(), "e", False)
        e = pytest.raises(ValueError, MockXInteger().translate, source).value
        try:
            # Using different Python interpreter versions and different source
            # strings results in different exception messages here.
            try:
                int(source)
                pytest.fail("Bad test data.")
            except ValueError:
                assert str(e) == str(sys.exc_info()[1])
        finally:
            del e  # explicitly break circular reference chain in Python 3


class TestXLong:
    """suds.xsd.sxbuiltin.XLong.translate() tests."""

    @pytest.mark.parametrize("source", (
        None,
        # bool
        False,
        True,
        # int
        -50,
        0,
        1,
        50,
        # long
        long(-50),
        long(0),
        long(1),
        long(50),
        # str
        "x",
        # other
        object(),
        _Dummy(),
        datetime.date(2101, 1, 1)))
    def test_from_python_object(self, source):
        assert MockXLong().translate(source, topython=False) is source

    @pytest.mark.parametrize(("source", "expected"), (
        ("-500", -500),
        ("0", 0),
        ("000", 0),
        ("1", 1),
        ("01", 1),
        ("100", 100)))
    def test_to_python_object(self, source, expected):
        translated = MockXLong().translate(source)
        assert translated.__class__ is long
        assert translated == expected

    @pytest.mark.parametrize("source",
        ("", 0, 1, True, False, 500, _Dummy(), object()))
    def test_to_python_object__invalid_class_or_empty_string(self, source):
        assert MockXLong().translate(source) is None

    @pytest.mark.parametrize("source", (" ", "0-0", "x", "poppycock"))
    def test_to_python_object__invalid_string(self, source, monkeypatch):
        """
        Suds raises raw Python exceptions when it fails to convert received
        response element data to its mapped Python long data type, according to
        the used WSDL schema.

        """
        monkeypatch.delitem(locals(), "e", False)
        e = pytest.raises(ValueError, MockXLong().translate, source).value
        try:
            # Using different Python interpreter versions and different source
            # strings results in different exception messages here.
            try:
                long(source)
                pytest.fail("Bad test data.")
            except ValueError:
                assert str(e) == str(sys.exc_info()[1])
        finally:
            del e  # explicitly break circular reference chain in Python 3


class TestXTime:
    """
    suds.xsd.sxbuiltin.XTime.translate() tests.

    Related Python object <--> string conversion details are tested in a
    separate date/time related test module. These tests are only concerned with
    basic translate() functionality.

    """

    def test_from_python_object(self):
        time = datetime.time(16, 53, 12)
        translated = MockXTime().translate(time, topython=False)
        assert translated.__class__ is suds.sax.date.Time
        assert str(translated) == "16:53:12"

    @pytest.mark.parametrize("source", (
        None,
        object(),
        _Dummy(),
        datetime.date(2101, 1, 1),
        datetime.datetime(2101, 1, 1, 22, 47, 9, 981)))
    def test_from_python_object__invalid(self, source):
        assert MockXTime().translate(source, topython=False) is source

    def test_to_python_object(self):
        assert MockXTime().translate("10:30:22") == datetime.time(10, 30, 22)

    def test_to_python_object__empty_string(self):
        assert MockXTime().translate("") == None


@pytest.mark.parametrize(("xsd_type_name", "xsd_type"),
    sorted(builtins.items()) +  # See 'Project implementation note #1'.
    [("...unknown...", XBuiltin)])
def test_create_builtin_type_schema_objects(xsd_type_name, xsd_type):
    schema = _create_dummy_schema()
    xsd_object = Factory.create(schema, xsd_type_name)
    assert xsd_object.__class__ is xsd_type
    assert xsd_object.name == xsd_type_name
    assert xsd_object.schema is schema


@pytest.mark.parametrize("xsd_type_name", ("tonkica-polonkica", "integer"))
def test_create_custom_mapped_builtin_type_schema_objects(xsd_type_name,
        monkeypatch):
    """User code can add or update built-in XSD type registrations."""
    _monkeypatch_builtin_XSD_type_registry(monkeypatch)
    class MockType:
        def __init__(self, schema, name):
            self.schema = schema
            self.name = name
    schema = _Dummy()
    Factory.maptag(xsd_type_name, MockType)
    xsd_object = Factory.create(schema, xsd_type_name)
    assert xsd_object.__class__ is MockType
    assert xsd_object.name == xsd_type_name
    assert xsd_object.schema is schema


# See 'Project implementation note #1'.
@pytest.mark.parametrize("name", sorted(builtins.keys()))
@pytest.mark.parametrize("namespace", builtin_namespaces)
def test_recognize_builtin_types(name, namespace):
    schema = _create_dummy_schema()
    assert schema.builtin((name, namespace))


# See 'Project implementation note #1'.
@pytest.mark.parametrize("name", sorted(builtins.keys()))
@pytest.mark.parametrize("namespace", ("", " ", "some-dummy-namespace"))
def test_recognize_builtin_types_in_unknown_namespace(name, namespace):
    schema = _create_dummy_schema()
    assert not schema.builtin((name, namespace))


@pytest.mark.parametrize("name", ("", " ", "x", "xyz"))
@pytest.mark.parametrize("namespace", builtin_namespaces +
    ["", " ", "some-dummy-namespace"])
def test_recognize_non_builtin_types(name, namespace):
    schema = _create_dummy_schema()
    assert not schema.builtin((name, namespace))


def test_recognize_custom_mapped_builtins(monkeypatch):
    """User code can register additional XSD built-ins."""
    _monkeypatch_builtin_XSD_type_registry(monkeypatch)
    schema = _create_dummy_schema()
    name = "trla-baba-lan"
    for ns in builtin_namespaces:
        assert not schema.builtin((name, ns))
    Factory.maptag(name, _Dummy)
    for ns in builtin_namespaces:
        assert schema.builtin((name, ns))


def test_resolving_builtin_types(monkeypatch):
    _monkeypatch_builtin_XSD_type_registry(monkeypatch)
    class MockXInteger(XInteger):
        pass
    Factory.maptag("osama", MockXInteger)

    wsdl = testutils.wsdl('<xsd:element name="wu" type="xsd:osama"/>',
        input="wu")
    client = testutils.client_from_wsdl(wsdl)

    element, schema_object = client.sd[0].params[0]
    assert element.name == "wu"
    assert element.type == ("osama", "http://www.w3.org/2001/XMLSchema")
    assert schema_object.__class__ is MockXInteger
    assert schema_object.name == "osama"
    assert schema_object.schema is client.wsdl.schema


def test_translation(monkeypatch):
    """Python <--> XML representation translation on marshall/unmarshall."""
    anObject = _Dummy()
    class MockType(XBuiltin):
        def __init__(self, *args, **kwargs):
            self._mock_translate_log = []
            super(MockType, self).__init__(*args, **kwargs)
        def translate(self, value, topython=True):
            self._mock_translate_log.append((value, topython))
            if topython:
                return anObject
            return "'ollywood"
    _monkeypatch_builtin_XSD_type_registry(monkeypatch)
    Factory.maptag("woof", MockType)

    namespace = "I'm a little tea pot, short and stout..."
    wsdl = testutils.wsdl("""\
      <xsd:element name="wi" type="xsd:woof"/>
      <xsd:element name="wo" type="xsd:woof"/>""", input="wi", output="wo",
        xsd_target_namespace=namespace, operation_name="f")
    client = testutils.client_from_wsdl(wsdl, nosend=True, prettyxml=True)

    # Check suds library's XSD schema input parameter information.
    schema = client.wsdl.schema
    element_in = schema.elements["wi", namespace]
    assert element_in.name == "wi"
    element_out = schema.elements["wo", namespace]
    assert element_out.name == "wo"
    schema_object_in = element_in.resolve()
    schema_object_out = element_out.resolve()
    assert element_in is client.sd[0].params[0][0]
    assert schema_object_in is client.sd[0].params[0][1]
    assert schema_object_in.__class__ is MockType
    assert schema_object_in._mock_translate_log == []
    assert schema_object_out.__class__ is MockType
    assert schema_object_out._mock_translate_log == []

    # Construct operation invocation request - test marshalling.
    request = client.service.f(55)
    assert schema_object_in._mock_translate_log == [(55, False)]
    assert schema_object_out._mock_translate_log == []
    CompareSAX.data2data(request.envelope, """\
<?xml version="1.0" encoding="UTF-8"?>
<Envelope xmlns="http://schemas.xmlsoap.org/soap/envelope/">
   <Header/>
   <Body>
      <wi xmlns="%s">&apos;ollywood</wi>
   </Body>
</Envelope>""" % (namespace,))

    # Process operation response - test unmarshalling.
    response = client.service.f(__inject=dict(reply=suds.byte_str("""\
<?xml version="1.0"?>
<Envelope xmlns="http://schemas.xmlsoap.org/soap/envelope/">
  <Body>
    <wo xmlns="%s">fri-fru</wo>
  </Body>
</Envelope>""" % (namespace,))))
    assert response is anObject
    assert schema_object_in._mock_translate_log == [(55, False)]
    assert schema_object_out._mock_translate_log == [("fri-fru", True)]


def _create_dummy_schema():
    """Constructs a new dummy XSD schema instance."""
    #TODO: Find out how to construct this XSD schema object directly without
    # first having to construct a suds.client.Client from a complete WSDL
    # schema.
    wsdl = testutils.wsdl('<xsd:element name="dummy"/>', input="dummy")
    client = testutils.client_from_wsdl(wsdl)
    return client.wsdl.schema


def _monkeypatch_builtin_XSD_type_registry(monkeypatch):
    """
    Monkeypatches the global suds built-in XSD type dictionary.

    After calling this function, a test is free to mess around with suds
    library's built-in XSD type register (register new ones, change classes
    registered for a particular XSD type, remove registrations, and such) and
    any such changes will be automatically undone at the end of the test.

    If a test does not call this function, any such modifications will be left
    valid in the current global application state and may affect tests run
    afterwards.

    """
    tags = Factory.tags
    assert tags.__class__ is dict
    monkeypatch.setattr(Factory, "tags", dict(tags))
