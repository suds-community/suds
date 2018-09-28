GENERAL DEVELOPMENT NOTES
=================================================

Project's sources are accessible from a `Git version control repository
<http://github.com/suds-community/suds>`_ hosted at Github.

Project development should be tracked in the ``TODO.txt`` file.

* Exact formatting is not important as long as its content is kept formatted
  consistently.
* Done tasks should be marked as such and not deleted.

Separate sections below:

* `TOP-LEVEL PROJECT FILES & FOLDERS`_
* `PYTHON COMPATIBILITY`_
* `RELEASE PROCEDURE`_
* `DEVELOPMENT & TESTING ENVIRONMENT`_
* `PYTHON 2/3 SOURCE CODE COMPATIBILITY`_
* `EXTERNAL DOCUMENTATION`_
* `STANDARDS CONFORMANCE`_
* `PROJECT IMPLEMENTATION NOTES`_
* `REPRODUCING PROBLEMATIC USE CASES`_

For additional design, research & development project notes see the project's
``notes/`` folder.


TOP-LEVEL PROJECT FILES & FOLDERS
=================================================

| build/
| dist/
| suds_jurko.egg-info/

* Folders created during project setup procedure (build/install).

| notes/

* Internal project design, research & development notes.

| suds/

* Basic project source code.

| tests/

* Project test code.

| tools/

* Project development & setup utility scripts. Related internal Python modules
  are located under its ``suds_devel/`` package folder.

| MANIFEST.in

* Build system configuration file listing the files to be included in the
  project's source distribution packages in addition to those automatically
  added to those packages by the used package preparation system.

| HACKING.rst
| LICENSE.txt
| README.txt
| TODO.txt

* Internal project documentation.

| setup.cfg

* Basic project Python configuration.

| setup.py

* Standard Python project setup script.

* Usage examples:

  ``setup.py --help``
    show detailed usage information
  ``setup.py --help-commands``
    show detailed ``setup.py`` command list
  ``setup.py build``
    build the project
  ``setup.py install``
    build & install the project
  ``setup.py register``
    register a project release at PyPI
  ``setup.py sdist``
    prepare a source distribution
  ``setup.py upload``
    upload prepared packages to PyPI

* Usage examples requiring ``setuptools``:

  ``setup.py develop``
    prepare the development environment (add the project folder to the Python
    module search path) the same as if installed using ``easy_install -e`` or
    ``pip install -e``
  ``setup.py test``
    run the project test suite (requires ``pytest``)


PYTHON COMPATIBILITY
=================================================

Base sources should remain Python 2.x compatible. Since the original project
states aiming for Python 2.4 compatibility we do so as well.

The Python 3.0 minor release is not supported. See `Python 3.0 support`_
subsection below for more detailed information.

Test & setup code needs to be implemented using Python 2 & 3 compatible source
code. Setup & setup related scripts need to be implemented so they do not rely
on other pre-installed libraries.

These backward compatibility requirements do not affect internal development
operations such as ``setup.py`` support for uploading a new project distribution
package to PyPI. Such operations need to be supported on the latest Python 2 & 3
releases only and no additional backward compatibility is either tested or
guaranteed for them.

The following is a list of backward incompatible Python features not used in
this project to maintain backward compatibility:

Features missing prior to Python 2.5
------------------------------------

* ``any`` & ``all`` functions.
* ``with`` statement.
* BaseException class introduced and KeyboardInterrupt & SystemExit exception
  classes stopped being Exception subclasses.

  * This means that code wanting to support Python versions prior to this
    release needs to re-raise KeyboardInterrupt & SystemExit exceptions before
    handling the generic 'Exception' case, unless it really wants to gobble up
    those special infrastructural exceptions as well.

* ``try``/``except``/``finally`` blocks.

  * Prior to this Python release, code like the following::

      try:
          A
      except XXX:
          B
      finally:
          C

    was considered illegal and needed to be written using nested ``try`` blocks
    as in::

      try:
          try:
              A
          except XXX:
              B
      finally:
          C

