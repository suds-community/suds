GENERAL DEVELOPMENT NOTES
=================================================

Project's sources are accessible from a `Mercurial version control repository
<http://bitbucket.org/jurko/suds>`_ hosted at BitBucket.

Project development should be tracked in the ``TODO.txt`` file.

* Exact formatting is not important as long as its content is kept formatted
  consistently.
* Done tasks should be marked as such and not deleted.

Testing:

* ``pytest`` testing framework needed to run unit tests.
* To run the tests using Python 3 first process them and the rest of the library
  sources using the Python ``py2to3`` conversion tool.
* For more detailed information see the `DEVELOPMENT & TESTING ENVIRONMENT`_
  section below.

Reproducing problematic use cases:

* Failing web service processing examples can be easily packaged as reproducible
  test cases using the suds library 'message & reply injection' technique.
* Some things you can achieve using this technique (for examples, see existing
  project unit tests):

  * Create a client object based on a fixed WSDL string.
  * Have a client object send a fixed request string without having it construct
    one based on the loaded WSDL schema and received arguments.
  * Have a client object process a fixed reply string without having it send a
    request to an actual external web service.

Base sources should remain Python 2.x compatible. Since the original project
states aiming for Python 2.4 compatibility we should do so as well.

Python features that need to be avoided for compatibility with older Python
versions:

* Features introduced in Python 2.5.

  * ``any`` & ``all`` functions.
  * ``with`` statement.
  * BaseException class introduced and KeyboardInterrupt & SystemExit exception
    classes stopped being Exception subclasses.

    * This means that code wanting to support Python versions prior to this
      release needs to re-raise KeyboardInterrupt & SystemExit exceptions
      before handling the generic 'Exception' case, unless it really wants to
      gobble up those special infrastructural exceptions as well.

  * ``try``/``except``/``finally`` blocks.

    * Prior to this Python release, code like the following::

        try:
            A
        except XXX:
            B
        finally:
            C

      was considered illegal and needed to be written using nested ``try``
      blocks as in::

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

* Features introduced in Python 2.6.

  * ``bytes`` type.
  * Byte literals, e.g. ``b"quack"``.
  * Class decorators.
  * ``fractions`` module.
  * ``numbers`` module.
  * String ``format()`` method.

* Features introduced in Python 2.7.

  * Dictionary & set comprehensions.
  * Set literals.

External documentation:

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

For additional design, research & development project notes see the project's
``notes/`` folder.


TOP-LEVEL FILES & FOLDERS
=================================================

| .hg/
| .hgignore
| .hgtags

* Mercurial version control related data.

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

| MANIFEST.in

* Build system configuration file listing the files to be included in the
  project's source distribution packages in addition to those automatically
  added to those packages by the used package preparation system.

| HACKING.rst
| LICENSE.txt
| README.txt
| TODO.txt

* Internal project documentation.

| run_all_tests.cmd

* Basic development script for running the full project test suite using
  multiple Python interpreter versions on a Windows development machine.

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
  ``setup.py develop``
    prepare the development environment (add the project folder to the Python
    module search path) the same as if installed using ``easy_install -e`` or
    ``pip install -e``
  ``setup.py install``
    build & install the project
  ``setup.py register``
    register a project release at PyPI
  ``setup.py sdist``
    prepare a source distribution
  ``setup.py test``
    run the project's test suite (requires ``pytest``)
  ``setup.py upload``
    upload prepared packages to PyPI


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

  * Remove the ``(development)`` suffix for official release builds.

4. Tag in Hg.

  * Name the tag like ``release-<version-info>``, e.g. ``release-0.5``.

5. Prepare official releases based only on tagged commits.

  * Official releases should always be prepared based on tagged revisions with
    no local changes in the used sandbox.
  * Prepare source distribution packages (both .zip & .tar.bz2 formats) and
    upload the prepared source packages.

    * Run ``setup.py sdist upload``.

  * Upload the prepared source package to the project site.

    * Use the BitBucket project web interface.

6. Next development version identification.

  * Bump up the forked project version counter.
  * Add back the ``(development)`` suffix, e.g. as in ``0.5 (development)``.

7. Notify whomever the new release might concern.


DEVELOPMENT & TESTING ENVIRONMENT
=================================================

In all command-line examples below pyX, pyXY & pyXYZ represent a Python
interpreter executable for a specific Python version X, X.Y & X.Y.Z
respectively.

Testing environment is generally set up as follows:

1. Install Python.
2. Install ``setuptools`` (using ``setup_ez.py`` or from the source
   distribution).