* ``yield`` expression inside a ``try`` block with a ``finally`` clause.

  * Prior to this Python release, code like the following::

      try:
          yield x
      finally:
          do_something()

    is considered illegal, but can be replaced with legal code similar to the
    following::

      try:
          yield x
      except:
          do_something()
          raise
      do_something()

Features missing prior to Python 2.6
------------------------------------

* ``bytes`` type.
* Byte literals, e.g. ``b"quack"``.
* Class decorators.
* ``fractions`` module.
* ``numbers`` module.
* String ``format()`` method.
* Using the ``with`` statement from Python 2.5.x requires the ``from __future__
  import with_statement``.


Features missing prior to Python 2.7
------------------------------------

* Dictionary & set comprehensions.
* Set literals.

Features missing in Python 3.0 & 3.1
------------------------------------

* py2to3 conversion for source files with an explicitly specified UTF-8 BOM.


Python 3.0 support
------------------

Python 3.0 release has been marked as deprecated almost immediately after the
release 3.1. It is not expected that this Python release is actively used
anywhere in the wild. That said, if anyone really wants this version supported
- patches are welcome.

At least the following problems have been found with Python 3.0:

* None of the tools required to properly test our project (setuptools, pip,
  virtualenv, tox, etc.) will work on it.
* When you attempt to setuptools project with Python 3.0, it attempts to use the
  ``sys.stdout.detach()`` method introduced only in Python 3.1. This specific
  issue could be worked around by using ``sys.stdout.buffer`` directly but the
  actual fix has not been attempted. If anyone wants to take this route though
  and work on supporting setuptools on Python 3.0 - be warned that it will most
  likely have other issues after this one as well.
* When applying py2to3 to the project sources, Python will use the current
  user's locale encoding instead of the one specified in the project sources,
  thus causing the operation to fail on some source files containing different
  unicode characters unless the user's environement uses some sort of unicode
  encoding by default, e.g. will fail on some test scripts when run on Windows
  with eastern European regional settings (uses the CP1250 encoding).


RELEASE PROCEDURE
=================================================

1. Document the release correctly in ``README.rst``.

2. Test the project build with the latest available ``setuptools`` project and
   update the ``ez_setup.py`` ``setuptools`` installation script as needed.

  * Use the latest available & tested ``setuptools`` release.
  * If a new ``setuptools`` release drops support for an older Python release,
    update our ``setup.py`` script to use an older ``setuptools`` installation
    script when run using the no longer supported Python release.

    * For example, ``setuptools`` version 2.0 dropped support for Python 2.4 &
      2.5 and so ``setup.py`` uses a separate ``ez_setup_1_4_2.py``
      ``setuptools`` installation script with Python versions older than 2.6.

3. Version identification.

  * Official releases marked with no extra suffix after the basic version
    number.
  * Alfa releases marked with the suffix ``.a#``.
  * Beta releases marked with the suffix ``.b#``.
  * Release candidate releases marked with the suffix ``.rc#``.
  * Development releases marked with the suffix ``.dev#``.
  * Version ordering (as recognized by pip & setuptools)::

      0.5.dev0 < 0.5.dev1 < 0.5.dev5
        < 0.5.a0.dev0 < 0.5.a0.dev5 < 0.5.a0
        < 0.5.a3.dev0 < 0.5.a3.dev5 < 0.5.a3
        < 0.5.b0.dev0 < 0.5.b0.dev5 < 0.5.b0
        < 0.5.b3.dev0 < 0.5.b3.dev5 < 0.5.b3
        < 0.5.rc0.dev0 < 0.5.rc0.dev5 < 0.5.rc0
        < 0.5.rc3.dev0 < 0.5.rc3.dev5 < 0.5.rc3
        < 0.5
      < 0.5.1.dev0 < ...
        ...
        < 0.5.1
      < 0.6.dev0 < ...
        ...
        < 0.6
      < 1.0.dev0 < ...
        ...
        < 1.0

4. Tag in Hg.

  * Name the tag like ``release-<version-info>``, e.g. ``release-0.5``.

5. Prepare official releases based only on tagged commits.

  * Official releases should always be prepared based on tagged revisions with
    no local changes in the used sandbox.
  * Prepare source distribution packages (both .zip & .tar.bz2 formats) and
    upload the prepared source packages to PyPI.

    * Run ``setup.py sdist upload``.

  * Prepare wheel packages for Python 2 & 3 using the latest Python 2 & 3
    environments with the ``wheel`` package installed and upload them to PyPI.

    * Run ``setup.py bdist_wheel upload`` using both Python 2 & 3.

  * Upload the prepared source & wheel packages to the project site.

    * Use the BitBucket project web interface.

6. Next development version identification.

  * If this was a development release.

    * Bump up the existing ``.dev#`` suffix, e.g. change ``0.8.dev2`` to
      ``0.8.dev3``.

  * If this was a non-development release.

    * Bump up the forked project version counter (may add/remove/bump
      alfa/beta/release-candidate mark suffixes as needed).
    * Add the ``.dev0`` suffix, e.g. as in ``0.8.dev0``.

7. Notify whomever the new release might concern.


DEVELOPMENT & TESTING ENVIRONMENT
=================================================

In all command-line examples below pyX, pyXY & pyXYZ represent a Python
interpreter executable for a specific Python version X, X.Y & X.Y.Z
respectively.

Setting up the development & testing environment
------------------------------------------------

``tools/setup_base_environments.py`` script should be used for setting up the
basic Python environments so they support testing our project. The script can be
configured from the main project Python configuration file ``setup.cfg``. It
implements all the backward compatibility tweaks and performs additional
required package installation that would otherwise need to be done manually in
order to be able to test our project in those environments.

These exact requirements and their related version specific tweaks are not
documented elsewhere so anyone interested in the details should consult the
script's sources.

The testing environment is generally set up as follows:

1. Install clean target Python environments.
#. Update the project's ``setup.py`` configuration with information on your
   installed Python environments.
#. Run the ``tools/setup_base_environments.py`` script.

Some older Python environments may have slight issues caused by varying support
levels in different used Python packages, but the basic testing functionality
has been tested to make sure it works on as wide array of supported platforms as
possible.

Examples of such issues:

* Colors not getting displayed on a Windows console terminal, with possibly ANSI
  color code escape sequences getting displayed instead.
* ``pip`` utility can not be run from the command-line using the ``py -m pip``
  syntax for some older versions. In such cases use the more portable ``py -c
  "import pip;pip.main()"`` syntax instead.
* Some specific older Python versions (e.g. 2.4.3) have no SSL support and so
  have to reuse installations downloaded by other Python versions.

Running the project tests - ``tools/run_all_tests.py`` script
-------------------------------------------------------------

``tools/run_all_tests.py`` script is a basic *poor man's tox* development script
that can be used for running the full project test suite using multiple Python
interpreter versions on a development machine.

Intended to be replaced by a more portable ``tox`` based or similar automated
testing solution some time in the future.

Can be configured by tweaking the main project Python configuration file
``setup.cfg``:

* List of target Python environments.
* Each target Python environment's invocation command.

Requires the target Python environment already be set up, and all the packages
required for running the project test suite installed. See the `Setting up the
development & testing environment`_ section for more detailed information.

Automatically installs the project in editable mode in all tested Python
environments.

Caveats:

* This method does not allow you to provide any extra ``pytest`` options when
  running the project test suite.

Running the project tests - ``setup.py test`` command
-----------------------------------------------------

Project tests can also be run for a specific Python environment by running the
project's ``setup.py`` script in that environment and invoking its ``test``
command. E.g. run a command like one of the following ones from the top level
project folder::

  py243 setup.py test
  py27 setup.py test
  py3 setup.py test

Note that the ``setup.py`` script always needs to be called from the top level
project folder.

For most Python versions, the target Python environment needs not be set up
prior to running this command. Where possible (e.g. not for Python 2.4.x or
3.1.x versions), any missing testing requirements will be installed
automatically, but not directly into the target environment but in the current
folder instead. This functionality should be considered a band-aid though, and
setting up the target environment can be better done as described in the
`Setting up the development & testing environment`_ section.