3. Install ``pip`` using ``setuptools`` (optional).
4. Install ``pytest`` using ``pip`` or ``setuptools``.

This should hold for all Python releases except some older ones explicitly
listed below.

To run all of the project unit tests with a specific interpreter without
additional configuration options run the project's ``setup.py`` script with the
'test' parameter and an appropriate Python interpreter. E.g. run any of the
following from the top level project folder::

  py243 setup.py test
  py27 setup.py test
  py3 setup.py test

To have more control over the test suite run it from the top level project
folder using ``pytest``, e.g.

* Using a Python 2.x interpreter::

    py27 -m pytest

* Using a Python 3.x interpreter::

    py33 setup.py build & py33 -m pytest build

This way you can specify additional ``pytest`` options on the command-line.

In both cases, tests run using Python interpreter version 3.x will be run in the
build folder constructed by the ``setup.py`` script running the ``py2to3`` tool
on the project's sources. You might need to manually remove the build folder in
order to have sources in it regenerated when wanting to run the test suite using
a different Python 3.x interpreter version, as those sources are regenerated
based solely on the original & processed source file timestamp information and
not the Python version used to process them.

See the ``pytest`` documentation for a detailed list of available command-line
options. Some interesting ones:

  -l          show local variable state in tracebacks
  --tb=short  shorter traceback information for each failure
  -x          stop on first failure

On Windows you might have a problem setting up multiple parallel Python
interpreter versions in case they match their major and minor version numbers,
e.g. Python 2.4.3 & 2.4.4. In those cases, standard Windows installer will
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

Notes on setting up specific Python versions
--------------------------------------------

Python 2.4.3

* First see more general Python 2.4.x related notes below (list of compatible
  required package versions, general caveats, etc).
* Does not work with HTTPS links so you can not use the Python package index
  directly, since it, at some point, switched to using HTTPS links only.

  * You could potentially work around this problem by somehow mapping its https:
    links to http: ones or download its link page manually, locally modify it to
    contain http: links and then use that download link page instead of the
    default downloaded one.
  * An alternative and tested solution is to download the required installation
    packages locally using Python 2.4.4 and then install them locally into the
    Python 2.4.3 environment.

    * In the example code below, we name the local installation package storage
      folder ``target_folder`` for illustration purposes only, with
      ``full_target_folder_path`` representing its full path.

    * First use the ``ez_setup.py`` script from the ``setuptools`` 1.4.2 release
      to install ``setuptools``::

        py243 ez_setup_1.4.2.py

    * Then use Python 2.4.4 to download the pip & pytest related installation packages::

        py244 -m easy_install --zip-ok --multi-version --always-copy --exclude-scripts --install-dir "target_folder" pip==1.1
        py244 -c "import pip;pip.main()" install pytest==2.4.1 py==1.4.15 -d "target_folder" --exists-action=i

    * Install ``pip`` from its local installation package (``target_folder``
      name used in this command must not contain any whitespace characters)::

        py243 -m easy_install -f "target_folder" --allow-hosts=None pip==1.1

    * Install ``pytest`` from its local installation packages (``target_folder``
      must be specified as a local file URL in this command, e.g.
      ``file:///full_target_folder_path``)::

        py243 -c "import pip;pip.main()" install pytest==2.4.1 py==1.4.15 -f "file:///full_target_folder_path" --no-index

Python 2.4.x

* Can not run ``pip`` using ``python.exe -m pip``. Workaround is to use one of
  the ``pip`` startup scripts found in the Python installation's ``Scripts``
  folder or to use the following invocation::

    py244 -c "import pip;pip.main()" <regular-pip-options>

* ``pip``

  * 1.1 - last version supporting Python 2.4.

    * Install using::

        py244 -m easy_install pip==1.1

  * Can not be run using ``python.exe -m pip``.

    * Workaround is to use one of the ``pip`` startup scripts found in the
      Python installation's ``Scripts`` folder or the following invocation::

        py244 -c "import pip;pip.main()" <regular-pip-options>

* ``pytest``

  * 2.4.1 - last version supporting Python 2.4.

    * Install::

        py244 -c "import pip;pip.main()" install pytest==2.4.1 py==1.4.15

      * ``pytest`` marked as depending on ``py`` package version >= 1.4.16 which
        is not Python 2.4 compatible (tested up to and including 1.4.18), so
        ``py`` package version 1.4.15 is used instead.

    * With the described configuration ``pytest``'s startup scripts will not
      work (as they explicitly check ``pytest``'s package dependencies), but
      ``pytest`` can still be run using::

        py244 -m pytest <regular-pytest-options>


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