The ``setup.py test`` command will build the project if needed and run its test
suite in the target Python environment. The project does not need to be
preinstalled into the target Python environment for this operation to work, and
neither will the operation leave it installed.

Unless a more restricted test set is selected using ``pytest`` specific
command-line options, ``setup.py test`` command runs the complete project test
suite.

Specific ``pytest`` command-line options may be provided by passing them all as
a single whitespace separated string tunnelled via the ``setup.py test``
command's ``--pytest-args``/``-a`` command-line option.

For example, the following command will run only tests containing ``binding`` in
their name, will stop on first failure and will automatically drop into Python's
post-mortem debugger on failure::

  setup.py test -a "-k binding -x --pdb"

Caveats:

* This method does not currently allow passing ``pytest`` specific command-line
  options containing embedded whitespace.
* When running the ``setup.py test`` command in a Windows Python 2.5 environment
  without an included ctypes module (e.g. 64-bit CPython 2.5 distribution does
  not include ctypes) and having it automatically install the colorama package
  version older than 0.1.11, you will get benign error messages reporting
  colorama's atexit handlers failing. Running the same command again avoids the
  issue since the colorama package will then already be installed. Suggested
  workaround is to use a colorama package version 0.3.2 or newer.

Running the project tests - using ``pytest`` directly
-----------------------------------------------------

To have greater control over the test suite and be able to specify additional
``pytest`` options on the command-line, or be able to run the tests on a
different project installation (e.g. official release installed directly from
PyPI), do the following:

1. Install the project into the target Python environment.

  * Installing the project can be done by either installing it directly into the
    target Python environment using one of the following commands (paths used
    assume the commands are being run from the top level project folder)::

      setup.py install
      easy_install .
      pip install .

    Or the project can be installed in editable mode using one of the following
    commands (so it does not need to be reinstalled after every source code
    change)::

      setup.py develop
      easy_install -e .
      pip install -e .

  * The installation step can be skipped if running Python 2 based project
    tests, and doing so from the top level project folder.

2. Run tests using ``pytest``.

  * If using Python 2.x:

    * Run ``pytest`` from the project's top level or ``tests`` folder::

        py2 -m pytest

  * If using Python 3.x:

    * Since the project uses py2to3 source conversion, you need to build the
      project in order to generate the project's Python 3 sources before they
      can be tested. If the project has been installed in editable mode, then
      simply run the following from the top level project folder::

        setup.py build

      and if it has not then rebuild and reinstall it using one of the following
      commands::

        setup.py develop
        setup.py install

      Note that you might need to manually remove the build folder in order to
      have its contents regenerated when wanting to run the test suite using a
      different Python 3.x interpreter version, as those sources are regenerated
      based solely on the original & processed source file timestamp information
      and not the Python version used to process them.

    * Run ``pytest`` from the the project's ``tests`` folder::

        py3 -m pytest

Each specific test module can also be run directly as a script.

Notes on the folder from which to run the tests:

* When running tests from a folder other than the top level project folder, the
  tested project version needs to first be installed in the used Python
  environment.
* Python 2 tests can be run from the top level project folder, in which case
  they will work even if the project has not been explicitly installed in the
  used Python environment. And even if another project version has been
  installed into the used Python environment, that one will be ignored and the
  one in the current folder used instead.
* Python 3 tests can not be run from the top level project folder or they would
  attempt and fail to use Python 2 based project sources found in the current
  folder.

See the ``pytest`` documentation for a detailed list of available command-line
options. Some interesting ones:

  -l          show local variable state in tracebacks
  --tb=short  shorter traceback information for each failure
  -x          stop on first failure
  --pdb       enter Python debugger on failure

Setting up multiple parallel Python interpreter versions on Windows
-------------------------------------------------------------------

On Windows you might have a problem setting up multiple parallel Python
interpreter versions in case their major and minor version numbers match, e.g.
Python 2.4.3 & 2.4.4. In those cases, standard Windows installer will
automatically remove the previous installation instead of simply adding a new
one. In order to achieve such parallel setup we suggest the following steps:

1. Install the first version in a dummy folder, and do so for the current user
   only.
#. Copy the dummy target folder to the desired folder for the first
   installation, e.g. Python243.
#. Uninstall the original version.
#. Set up a shortcut or a batch script (e.g. py243.cmd) for running this
   interpreter without having to have it added to the system path.
#. Repeat the steps for the second installation.

Installing Python for the current user only is necessary in order to make Python
install all of its files into the target folder and not move some of them into
shared system folders.

Note that this will leave you without start menu or registry entries for these
Python installations. Registry entries should be needed only if you want to run
some external Python package installation tool requiring those entries in order
to determine where to install its package data. In that case you can set those
entries manually, e.g. by using a script similar to the one found at
`<http://nedbatchelder.com/blog/201007/installing_python_packages_from_windows_installers_into.html>`_.


PYTHON 2/3 SOURCE CODE COMPATIBILITY
=================================================

These are notes related to maintaining Python 2/3 source code compatibility in
parts of this project that require it.

Use the ``six <http://pythonhosted.org/six>`` Python 2/3 compatibility support
package to make the compatibility patches simpler. Where a solution provided by
``six`` can not be used, explicitly explain the reason why in a related code
comment.

Do not use ``u"..."`` Python unicode literals since we wish to support Python
3.1 & 3.2 versions which do not support them. Useful site for easily converting
unicode strings to their ``unicode-escape`` encoded representation which can
then be used with the ``six.u()`` helper function:

  http://www.rapidmonkey.com/unicodeconverter


EXTERNAL DOCUMENTATION
=================================================

* SOAP

  * http://www.w3.org/TR/soap

  * Version 1.1.

    * http://www.w3.org/TR/2000/NOTE-SOAP-20000508

  * Version 1.2.

    * Part0: Primer

      * http://www.w3.org/TR/2007/REC-soap12-part0-20070427
      * Errata: http://www.w3.org/2007/04/REC-soap12-part0-20070427-errata.html

    * Part1: Messaging Framework

      * http://www.w3.org/TR/2007/REC-soap12-part1-20070427
      * Errata: http://www.w3.org/2007/04/REC-soap12-part1-20070427-errata.html

    * Part2: Adjuncts

      * http://www.w3.org/TR/2007/REC-soap12-part2-20070427
      * Errata: http://www.w3.org/2007/04/REC-soap12-part2-20070427-errata.html

    * Specification Assertions and Test Collection

      * http://www.w3.org/TR/2007/REC-soap12-testcollection-20070427
      * Errata:
        http://www.w3.org/2007/04/REC-soap12-testcollection-20070427-errata.html

* WS-I Basic Profile 1.1

  * http://www.ws-i.org/Profiles/BasicProfile-1.1.html

* WSDL 1.1

  * http://www.w3.org/TR/wsdl

* XML Schema

  * Part 0: Primer Second Edition - http://www.w3.org/TR/xmlschema-0

    * Non-normative document intended to provide an easily readable description
      of the XML Schema facilities, and is oriented towards quickly
      understanding how to create schemas using the XML Schema language.

  * Part 1: Structures - http://www.w3.org/TR/xmlschema-1
  * Part 2: Datatypes - http://www.w3.org/TR/xmlschema-2


STANDARDS CONFORMANCE
=================================================

There seems to be no complete standards conformance overview for the suds
project. This section contains just some related notes, taken down while hacking
on this project. As more related information is uncovered, it should be added
here as well, and eventually this whole section should be moved to the project's
user documentation.

Interpreting message parts defined by a WSDL schema
---------------------------------------------------

* Each message part is interpreted as a single parameter.

  * What we refer to here as a 'parameter' may not necessarily correspond 1-1 to
    a Python function argument passed when using the suds library's Python
    function interface for invoking web service operations. In some cases suds
    may attempt to make the Python function interfaces more intuitive to the
    user by automatically unwrapping a parameter as defined inside a WSDL schema
    into multiple Python function arguments.

* In order to achieve interoperability with existing software 'in the wild',
  suds does not fully conform to the WSDL 1.1 specification with regard as to
  how message parts are mapped to input data contained in SOAP XML web service
  operation invocation request documents.

  * WSDL 1.1 standard states:

    * 2.3.1 Message Parts.

      * A message may have message parts referencing either an element or a type
        defined in the WSDL's XSD schema.
      * If a message has a message part referencing a type defined in the WSDL's
        XSD schema, then that must be its only message part.

    * 3.5 soap:body.

      * If using document/literal binding and a message has a message part
        referencing a type defined in the WSDL's XSD schema then that part
        becomes the schema type of the enclosing SOAP envelope Body element.

  * Suds supports multiple message parts, each of which may be related either to
    an element or a type.
  * Suds uses message parts related to types, as if they were related to an
    element, using the message part name as the representing XML element name in
    the constructed related SOAP XML web service operation invocation request
    document.
  * WS-I Basic Profile 1.1 standard explicitly avoids the issue by stating the
    following:

    * R2204 - A document/literal binding in a DESCRIPTION MUST refer, in each of
      its soapbind:body element(s), only to wsdl:part element(s) that have been
      defined using the element attribute.

  * Rationale.

    * No other software has been encountered implementing the exact
      functionality specified in the WSDL 1.1 standard.
    * Already done in the original suds implementation.
    * Example software whose implementation matches our own.

      * SoapUI.

        * Tested with version 4.6.1.

      * WSDL analyzer & invoker at `<http://www.validwsdl.com>`_.

WSDL XSD schema interpretation
------------------------------

* ``minOccurs``/``maxOccurs`` attributes on ``all``, ``choice`` & ``sequence``
  schema elements are ignored.

  * Rationale.

    * Already done in the original suds implementation.

  * Extra notes.

    * SoapUI (tested with version 4.6.1).

      * For ``all``, ``choice`` & ``sequence`` schema elements with their
        ``minOccurs`` attribute set to "0", does not explicitly mark elements
        found in such containers as optional.

* Supports sending multiple same-named web service operation parameters, but
  only if they are specified next to each other in the constructed web service
  operation invocation request document.

  * Done by passing a list or tuple of such values to the suds constructed
    Python function representing the web service operation in question.
  * Rationale.

    * Already done in the original suds implementation.

  * Extra notes.

    * Such same-named values break other web service related tools as well, e.g.
      WSDL analyzer & invoker at `<http://www.validwsdl.com>`_.


PROJECT IMPLEMENTATION NOTES
=================================================

Sometimes we have a reason for implementing a feature in a certain way that may
not be obvious at first and which thus deserves an implementation comment
explaining the rationale behind it. In cases when such rationale would then be
duplicated at different places in code, and project implementation note should
be added and identified here, and its respective implementation locations marked
using a comment such as::

  # See 'Project implementation note #42'.

Project implementation note #1
-------------------------------
``pytest`` test parametrizations must be defined so they get ordered the same in
different test processes.

Doing otherwise may confuse the ``pytest`` ``xdist`` plugin used for running
parallel tests using multiple test processes (last tested using
``pytest 2.5.2``, ``xdist 1.10`` & ``execnet 1.2.0``) and may cause it to exit
with errors such as::

  AssertionError: Different tests were collected between gw1 and gw0

Specifically, this means that ``pytest`` test parametrizations should not be
constructed using iteration over unordered collections such as sets or
dictionaries, at least not with Python's hash randomization feature enabled
(implemented as optional since Python 2.6.8, enabled by default since Python
3.3).

See the following ``pytest`` issues for more detailed information:

* `#301 <http://bitbucket.org/hpk42/pytest/issue/301>`_ - serializing collection
  process (per host) on xdist to avoid conflicts/collection errors
* `#437 <http://bitbucket.org/hpk42/pytest/issue/437>`_ - different tests
  collected on two nodes with xdist


REPRODUCING PROBLEMATIC USE CASES
=================================================

Failing web service processing examples can be easily packaged as reproducible
test cases using the suds library 'message & reply injection' technique.

Some things you can achieve using this technique (for examples, see existing
project unit tests):

* Create a client object based on a fixed WSDL string.
* Have a client object send a fixed request string without having it construct
  one based on the loaded WSDL schema and received arguments.
* Have a client object process a fixed reply string without having it send a
  request to an actual external web service.
