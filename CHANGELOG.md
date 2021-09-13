Release notes
=============

version 1.0.0-beta.1, 1.0.0-beta.2 (2021-09-13)
------------------------
* Drop support for python 2.x

version 0.8.5 (2021-05-14)
------------------------
* R4201 Any PASSWORD MUST specify a Type attribute
* Compress or decompress message when Content-Encoding is present in headers
* Do not force byte-compilation optimization at level 1

version 0.8.4 (2019-12-21)
------------------------
* Add per invocation timeout
* Ensure request headers set in options are used to fetch definitions

version 0.8.3 (2019-06-24)
------------------------
* Fix pypi description format

version 0.8.2 (2019-06-23)
------------------------
* Add option to disable the sorting of namespaces.
* Add option to allow unknown message parts.

version 0.8.1 (2019-02-06)
------------------------
* Fix bug introduced in 0.8.0, initialize optional arrays with empty lists (@guifran001)

version 0.8.0 (2019-01-31)
------------------------
* [Breaking] Objects should not be instantiated with empty optional attributs, see https://github.com/suds-community/suds/issues/14 for more information. (@guifran001)
* Add WSSE password digest and nonce encoding type (@ovnicraft)

version 0.7.3 (2019-01-04)
------------------------
* Pass header while requesting a WSDL (@guifran001)

version 0.7.2 (2018-10-25)
------------------------
* Fix Travis deploy (@btb)

version 0.7.1 (2018-10-15)
------------------------
* Documentation updates (@phillbaker)
* Add travis deploy (@phillbaker)

version 0.7.0 (2018-09-29)
------------------------

-   Based on revision 712 (1e48fd79a1fc323006826439e469ba7b3d2b5a68)
    from the original `suds` Python library development project\'s
    Subversion repository.
    -   Last officially packaged & released `suds` Python library
        version - 0.4.1.
-   Supported Python versions.
    -   Intended to work with Python 2.4+, except for the following
        versions:
        -   Python 3.0.x - not supported by setuptools, pip or pytest.
    -   Basic sources prepared for Python 2.x.
    -   For using Python 3 the sources first processed by the Python
        `py2to3` tool during the setup procedure.
    -   Tested in the environments listed in the
        [.travis.yml]{.title-ref}
-   Improved support for `decimal` XSD types.
    -   Now modeled internally using Python\'s `decimal.Decimal` type
        instead of `float` - see the new `suds.xsd.sxbuiltin.XDecimal`
        class.
    -   Based on a patch included with [#454](http://fedorahosted.org/suds/ticket/454) for the original
        `suds` library implementation.
    -   In order to get a `decimal` value formatted correctly in
        constructed SOAP request XML documents, pass it to `suds` as
        `decimal.Decimal` or an `int`/`long`.
        -   In general, passing a value of a Python type other than
            `decimal.Decimal` causes that type\'s native string
            representation to be used which might not strictly match the
            lexical representation rules defined in the XSD
            specification for the `decimal` XSD type. For instance, a
            `float` value may be represented using scientific notation,
            or a `fractions.Fraction` may be represented using its
            `numerator` & `denominator` values.
        -   Specific user applications can easily register their own
            customized `XDecimal` implementation using
            `suds.xsd.sxbuiltin.Factory.maptag()` if they want to use
            more specialized `decimal` value handling.
-   Updated how `suds` constructs its cached WSDL & XML identifiers to
    allow cached data reuse between different processes with Python\'s
    hash randomization feature enabled.
    -   Previously constructed using the built-in Python `hash()`
        function, while now it gets constructed using `md5` hash.
    -   Python\'s hash randomization (implemented since Python 2.6.8,
        enabled by default since Python 3.3) was causing different
        processes to mangle their cached data names differently.
    -   Many thanks to Eugene Yakubovich for reporting the issue as well
        as providing the initial fix.
-   Fixed loading recursive WSDL imports.
-   Fixed loading recursive XSD imports/includes.
-   Fixed an infinite recursion bug encountered when looking for an XSD
    type in an XSD schema that does not contain it but itself defines a
    type referencing a recursively defined type from an imported XSD
    schema.
    -   Kudos to Kevin Pors ([krpors]{.title-ref} on BitBucket) for
        detecting, analysing & reporting the issue, plus preparing a
        working quick-fix.
-   Removed never actually used `suds.mx.appender.DictAppender` class.
    -   All code paths that could potentially lead to this class getting
        used convert any encountered dictionaries to
        `suds.sudsobject.Object` instances and report an error in case a
        corresponding XSD type can not be found.
-   Now marshalling passed empty object optional params as empty SOAP
    request XML elements.
    -   Before, passing an empty suds object as an optional parameter
        value was treated the same as not passing that parameter\'s
        value or passing it `None` - the value would not get marshalled
        into the constructed SOAP request at all.
    -   Now, user can still not have the value marshalled by passing
        nothing or `None`, but passing an empty object will get
        marshalled as an actual SOAP request XML element.
    -   Kudos to Nicholas Chen (nicholaschen at BitBucket) & Mark
        Saniscalchi (msaniscalchi at BitBucket) for reporting the issue
        and preparing the initial fix.
-   Made `suds` no longer eat up, log & ignore exceptions raised from
    registered user plugins (detected & reported by Ezequiel Ruiz &
    Bouke Haarsma, patch & test case contributed by Bouke Haarsma).
-   Fixed places in code where `suds` could eat up & silently ignore
    internal Python exceptions like `KeyboardInterrupt` or `SystemExit`.
-   Fixed the exception message used when attempting to construct a
    `suds.sax.element.Element` with a non-`Element` parent.
-   `suds.xsd.sxbase.SchemaObject.content()` now runs in linear instead
    of quadratic time.
-   `DepList` class replaced with a simple `dependency_sort()` function
    taking a single dependency dictionary as input.
    -   The original implementation\'s interface was too heavy-weight
        with no added value.
    -   Anything tried with the original interface outside the basic
        use-case covered by `dependency_sort()` was actually or could be
        easily broken.
    -   `suds.xsd.deplist` module renamed to `suds.xsd.depsort`.
-   Global XSD elements (i.e. top-level + reference elements) are now
    correctly always considered qualified and their `form` attribute
    values are ignored.
    -   Many thanks to Andrew Yager from BitBucket for reporting the
        issue.
-   `suds.cache` module cleanup.
    -   Fixed `FileCache` default cache location related security issue.
        -   Each process now uses a separate temporary folder as its
            default cache location.
        -   Different `FileCache` instances within the same process
            still use the same default cache location and user may still
            explicitly specify a non-default location for each
            `FileCache` instance.
        -   Default cache location now gets removed automatically on
            process exit. User code may disable this removal by setting
            the `FileCache.remove_default_location_on_exit` class
            attribute to False.
        -   Additional external information on this issue:
            -   [Red Hat bug 978696](https://bugzilla.redhat.com/show_bug.cgi?id=978696)
            -   [CVE-2013-2217](http://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2013-2217)
            -   [Ubuntu USN-2008-1: Suds vulnerability](http://www.ubuntu.com/usn/USN-2008-1)
            -   <http://lists.opensuse.org/opensuse-updates/2013-07/msg00062.html>
            -   <https://bugzilla.novell.com/show_bug.cgi?id=827568>
            -   <http://www.openwall.com/lists/oss-security/2013/06/27/8>
        -   Many thanks to Rolf Krahl for the initial report, providing
            links to related external resources as well as helping
            brainstorm the whole issue.
    -   Fixed a bug causing `DocumentCache` to never actually cache any
        documents since one of the last commits made to the original
        `suds` project.
        -   That commit refactored `suds.sax.document.Document` so it is
            no longer derived from `suds.sax.element.Element` while the
            `suds.cache.DocumentCache.put()` implementation simply did
            nothing when passed something other than a
            `suds.sax.element.Element` instance.
            `suds.reader.DocumentReader` on the other hand always passes
            `suds.sax.document.Document` instances to its cache\'s
            `put()` method.
        -   Many thanks to bgr\_ at BitBucket for reporting the issue.
    -   Fixed a bug causing `DocumentCache` & `ObjectCache` to not
        remove their cached files when failing to read data from them or
        process the data read from them.
    -   `FileCache` version file operations now take care to close the
        file in case of a failed read/write operation.
    -   Removed `FileCache.setlocation()` method as it was never used
        inside `suds` and if used from user code would have caused the
        cache to use a specific folder but without making sure that the
        data already stored in it has been prepared for the correct
        `suds` version, as done when passing a location parameter to the
        `FileCache` constructor.
    -   Private and protected `FileCache` interface methods renamed to
        use leading underscores.
        -   `FileCache.getf()` \--\> `FileCache._getf()`.
        -   `FileCache.__fn()` \--\> `FileCache.__filename()`.
        -   `FileCache.checkversion()` \--\>
            `FileCache.__check_version()`.
        -   `FileCache.mktmp()` \--\> `FileCache.__mktmp()`.
        -   `FileCache.open()` \--\> `FileCache.__open()`.
        -   `FileCache.setduration()` \--\>
            `FileCache.__set_duration()`.
        -   `FileCache.validate()` \--\>
            `FileCache.__remove_if_expired()`.
    -   Updated `FileCache` duration implementation.
        -   `FileCache` construction now takes standard
            `datetime.timedelta` duration related keyword arguments
            instead of just `weeks`, `days`, `hours`, `minutes` &
            `seconds`. More to the point, it now also supports
            `milliseconds` & `microseconds` keyword arguments.
        -   Corrected `FileCache` docstring stating that it accepted a
            `months` keyword argument. Using that argument would
            actually have caused a failure when passing it to a
            `datetime.timedelta` initializer internally.
        -   You may now specify multiple duration keyword arguments in
            `FileCache` construction and they will all get summed up
            when constructing the internal `datetime.timedelta` duration
            representation. Before, you could specify such multiple
            arguments, but that would only make the `FileCache` silently
            use duration `0`, i.e. its cache entries would never expire.
-   Fixed `suds.sax.document.Document` str conversion broken around the
    end of 2011 by some accidental interaction between our Python 3
    compatibility fixes and one of the final official `suds` project
    commits making `suds.sax.document.Document` no longer be derived
    from `suds.sax.element.Element`.
    -   Many thanks to Ezequiel Ruiz (emruiz81 at BitBucket) for
        detecting & reporting the issue, as well as providing the
        initial patch.
-   Cleaned up `suds.transport` ASCII/unicode URL/data handling.
    -   `suds.transport.Request` now allows specifying its URL input as
        either a byte or a unicode string with any Python version.
        Internally that URL information is always converted to the used
        Python interpreter\'s native `str` data type (byte string for
        Python versions prior to 3.0, or unicode string for later ones).
    -   Given URLs must not contain any non-ASCII characters, and any
        attempt to create a `suds.transport.Request` with such an
        invalid URL is reported as a `UnicodeError` (either
        `UnicodeDecodeError` or `UnicodeEncodeError` depending on the
        exact Python version and the given URL data type used).
    -   `suds.transport.Reply` & `suds.transport.Request` string
        representation cleaned up and no longer raises an error when
        their message data contains non-ASCII characters.
-   `suds.client` module cleanup.
    -   Removed unused `suds.client.Client.messages` attribute.
    -   Renamed private `SoapClient` & `SimClient` classes:
        -   `SoapClient` \--\> `_SoapClient`.
        -   `SimClient` \--\> `_SimClient`.
    -   Several private methods renamed:
        -   `_SoapClient.location()` \--\> `_SoapClient.__location()`.
        -   `_SoapClient.get_fault()` \--\> `_SoapClient.__get_fault()`.
        -   `_SoapClient.headers()` \--\> `_SoapClient.__headers()`.
    -   `RequestContext` no longer has `client` & `original_envelope`
        attributes.
        -   `client` attribute seems unnecessary.
        -   `original_envelope` was an incorrectly documented bug trap -
            it represented the XML request envelope as a `SAX` XML
            document from after being processed by registered
            `marshalled` plugins, but before being processed by
            registered `sending` plugins. Users should use the
            `envelope` attribute instead which can easily be converted
            into a `SAX` XML document if needed by parsing it using
            `suds.sax.parser.Parser.parse()`. That envelope has been
            consistently processed by all relevant registered plugins
            and matches the data to be sent over the registered
            transport exactly.
    -   Cleaned up `_SoapClient` debug log messages a bit.
-   `suds.reader` module cleanup.
    -   Several private methods renamed:
        -   `DocumentReader.cache()` \--\> `DocumentReader.__cache()`
        -   `DocumentReader.download()` \--\> `DocumentReader.__fetch()`
        -   `DefinitionsReader.cache()` \--\>
            `DefinitionsReader.__cache()`
-   Updated the `BuildError` exception message.
    -   Reformatted.
    -   Converted to a unicode string.
-   Marked `suds.mx.core.Core.node()` as abstract since this base class
    variant is never actually used (both `Encoded` & `Literal` derived
    classes use a different implmentation).
-   `suds.binding.Binding` converted to a new-style class.
-   `suds.tostr()` utility function may no longer silently eat internal
    Python exceptions like `KeyboardInterrupt` or `SystemExit`.
-   Removed the unused `SoapHeadersNotPermitted` exception class.
-   Extra input arguments now reported when invoking web service
    operations taking no input parameters.
-   Using injected requests/replies/error-information with a web service
    operation taking at least one input parameter no longer causes
    `suds` to report an invalid extra argument error.
-   Internal project development improvements.
    -   The project will from now on be distributed as a wheel as well
        as a source distribution.
    -   Added a script for automatically setting up required development
        Python environments for this project, hopefully supporting the
        full range of supported Python versions out of the box.
    -   Improved internal project `HACKING.rst` documentation.
-   `setup.py` improvements.
    -   Python 3.0.x releases explicitly marked as not supported.
    -   Attempting to run `setup.py` in an unsupported Python
        environment now reports a clean error message.
    -   Now uses `setuptools` 1.4.2 with Python 2.4 & 2.5, and
        `setuptools` 5.1 with all more recent Python releases.
    -   Project may now be installed without even in environments when
        you can not install `setuptools`.
        -   In such cases `setup.py` will attempt to use any
            preinstalled `setuptools` version, and if none is available,
            it will disable some of its features and fall back to using
            a plain `distutils` based setup. See the `setup.py` script
            comments for a more detailed listing of all `setup.py`
            features affected by this.
    -   Several installation issues fixes when installing into Python
        3.x environments prior to Python 3.2.3.
    -   When installing the project into a Python 3.x environment prior
        to Python 3.2, `setuptools` is not installed automatically since
        one of its test modules contains UTF-8 BOM characters, which
        would cause such automated installation to fail.
        -   If needed, `setuptools` can still be installed into such
            environments by manually running its `ez_setup.py`
            installation script. Such an installation will encounter the
            same errors but will ignore them, effectively just leaving
            the installed `setuptools` package with one defective test
            module, but fully operational at run-time.
    -   When installing the project into a Window Python 2.5
        environment, you no longer need to manually install a compatible
        `colorama` package versions in order to be able to run the
        project tests.
    -   Package meta-data may now contain non-ASCII characters on
        platforms where that is allowed, namely with all Python versions
        except Python 3.x prior to 3.2.2.
    -   `setup.py test` command improvements.
        -   Now works in Python 2.4.x environments.
        -   Now reports cleanly if it can not be used for some reason,
            both when run and in the command\'s `--help-commands`
            listing.
        -   Better commented the related implementation.
-   Test suite improvements.
    -   Test suite no longer installed together with the project, thus
        no longer causing confusion by existing in the target Python
        environment as a global `tests` package.
        -   The tests may now be run from the source archive, and will
            always run on the `suds` version found installed in the used
            Python environment.
    -   Refactored the quick & dirty batch script used to run all the
        project tests in multiple Python environments to remove much
        code duplication.
    -   Automated project testing in several additional Python
        environment versions.
    -   Added more detailed XSD modeling tests.
    -   Added tests demonstrating how additional or replacement built-in
        XSD types can be registered with `suds`.
    -   All project tests now using Python 2 & 3 compatible source code
        and so no longer need to be built separately for Python 3.
    -   Added new and updated existing `suds.cache` module related
        tests.
    -   Documented that all `pytest` test parametrizations should be
        prepared so they get ordered the same on all test runs. See
        `Project implementation note #1` in `HACKING.rst` for more
        detailed information.
        -   Many thanks to Bruno Oliveira (nicoddemus at BitBucket) for
            researching related `pytest` `xdist` usage problems,
            discovering & explaining the underlying issue as well as
            providing an initial project patch for it.

version 0.6 (2014-01-24)
------------------------

-   Based on revision 712 (1e48fd79a1fc323006826439e469ba7b3d2b5a68)
    from the original `suds` Python library development project\'s
    Subversion repository.
    -   Last officially packaged & released `suds` Python library
        version - 0.4.1.
-   Supported Python versions.
    -   Intended to work with Python 2.4+.
    -   Basic sources prepared for Python 2.x.
    -   For using Python 3 the sources first processed by the Python
        `py2to3` tool during the setup procedure.
    -   Tested in the following environments:
        -   Python 2.4.3/x86, on Windows 7/SP1/x64.
        -   Python 2.4.4/x86, on Windows 7/SP1/x64.
        -   Python 2.7.6/x64, on Windows 7/SP1/x64.
        -   Python 3.2.5/x64, on Windows 7/SP1/x64.
        -   Python 3.3.3/x86, on Windows 7/SP1/x64.
        -   Python 3.3.3/x64, on Windows 7/SP1/x64.
-   Fixed sending HTTP request containing non-ASCII unicode data using
    Python 2.7.
    -   Many thanks to mduggan1 and Alexey Sveshnikov for reporting the
        issue and suggesting patches.
-   Fixed unicode data logging issue (contributed by Bouke Haarsma).
-   `suds.transport.Request` object string representation cleaned up a
    bit -added a missing space before the URL to make it consistent with
    how all the other Request & Reply data is represented in such
    strings.
-   Fixed issue with `suds` client failing to be create its default
    cache object (e.g. because a folder it needs is write protected) and
    thus preventing the client from being created without any chance for
    the user to specify an alternative cache.
    -   The default client cache is now instantiated only if user does
        not explicitly specify some other alternate cache (or even None
        to disable the whole data caching system).
    -   Many thanks to Arthur Clune for reporting the issue.
-   Added explicit tests for URL parameters being passed as unicode or
    single-byte strings under Python 2 but only unicode strings under
    Python 3, and improved how such invalid parameter values are
    reported.
    -   This behaviour matches urllib implementation differences between
        Python 3 and earlier Python interpreter versions.
    -   Many thanks to Mesut Tasci for reporting a related issue and
        preparing the initial patch for it.
-   Extra arguments used when making a web service operation call are
    now reported similar to how this is done for regular Python
    functions.
    -   The extra argument error reporting may be disabled using the new
        `extraArgumentErrors` `suds` option.
    -   Basic idea and the initial implementation for this feature
        contributed by Bouke Haarsma.
-   Corrected a typo in the `BuildError` exception message.
-   Removed partial support for pre-2.4 Python versions since such old
    Python versions are no longer officially supported nor are they
    tested anywhere.
-   Updated documented project links to use HTTP instead of HTTPS
    protocol.
-   Setup improvements.
    -   Fixed setup to work with soft links in the current working
        folder path (contributed by ryanpetrello).
    -   Project now installed as a zipped egg folder.
    -   No longer attempts to work around Python 2.4.3 issues with
        urllib HTTPS downloads since now PyPI updated all of its links
        to HTTPS and the patch would need to become much more complex to
        deal with this, while making the setup much more difficult to
        understand and maintain.
        -   On the other hand, this is now an extremely old Python
            version, so the change is not expected to have much impact.
            Anyone still using this version will just have to work
            around the issue manually, e.g. by downloading the necessary
            packages and running their setup procedures directly.
    -   `long_description` field content wrapped to 72 characters, since
        `PKG-INFO` package distribution metadata file stores this text
        with an 8 space indentation.
-   Improved internal project development documentation.
    -   `HACKING.txt` updated, converted to .rst format & renamed to
        `HACKING.rst`.
    -   Started internal project design, research & development notes
        documentation. Stored in a new `notes/` subfolder, included in
        the project\'s source distribution, but not its builds or
        installations.
-   Internal test suite improvements.
    -   Added unit tests for transport related `Request` & `Reply`
        classes.
    -   Improved `HTTPTransport` related unit tests.
    -   Split up some web service operation invocation request
        construction tests into:
        -   parameter definition tests
        -   argument parsing tests
        -   binding specific request construction tests
    -   Many new tests added & existing ones extended.
    -   Several redundant tests removed.
    -   Added a basic development script for running the project\'s full
        test suite using multiple Python interpreter versions under
        Windows.
    -   Better test support when running with disabled assertion
        optimizations enabled.
    -   Cleaned up support for running test scripts directly as Python
        scripts.
        -   May now be passed pytest command-line options.
        -   Now return an exit code indicating the test result
            (0=success, !0=failure).
-   Known defects.
    -   Extra argument errors not reported for web service operations
        taking no input parameters.
    -   Invalid extra argument error reported when using an injected
        request/reply/ error-information with a web service operation
        taking at least one input parameter.
    -   Security issue CVE-2013-2217 - using fixed default cache
        location.
    -   Incorrect referencing XSD element\'s `form` attribute value
        handling -global XSD elements (i.e. top-level + reference
        elements) sometimes considered unqualified.
    -   Loading recursive WSDL imports is broken.
    -   Loading recursive XSD imports/includes is broken.
    -   Infinite recursion bug encountered when looking for an XSD type
        in an XSD schema that does not contain it but itself defines a
        type referencing a recursively defined type from an imported XSD
        schema.

version 0.5 (2013-11-25)
------------------------

-   Based on revision 712 (1e48fd79a1fc323006826439e469ba7b3d2b5a68)
    from the original `suds` Python library development project\'s
    Subversion repository.
    -   Last officially packaged & released `suds` Python library
        version - 0.4.1.
-   Supported Python versions.
    -   Intended to work with Python 2.4+.
    -   Basic sources prepared for Python 2.x.
    -   For using Python 3 the sources first processed by the Python
        `py2to3` tool during the setup procedure.
    -   Tested in the following environments:
        -   Python 2.4.3/x86, on Windows 7/SP1/x64.
        -   Python 2.4.4/x86, on Windows 7/SP1/x64.
        -   Python 2.7.6/x64, on Windows 7/SP1/x64.
        -   Python 3.2.5/x64, on Windows 7/SP1/x64.
        -   Python 3.3.3/x86, on Windows 7/SP1/x64.
        -   Python 3.3.3/x64, on Windows 7/SP1/x64.
-   Updated the project\'s versioning scheme and detached it from the
    original `suds` project. The original project\'s stall seems to be
    long-term (likely permanent) and making our version information
    match the original one was getting to be too much of a hassle.
    -   For example, with our original versioning scheme, latest pip
        versions recognize our package releases as \'development
        builds\' and refuse to install them by default (supply the
        `--pre` command-line option to force the install anyway).
-   Improved the `suds` date/time handling (contributed by MDuggan1,
    based on a patch attached to issue
    [#353](http://fedorahosted.org/suds/ticket/353) on the original
    `suds` project issue tracker).
    -   Replaces the timezone handling related fix made in the previous
        release.
    -   More detailed testing.
    -   Corrected subsecond to microsecond conversion, including
        rounding.
    -   `DateTime` class no longer derived from `Date` & `Time` classes.
    -   Recognizes more date/time strings valid \'by intuition\'.
    -   Rejects more invalid date/time strings.
        -   Time zone specifiers containing hours and minutes but
            without a colon are rejected to avoid confusion, e.g.
            whether `+121` should be interpreted as `+12:01` or
            `+01:21`.
        -   Time zone specifiers limited to under 24 hours. Without this
            Python\'s timezone UTC offset calculation would raise an
            exception on some operations, e.g. timezone aware
            `datetime.datetime`/`time` comparisons.
-   Removed several project files related to the original developer\'s
    development environment.
-   Removed several internal Mercurial version control system related
    files from the project\'s source distribution package.
-   Better documented the project\'s development & testing environment.
-   Known defects.
    -   Security issue CVE-2013-2217 - using fixed default cache
        location.
    -   Incorrect referencing XSD element\'s `form` attribute value
        handling -global XSD elements (i.e. top-level + reference
        elements) sometimes considered unqualified.
    -   Loading recursive WSDL imports is broken.
    -   Loading recursive XSD imports/includes is broken.
    -   Infinite recursion bug encountered when looking for an XSD type
        in an XSD schema that does not contain it but itself defines a
        type referencing a recursively defined type from an imported XSD
        schema.

version 0.4.1 jurko 5 (2013-11-11)
----------------------------------

-   Based on revision 712 (1e48fd79a1fc323006826439e469ba7b3d2b5a68)
    from the original `suds` Python library development project\'s
    Subversion repository.
    -   Last officially packaged & released `suds` Python library
        version - 0.4.1.
-   Supported Python versions.
    -   Intended to work with Python 2.4+.
    -   Basic sources prepared for Python 2.x.
    -   For using Python 3 the sources first processed by the Python
        `py2to3` tool during the setup procedure.
    -   Tested in the following environments:
        -   Python 2.4.3/x86, on Windows 7/SP1/x64.
        -   Python 2.4.4/x86, on Windows 7/SP1/x64.
        -   Python 2.7.3/x64, on Windows 7/SP1/x64.
        -   Python 3.2.3/x64, on Windows 7/SP1/x64.
        -   Python 3.3.2/x86, on Windows 7/SP1/x64.
        -   Python 3.3.2/x64, on Windows 7/SP1/x64.
-   Improved Python 3 support.
    -   Cache files now used again.
        -   Problems caused by cache files being stored in text mode,
            but attempting to write a bytes object in them. Too eager
            error handling was then causing all such cached file usage
            to fail silently.
    -   `WebFault` containing non-ASCII data now gets constructed
        correctly.
    -   Fixed issue with encoding of authentication in
        `transport/http.py` (contributed by Phillip Alday).
    -   Unicode/byte string handling fixes.
-   Fixed encoding long user credentials for basic HTTP authentication
    in `transport/http.py` (contributed by Jan-Wijbrand Kolman).
-   Fixed an `IndexError` occurring when calling a web service operation
    with only a single input parameter.
-   Fixed a log formatting error, originated in the original `suds`
    (contributed by Guy Rozendorn).
-   Fixed local timezone detection code (contributed by Tim Savage).
-   Setup updated.
    -   Fixed a problem with running the project setup on non-Windows
        platforms.
        -   `version.py` file loading no longer sensitive to the
            line-ending type used in that file.
        -   Stopped using the `distribute` setup package since it has
            been merged back into the original `setuptools` project. Now
            using `setuptools` version 0.7.2 or later.
        -   Automatically downloads & installs an appropriate
            `setuptools` package version if needed.
    -   `distutils` `obsoletes` setup parameter usage removed when run
        using this Python versions earlier than 2.5 as that is the first
        version implementing support for this parameter.
-   Removed different programming techniques & calls breaking
    compatibility with Python 2.4.
    -   String `format()` method.
    -   Ternary if operator.
-   Project `README` file converted to .rst format (contributed by
    Phillip Alday).
-   Corrected internal input/output binding usage. Output binding was
    being used in several places where the input one was expected.
-   HTTP status code 200 XML replies containing a `Fault` element now
    consistently as a SOAP fault (plus a warning about the non-standard
    HTTP status code) both when reporting such faults using exceptions
    or by returning a (status, reason) tuple.
    -   Before this was done only when reporting them using exceptions.
-   Reply XML processing now checks the namespace used for `Envelope` &
    `Body` elements.
-   SOAP fault processing now checks the namespaces used for all
    relevant tags.
-   Plugins now get a chance to process `received()` & `parsed()` calls
    for both success & error replies.
-   SOAP fault reports with invalid Fault structure no longer cause
    `suds` code to break with an \'invalid attribute\' exception.
-   SOAP fault reports with no `<detail>` tag (optional) no longer cause
    `suds` code to break with an \'invalid attribute\' exception when
    run with the `suds` `faults` option set to `False`.
-   Added correct handling for HTTP errors containing no input file
    information. Previously such cases caused `suds` to break with an
    \'invalid attribute\' exception.
-   `SimClient` injection keywords reorganized:
    -   `msg` - request message.
    -   `reply` - reply message (\'msg\' must not be set).
    -   `status` - HTTP status code accompanying the \'reply\' message.
    -   `description` - description string accompanying the \'reply\'
        message.
-   Added `unwrap` option, allowing the user to disable `suds`
    library\'s automated simple document interface unwrapping
    (contributed by Juraj Ivančić).
-   SOAP request parameter XML elements no longer constructed in
    incorrect namespaces in case they have been defined by XSD schema
    elements referencing XSD schema elements with a different target
    namespace.
-   `DocumentStore` instance updated.
    -   Separate `DocumentStore` instances now hold separate data with
        every instance holding all the hardcoded `suds` library XML
        document data.
    -   `DocumentStore` now supports a dict-like `update()` method for
        adding new documents to it.
    -   `Client` instances may now be given a specific `DocumentStore`
        instance using the \'documentStore\' option. Not specifying the
        option uses a shared singleton instance. Specifying the option
        as `None` avoids using any document store whatsoever.
    -   `suds` tests no longer have to modify the global shared
        `DocumentStore` data in order to avoid loading its known data
        from external files and so may no longer affect each other by
        leaving behind data in that global shared `DocumentStore`.
    -   Documents may now be fetched from a `DocumentStore` using a
        transport protocol other than `suds`. When using the `suds`
        protocol an exception is raised if the document could not be
        found in the store while in all other cases `None` is returned
        instead.
    -   Documents in a `DocumentStore` are now accessed as bytes instead
        file-like stream objects.
    -   Made more `DocumentStore` functions private.
-   Corrected error message displayed in case of a transport error.
-   Many unit tests updated and added.
-   Unit tests may now be run using the setuptools `setup.py test`
    command.
    -   Note that this method does not allow passing additional pytest
        testing framework command-line arguments. To specify any such
        parameters invoke the pytest framework directly, e.g. using
        `python -m pytest` in the project\'s root folder.
-   Internal code cleanup.
    -   Removed undocumented, unused and untested `binding.replyfilter`
        functionality.
    -   Binding classes no longer have anything to do with method
        independent Fault element processing.
    -   Removed SoapClient `last_sent()` and `last_received()`
        functions.
    -   Fixed file closing in `reader.py` & `cache.py` modules - used
        files now closed explicitly in case of failed file operations
        instead of relying on the Python GC to close them \'some time
        later on\'.
    -   Fixed silently ignoring internal exceptions like
        `KeyboardInterrupt` in the `cache.py` module.
    -   Removed unused `Cache` module `getf()` & `putf()` functions.
        `getf()` left only in `FileCache` and its derived classes.
-   Known defects.
    -   Security issue CVE-2013-2217 - using fixed default cache
        location.
    -   Incorrect referencing XSD element\'s `form` attribute value
        handling -global XSD elements (i.e. top-level + reference
        elements) sometimes considered unqualified.
    -   Loading recursive WSDL imports is broken.
    -   Loading recursive XSD imports/includes is broken.
    -   Infinite recursion bug encountered when looking for an XSD type
        in an XSD schema that does not contain it but itself defines a
        type referencing a recursively defined type from an imported XSD
        schema.

version 0.4.1 jurko 4 (2012-04-17)
----------------------------------

-   Based on revision 712 (1e48fd79a1fc323006826439e469ba7b3d2b5a68)
    from the original `suds` Python library development project\'s
    Subversion repository.
    -   Last officially packaged & released `suds` Python library
        version - 0.4.1.
-   Supported Python versions.
    -   Intended to work with Python 2.4+.
    -   Basic sources prepared for Python 2.x.
    -   For using Python 3 the sources first processed by the Python
        `py2to3` tool during the setup procedure.
    -   Installation procedure requires the `distribute` Python package
        to be installed on the system.
    -   Tested in the following environments:
        -   Python 2.7.1/x64 on Windows XP/SP3/x64.
        -   Python 3.2.2/x64 on Windows XP/SP3/x64.
-   Cleaned up how the distribution package maintainer name string is
    specified so it does not contain characters causing the setup
    procedure to fail when run using Python 3+ on systems using CP1250
    or UTF-8 as their default code-page.
-   Internal cleanup - renamed bounded to single\_occurrence and
    unbounded to multi\_occurrence.
-   Original term unbounded meant that its object has more than one
    occurrence while its name inferred that \'it has no upper limit on
    its number of occurrences\'.
-   Known defects.
    -   SOAP request parameter XML elements constructed in incorrect
        namespaces in case they have been defined by XSD schema elements
        referencing XSD schema elements with a different target
        namespace.
    -   Security issue CVE-2013-2217 - using fixed default cache
        location.
    -   Incorrect referencing XSD element\'s `form` attribute value
        handling -global XSD elements (i.e. top-level + reference
        elements) sometimes considered unqualified.
    -   Loading recursive WSDL imports is broken.
    -   Loading recursive XSD imports/includes is broken.
    -   Infinite recursion bug encountered when looking for an XSD type
        in an XSD schema that does not contain it but itself defines a
        type referencing a recursively defined type from an imported XSD
        schema.

version 0.4.1 jurko 3 (2011-12-26)
----------------------------------

-   Based on revision 711 (1be817c8a7672b001eb9e5cce8842ebd0bf424ee)
    from the original `suds` Python library development project\'s
    Subversion repository.
    -   Last officially packaged & released `suds` Python library
        version - 0.4.1.
-   Supported Python versions.
    -   Intended to work with Python 2.4+.
    -   Basic sources prepared for Python 2.x.
    -   For using Python 3 the sources first processed by the Python
        `py2to3` tool during the setup procedure.
    -   Installation procedure requires the `distribute` Python package
        to be installed on the system.
    -   Tested in the following environments:
        -   Python 2.7.1/x86 on Windows XP/SP3/x86.
        -   Python 3.2.2/x86 on Windows XP/SP3/x86.
-   Operation parameter specification string no longer includes a
    trailing comma.
-   `suds.xsd.xsbasic.Enumeration` objects now list their value in their
    string representation.
-   `suds.sudsobject.Metadata` `__unicode__()`/`__str__()`/`__repr__()`
    functions no longer raise an `AttributeError` when the object is not
    empty.
-   Fixed a bug with `suds.xsd.sxbasic.TypedContent.resolve()` returning
    an incorrect type when called twice on the same node referencing a
    builtin type with the parameter `nobuiltin=True`.
-   Added more test cases.
-   Known defects.
    -   SOAP request parameter XML elements constructed in incorrect
        namespaces in case they have been defined by XSD schema elements
        referencing XSD schema elements with a different target
        namespace.
    -   Security issue CVE-2013-2217 - using fixed default cache
        location.
    -   Incorrect referencing XSD element\'s `form` attribute value
        handling -global XSD elements (i.e. top-level + reference
        elements) sometimes considered unqualified.
    -   Loading recursive WSDL imports is broken.
    -   Loading recursive XSD imports/includes is broken.
    -   Infinite recursion bug encountered when looking for an XSD type
        in an XSD schema that does not contain it but itself defines a
        type referencing a recursively defined type from an imported XSD
        schema.

version 0.4.1 jurko 2 (2011-12-24)
----------------------------------

-   Based on revision 711 (1be817c8a7672b001eb9e5cce8842ebd0bf424ee)
    from the original `suds` Python library development project\'s
    Subversion repository.
    -   Last officially packaged & released `suds` Python library
        version - 0.4.1.
-   Supported Python versions.
    -   Intended to work with Python 2.4+.
    -   Basic sources prepared for Python 2.x.
    -   For using Python 3 the sources first processed by the Python
        `py2to3` tool during the setup procedure.
    -   Installation procedure requires the `distribute` Python package
        to be installed on the system.
    -   Tested in the following environments:
        -   Python 2.7.1/x86 on Windows XP/SP3/x86.
        -   Python 3.2.2/x86 on Windows XP/SP3/x86.
-   Fixed a bug causing converting a `suds.client.Client` object to a
    string to fail & raise an `IndexError` exception.
    -   Changed the way `suds.client.Client to-string` conversion
        outputs build info. This fixes a bug in the original
        `0.4.1 jurko 1` forked project release causing printing out a
        `suds.client.Client` object to raise an exception due to the
        code in question making some undocumented assumptions on how the
        build information string should be formatted.
-   Known defects.
    -   SOAP request parameter XML elements constructed in incorrect
        namespaces in case they have been defined by XSD schema elements
        referencing XSD schema elements with a different target
        namespace.
    -   Security issue CVE-2013-2217 - using fixed default cache
        location.
    -   Incorrect referencing XSD element\'s `form` attribute value
        handling -global XSD elements (i.e. top-level + reference
        elements) sometimes considered unqualified.
    -   Loading recursive WSDL imports is broken.
    -   Loading recursive XSD imports/includes is broken.
    -   Infinite recursion bug encountered when looking for an XSD type
        in an XSD schema that does not contain it but itself defines a
        type referencing a recursively defined type from an imported XSD
        schema.

version 0.4.1 jurko 1 (2011-12-24)
----------------------------------

-   Based on revision 711 (1be817c8a7672b001eb9e5cce8842ebd0bf424ee)
    from the original `suds` Python library development project\'s
    Subversion repository.
    -   Last officially packaged & released `suds` Python library
        version - 0.4.1.
-   Supported Python versions.
    -   Intended to work with Python 2.4+.
    -   Basic sources prepared for Python 2.x.
    -   For using Python 3 the sources first processed by the Python
        `py2to3` tool during the setup procedure.
    -   Installation procedure requires the `distribute` Python package
        to be installed on the system.
    -   Tested in the following environments:
        -   Python 2.7.1/x86 on Windows XP/SP3/x86.
        -   Python 3.2.2/x86 on Windows XP/SP3/x86.
-   Added Python 3 support:
    -   Based on patches integrated from a Mercurial patch queue
        maintained by [Bernhard
        Leiner](https://bitbucket.org/bernh/suds-python-3-patches).
        -   Last collected patch series commit:
            `96ffba978d5c74df28846b4273252cf1f94f7c78`.
    -   Original sources compatible with Python 2. Automated conversion
        to Python 3 sources during setup.
        -   Automated conversion implemented by depending on the
            `distribute` setup package.
-   Made `suds` work with operations taking choice parameters.
    -   Based on a patch by michaelgruenewald & bennetb01 attached to
        ticket [#342](http://fedorahosted.org/suds/ticket/342) on
        the original `suds` project issue tracker. Comments listed
        related to that ticket seem to indicate that there may be
        additional problems with this patch but so far we have not
        encountered any.
-   Fixed the `DateTimeTest.testOverflow` test to work correctly in all
    timezones.
    -   This test would fail if run directly when run on a computer with
        a positive timezone time adjustment while it would not fail when
        run together with all the other tests in this module since some
        other test would leave behind a nonpositive timezone adjustment
        setting. Now the test explicitly sets its own timezone time
        adjustment to a negative value.
    -   Fixes a bug referenced in the original `suds` project issue
        tracker as ticket
        [#422](http://fedorahosted.org/suds/ticket/422).
-   Corrected accessing `suds.xsd.sxbase.SchemaObject` subitems by
    index.
    -   Fixes a bug referenced in the original `suds` project issue
        tracker as ticket
        [#420](http://fedorahosted.org/suds/ticket/420).
-   Internal code & project data cleanup.
    -   Extracted version information into a separate module.
    -   Added missing release notes for the original `suds` Python
        library project.
    -   Ported unit tests to the `pytest` testing framework.
    -   Cleaned up project tests.
        -   Separated standalone tests from those requiring an external
            web service.
        -   Added additional unit tests.
        -   Added development related documentation - `HACKING.txt`.
        -   Setup procedure cleaned up a bit.
-   Known defects.
    -   Converting a `suds.client.Client` object to a string fails &
        raises an `IndexError` exception.
    -   SOAP request parameter XML elements constructed in incorrect
        namespaces in case they have been defined by XSD schema elements
        referencing XSD schema elements with a different target
        namespace.
    -   Security issue CVE-2013-2217 - using fixed default cache
        location.
    -   Incorrect referencing XSD element\'s `form` attribute value
        handling -global XSD elements (i.e. top-level + reference
        elements) sometimes considered unqualified.
    -   Loading recursive WSDL imports is broken.
    -   Loading recursive XSD imports/includes is broken.
    -   Infinite recursion bug encountered when looking for an XSD type
        in an XSD schema that does not contain it but itself defines a
        type referencing a recursively defined type from an imported XSD
        schema.

Original suds library release notes
===================================

**version 0.4.1 (2010-10-15)**

-   \<undocumented\>
-   Known defects.
    -   SOAP request parameter XML elements constructed in incorrect
        namespaces in case they have been defined by XSD schema elements
        referencing XSD schema elements with a different target
        namespace.
    -   Security issue CVE-2013-2217 - using fixed default cache
        location.
    -   Incorrect referencing XSD element\'s `form` attribute value
        handling -global XSD elements (i.e. top-level + reference
        elements) sometimes considered unqualified.
    -   Loading recursive WSDL imports is broken.
    -   Loading recursive XSD imports/includes is broken.
    -   Infinite recursion bug encountered when looking for an XSD type
        in an XSD schema that does not contain it but itself defines a
        type referencing a recursively defined type from an imported XSD
        schema.

**version 0.4 (2010-09-08)**

-   Fix spelling errors in spec description.
-   Fix source0 URL warning.
-   Updated caching to not cache intermediate WSDLs.
-   Added `DocumentCache` which caches verified XML documents as text.
    User can choose.
-   Added `cachingpolicy` option to allow user to specify whether to
    cache XML documents or WSDL objects.
-   Provided for repeating values in reply for message parts consistent
    with the way this is handled in nested objects.
-   Added `charset=utf-8` to stock content-type HTTP header.
-   Added `<?xml version="1.0" encoding="UTF-8"?>` to outgoing SOAP
    messages.
-   Detection of faults in successful (http=200) replies and raise
    `WebFault`. Search for `<soapenv:Fault/>`.
-   Add plugins facility.
-   Fixed Tickets: #251, #313, #314, #334.

**version 0.3.9 (2009-12-17)**

-   Bumped python requires to 2.4.
-   Replaced stream-based caching in the transport package with
    document-based caching.
-   Caches pickled `Document` objects instead of XML text. 2x Faster!
-   No more SAX parsing exceptions on damaged or incomplete cached
    files.
-   Cached WSDL objects. Entire `Definitions` object including contained
    `Schema` object cached via pickle.
-   Copy of SOAP encoding schema packaged with `suds`.
-   Refactor `Transports` to use `ProxyHandler` instead of
    `urllib2.Request.set_proxy()`.
-   Added WSSE enhancements `<Timestamp/>` and `<Expires/>` support.
    See: Timestamp token.
-   Fixed Tickets: #256, #291, #294, #295, #296.

**version 0.3.8 (2009-12-09)**

-   Included Windows NTLM Transport.
-   Add missing `self.messages` in `Client.clone()`.
-   Changed default behavior for WSDL `PartElement` to be optional.
-   Add support for services/ports defined without `<address/>` element
    in WSDL.
-   Fix `sax.attribute.Element.attrib()` to find by name only when ns is
    not specified; renamed to `Element.getAttribute()`.
-   Update `HttpTransport` to pass timeout parameter to urllib2 open()
    methods when supported by urllib2.
-   Add `null` class to pass explicit NULL values for parameters and
    optional elements.
-   SOAP encoded array `soap-enc:Array` enhancement for rpc/encoded.
    Arrays passed as python arrays - works like document/literal now. No
    more using the factory to create the Array. Automatically includes
    `arrayType` attribute. E.g. `soap-enc:arrayType="Array[2]"`.
-   Reintroduced ability to pass complex (objects) using python dict
    instead of `suds` object via factory.
-   Fixed tickets: #84, #261, #262, #263, #265, #266, #278,
    #280, #282.

**version 0.3.7 (2009-10-16)**

-   Better SOAP header support
-   Added new transport `HttpAuthenticated` for active (not passive)
    basic authentication.
-   New options (`prefixes`, `timeout`, `retxml`).
-   WSDL processing enhancements.
-   Expanded builtin XSD type support.
-   Fixed `<xs:include/>`.
-   Better XML `date`/`datetime` conversion.
-   `Client.clone()` method added for lightweight copy of client object.
-   XSD processing fixes/enhancements.
-   Better `<simpleType/>` by `<xs:restriction/>` support.
-   Performance enhancements.
-   Fixed tickets: #65, #232, #233, #235, #241, #242, #244,
    #247, #254, #254, #256, #257, #258.

**version 0.3.6 (2009-04-31)**

-   Change hard coded `/tmp/suds` to `tempfile.gettempdir()` and create
    `suds/` on demand.
-   Fix return type for `Any.get_attribute()`.
-   Update HTTP caching to ignore `file://` URLs.
-   Better logging of messages when only the reply is injected.
-   Fix `XInteger` and `XFloat` types to translate returned arrays
    properly.
-   Fix `xs:import` schema with same namespace.
-   Update parser to not load external references and add
    `Import.bind()` for `XMLSchema.xsd` location.
-   Add schema doctor - used to patch XSDs at runtime (see
    `Option.doctor`).
-   Fix deprecation warnings in python 2.6.
-   Add behavior for `@default` defined on `<element/>`.
-   Change `@xsi:type` value to always be qualified for doc/literal
    (reverts 0.3.5 change).
-   Add `Option.xstq` option to control when `@xsi:type` is qualified.
-   Fixed Tickets: #64, #129, #205, #206, #217, #221, #222,
    #224, #225, #228, #229, #230.

**version 0.3.5 (2009-04-16)**

-   Adds HTTP caching. Default is (1) day. Does not apply to method
    invocation. See: documentation for details.
-   Removed checking fedora version check in spec since no longer
    building \< fc9.
-   Updated makefile to roll tarball with tar.sh.
-   Moved bare/wrapped determination to WSDL for document/literal.
-   Refactored `Transport` into a package (provides better logging of
    HTTP headers).
-   Fixed Tickets: #207, #209, #210, #212, #214, #215.

**version 0.3.4 (2009-02-24)**

-   Static (automatic)
    `Import.bind('http://schemas.xmlsoap.org/soap/encoding/')`, users no
    longer need to do this.
-   Basic ws-security with {{{UsernameToken}}} and clear-text password
    only.
-   Add support for `sparse` SOAP headers via passing dictionary.
-   Add support for arbitrary user defined SOAP headers.
-   Fixes service operations with multiple SOAP header entries.
-   Schema loading and dereferencing algorithm enhancements.
-   Nested SOAP multirefs fixed.
-   Better (true) support for `elementFormDefault="unqualified"`
    provides more accurate namespacing.
-   WSDL part types no longer default to WSDL `targetNamespace`.
-   Fixed Tickets: #4, #6, #21, #32, #62, #66, #71, #72, #114,
    #155, #201.

**version 0.3.3 (2008-11-31)**

-   No longer installs (tests) package.
-   Implements API-3 proposal
    (<https://fedorahosted.org/suds/wiki/Api3Proposal>).
    -   Pluggable transport.
    -   Keyword method arguments.
    -   Basic HTTP authentication in default transport.
-   Add namespace prefix normalization in SOAP message.
-   Better SOAP message pruning of empty nodes.
-   Fixed Tickets: #51 - #60.

**version 0.3.2 (2008-11-07)**

-   SOAP {{{MultiRef}}} support `(1st pass added r300)`.
-   Add support for new schema tags:
    -   `<xs:include/>`
    -   `<xs:simpleContent/>`
    -   `<xs:group/>`
    -   `<xs:attributeGroup/>`
-   Added support for new xs \<\--\> python type conversions:
    -   `xs:int`
    -   `xs:long`
    -   `xs:float`
    -   `xs:double`
-   Revise marshaller and binding to further sharpen the namespacing of
    nodes produced.
-   Infinite recursion fixed in `xsd` package `dereference()` during
    schema loading.
-   Add support for `<wsdl:import/>` of schema files into the WSDL root
    `<definitions/>`.
-   Fix double encoding of (&).
-   Add Client API:
    -   `setheaders()` - same as keyword but works for all invocations.
    -   `addprefix()` - mapping of namespace prefixes.
    -   `setlocation()` - override the location in the WSDL; same as
        keyword except for all calls.
    -   `setproxy()` - same as proxy keyword but for all invocations.
-   Add proper namespace prefix for SOAP headers.
-   Fixed Tickets: #5, #12, #34, #37, #40, #44, #45, #46, #48,
    #49, #50, #51.

**version 0.3.1 (2008-10-01)**

-   Quick follow up to the 0.3 release that made working multi-port
    service definitions harder then necessary. After consideration (and
    a good night sleep), it seemed obvious that a few changes would make
    this much easier:
    1)  filter out the non-SOAP bindings - they were causing the real
        trouble;
    2)  since most servers are happy with any of the SOAP bindings (SOAP
        1.1 and 1.2), ambiguous references to methods when invoking then
        without the port qualification will work just fine in almost
        every case. So, why not just allow `suds` to select the port.
        Let us not make the user do it when it is not necessary. In most
        cases, users on 0.2.9 and earlier will not have to update their
        code when moving to 0.3.1 as they might have in 0.3.

**version 0.3 (2008-09-30)**

-   Extends the support for multi-port services introduced in 0.2.9.
    This addition, provides for multiple services to define the *same*
    method and `suds` will handle it properly. See section \'SERVICES
    WITH MULTIPLE PORTS:\'.
-   Add support for multi-document document/literal SOAP binding style.
    See section \'MULTI-DOCUMENT Document/Literal:\'.
-   Add support for `xs:group`, `xs:attributeGroup` tags.
-   Add `Client.last_sent()` and `Client.last_received()`.

**version 0.2.9 (2008-09-09)**

-   Support for multiple ports within a service.
-   Attribute references `<xs:attribute ref=""/>`.
-   Make XML special character encoder in sax package - pluggable.

**version 0.2.8 (2008-08-28)**

-   Update document/literal binding to always send the document root
    referenced by the `<part/>`. After yet another review of the space
    and user input, seems like the referenced element is ALWAYS the
    document root.
-   Add support for \'binding\' `schemaLocation`s to namespace-uri. This
    is for imports that do not specify a `schemaLocation` and still
    expect the schema to be downloaded. E.g. Axis references
    \'<http://schemas.xmlsoap.org/soap/encoding/>\' without a
    schemaLocation. So, by doing this:

        >
        > from suds.xsd.sxbasic import Import
        > Import.bind('http://schemas.xmlsoap.org/soap/encoding/')
        >

    The schema is bound to a `schemaLocation` and it is downloaded.

-   Basic unmarshaller does not need a [schema]{.title-ref}. Should have
    been removed during refactoring but was missed.
-   Update client to pass kwargs to `send()` and add `location` kwarg
    for overriding the service location in the WSDL.
-   Update marshaller to NOT emit XML for object attributes that
    represent elements and/or attributes that are *both* optional and
    `value=None`.
    -   Update factory (builder) to include all attributes.
    -   Add `optional()` method to `SchemaObject`.
-   Update WSDL to override namespace in operation if specified.
-   Fix schema loading issue - build all schemas before processing
    imports.
-   Update packaging in preparation of submission to fedora.

**version 0.2.7 (2008-08-11)**

-   Add detection/support for document/literal - wrapped and unwrapped.
-   Update document/literal {wrapped} to set document root (under
    \<body/\>) to be the wrapper element (w/ proper namespace).
-   Add support for `<sequence/>`, `<all/>` and `<choice/>` having
    `maxOccurs` and have the. This causes the unmarshaller to set values
    for elements contained in an unbounded collection as a list.
-   Update client.factory (builder) to omit children of `<choice/>`
    since the \'user\' really needs to decide which children to include.
-   Update flattening algorithm to prevent re-flattening of types from
    imported schemas.
-   Adjustments to flattening/merging algorithms.

**version 0.2.6 (2008-08-05)**

-   Fix ENUMs broken during `xsd` package overhaul.
-   Fix type as defined in ticket #24.
-   Fix duplicate param names in method signatures as reported in ticket
    #30.
-   `suds` licensed as LGPL.
-   Remove logging setup in `suds.__init__()` as suggested by patch in
    ticket #31. Users will now need to configure the logger.
-   Add support for `Client.Factory.create()` alt: syntax for fully
    qualifying the type to be built as: `{namespace}name`. E.g.:

        > client.factory.create('{http://blabla.com/ns}Person')

**version 0.2.5 (2008-08-01)**

-   Overhauled the `xsd` package. This new (merging) approach is simpler
    and should be more reliable and maintainable. Also, should provide
    better performance since the merged schema performs lookups via
    dictionary lookup. This overhaul should fix current `TypeNotFound`
    and `<xs:extension/>` problems, I hope :-).
-   Fixed dateTime printing bug.
-   Added infinite recursion prevention in `builder.Builder` for XSD
    types that contain themselves.

**version 0.2.4 (2008-07-28)**

-   Added support for WSDL imports: `<wsdl:import/>`.
-   Added support for XSD\<-\>python type conversions (thanks: Nathan
    Van Gheem) for:
    -   `xs:date`
    -   `xs:time`
    -   `xs:dateTime`
-   Fixed:
    -   Bug: Schema `<import/>` with `schemaLocation` specified.
    -   Bug: Namespaces specified in service description not valid until
        client/ proxy is printed.

**version 0.2.3 (2008-07-23)**

-   Optimizations.

**version 0.2.2 (2008-07-08)**

-   Update exceptions to be more /standard/ python by using
    `Exception.__init__()` to set `Exception.message` as suggested by
    ticket #14; update bindings to raise `WebFault` passing (p).
-   Add capability in bindings to handle multiple root nodes in the
    returned values; returned as a composite object unlike when lists
    are returned.
-   Fix `soapAction` to be enclosed by quotes.
-   Add support for `<xs:all/>`.
-   Fix `unbounded()` method in `SchemaObject`.
-   Refactored schema into new `xsd` package. Files just getting too
    big. Added `execute()` to `Query` and retrofitted `suds` to
    `execute()` query instead of using `Schema.find()` directly. Also,
    moved hokey `start()` methods from schema, as well as, query
    incrementation.
-   Add `inject` keyword used to `inject` outbound SOAP messages and/or
    inbound reply messages.
-   Refactored SoapClient and
    1)  rename `send()` to `invoke(`)
    2)  split message sending from `invoke()` and place in `send()`
-   Add `TestClient` which allows for invocation kwargs to have
    `inject={'msg=, and reply='}` for message and reply injection.
-   Add `Namespace` class to `sax` for better management of namespace
    behavior; retrofix `suds` to import and use `Namespace`.
-   Change the default namespace used to resolve referenced types
    (having attributes `@base=""`, `@type=""`) so that when no prefix is
    specified: uses XML (node) namespace instead of the
    `targetNamespace`.
-   Apply fix as defined by <davidglick@onenw.org> in ticket #13.
-   Update service definition to print to display service methods as
    `my_method(xs:int arg0, Person arg1)` instead of
    `my_method(arg0{xs:int}, arg1{Person})` which is more like
    traditional method signatures.
-   Add XSD/python type conversion to unmarshaller (`XBoolean` only);
    refactor unmarshaller to use `Content` class which makes APIs
    cleaner, adds symmetry between marshaller(s) and unmarshaller(s),
    provides good mechanism for schema-property based type conversions.
-   Refactored marshaller with Appenders; add `nobuiltin` flag to
    `resolve()` to support fix for `returned_type()` and
    `returned_collection()` in bindings.
-   Add support for (202, 204) HTTP codes.
-   Add `XBoolean` and mappings; add `findattr()` to `TreeResolver` in
    preparation for type conversions.
-   Updated schema and schema property loading (deep recursion stopped);
    Changed `Imported` schemas so then no longer copy imported schemas,
    rather the import proxies find requests; Add `ServiceDefinition`
    class which provides better service inspection; also provides
    namespace mapping and show types; schema property API simplified;
    support for `xs:any` and `xs:anyType` added; Some schema lookup
    problems fixed; Binding classes refactored slightly; A lot of debug
    logging added (might have to comment some out for performance -some
    of the args are expensive).
-   Add `sudsobject.Property`; a property is a special `Object` that
    contains a `value` attribute and is returned by the `Builder`
    (factory) for schema-types without children such as: `<element/>`
    and `<simpleType/>`; `Builder`, `Marshaller` and `Resolver` updated
    to handle `Properties`; `Resolver` and `Schema` also updated to
    handle attribute lookups (this was missing).
-   Add groundwork for user defined SOAP headers.
-   Fix `elementFormDefault` per ticket #7
-   Remove unused kwargs from bindings; cache bindings in WSDL; retrofit
    legacy `ServiceProxy` to delegate to {new} `Client` API; remove
    keyword `nil_supported` in favor of natural handling by `nillable`
    attribute on `<element/>` within schemas.
-   Add support for `<element/>` attribute flags (`nillable` and
    `form`).
-   Add the `Proxy` (2nd generation API) class.
-   Add accessor/conversion functions so that users do not need to
    access `__x__` attributes. Also add `todict()` and `get_items()` for
    easy conversion to dictionary and iteration.
-   Search top-level elements for `@ref` before looking deeper.
-   Add `derived()` to `SchemaObject`. This is needed to ensure that all
    derived types (WSDL classes) are qualified by `xsi:type` without
    specifying the `xsi:type` for all custom types as did in earlier
    `suds` releases. Update the literal marshaller to only add the
    `xsi:type` when the type needs to be specified.
-   Change ns promotion in `sax` to prevent ns promoted to parent when
    parent has the prefix.
-   Changed binding `returned_type()` to return the (unresolved)
    `Element`.
-   In order to support the new features and fix reported bugs, I\'m in
    the process of refactoring and hopefully evolving the components in
    `suds` that provide the input/output translations:

    -   `Builder` (translates: XSD objects =\> python objects)
    -   `Marshaller` (translates: python objects =\> XML/SOAP)
    -   `Unmarshaller` (translates: XML/SOAP =\> python objects)

    This evolution will provide better symmetry between these components
    as follows:

    The `Builder` and `Unmarshaller` will produce python (subclass of
    `sudsobject.Object`) objects with:

    -   `__metadata__.__type__` = XSD type (`SchemaObject`)
    -   subclass name (`__class__.__name__`) = schema-type name

    and

    The `Marshaller`, while consuming python objects produced by the
    `Builder` or `Unmarshaller`, will leverage this standard information
    to produce the appropriate output (XML/SOAP).

    The 0.2.1 code behaves *mostly* like this but \... not quite. Also,
    the implementations have some redundancy.

    While doing this, it made sense to factor out the common schema-type
    \"lookup\" functionality used by the `Builder`, `Marshaller` and
    `Unmarshaller` classes into a hierarchy of `Resolver` classes. This
    reduces the complexity and redundancy of the `Builder`, `Marshaller`
    and `Unmarshaller` classes and allows for better modularity. Once
    this refactoring was complete, the difference between the
    literal/encoded `Marshallers` became very small. Given that the
    amount of code in the `bindings.literal` and `bindings.encoded`
    packages was small (and getting smaller) and in the interest of
    keeping the `suds` code base compact, I moved all of the marshalling
    classes to the `bindings.marshaller` module. All of the
    `bindings.XX` sub-packages will be removed.

    The net effect:

    All of the `suds` major components:

    -   client (old: service proxy)
    -   WSDL
        -   schema (xsd package)
        -   resolvers
    -   output (marshalling)
    -   builder
    -   input (unmarshalling)

    Now have better:

    -   modularity
    -   symmetry with regard to `Object` metadata.
    -   code re-use (\< 1% code duplication \-\-- I hope)
    -   looser coupling

    and better provide for the following features/bug-fix:

    -   Proper level of XML element qualification based on
        `<schema elementFormDefault=""/>` attribute. This will ensure
        that when `elementFormDefault="qualified"`, `suds` will include
        the proper namespace on root elements for both literal and
        encoded bindings. In order for this to work properly, the
        literal marshaller (like the encoded marshaller) needed to be
        schema-type aware. Had I added the same schema-type lookup as
        the encoded marshaller instead of the refactoring described
        above, the two classes would have been almost a complete
        duplicate of each other :-(

-   The builder and unmarshaller used the `schema.Schema.find()` to
    resolve schema-types. They constructed a path as `person.name.first`
    to resolve types in proper context. Since `Schema.find()` was
    stateless, it resolved the intermediate path elements on every call.
    The new resolver classes are stateful and resolve child types *much*
    more efficiently.
-   Prevent name collisions in `sudsobject.Object` like the `items()`
    method. I\'ve moved all methods (including class methods) to a
    `Factory` class that is included in the `Object` class as a class
    attr (`__factory__`). Now that *all* attributes have python built-in
    naming, we should not have any more name collisions. This of course
    assumes that no WSDL/schema entity names will have a name with the
    python built-in naming convention but I have to draw the line
    somewhere. :-)

**version 0.2.1 (2008-05-08)**

-   Update the `schema.py` `SchemaProperty` loading sequence so that the
    schema is loaded in 3 steps:

    1)  Build the raw tree.
    2)  Resolve dependencies such as `@ref` and `@base`.
    3)  Promote grandchildren as needed to flatten (denormalize) the
        tree.

    The WSDL was also changed to only load the schema once and store it.
    The schema collection was changed to load schemas in 2 steps:

    1)  Create all raw schema objects.
    2)  Load schemas.

    This ensures that local imported schemas can be found when
    referenced out of order. The `sax.py` `Element` interface changed:
    `attribute()` replaced by `get()` and `set()`. Also, `__getitem__()`
    and `__setitem__()` can be used to access attribute values. Epydocs
    updated for `sax.py`. And \... last `<element ref=/>` now supported
    properly.

-   Fix logging by: NOT setting to info in `suds.__init__.logger()`; set
    handler on root logger only; moved logger (log) from classes to
    modules and use \_\_name\_\_ for logger name. NOTE: This means that
    to enable SOAP message logging one should use:

        >
        > logger('suds.serviceproxy').setLevel(logging.DEBUG)
        >

    instead of:

        >
        > logger('serviceproxy').setLevel(logging.DEBUG)
        >

-   Add support for XSD schema `<attribute/>` nodes which primarily
    affects objects returned by the `Builder`.
-   Update `serviceproxy.py:set_proxies()` to log `DEBUG` instead of
    `INFO`.
-   Enhance schema `__str__()` to show both the raw XML and the model
    (mostly for debugging).

**version 0.2 (2008-04-28)**

-   Contains the first cut at the rpc/encoded SOAP style.
-   Replaced `Property` class with `suds.sudsobject.Object`. The
    `Property` class was developed a long time ago with a slightly
    different purpose. The `suds` `Object` is a simpler (more straight
    forward) approach that requires less code and works better in the
    debugger.
-   The `Binding` (and the encoding) is selected on a per-method basis
    which is more consistent with the WSDL. In \<= 0.1.7, the binding
    was selected when the `ServiceProxy` was constructed and used for
    all service methods. The binding was stored as `self.binding`. Since
    the WSDL provides for a separate binding style and encoding for each
    operation, `suds` needed to be change to work the same way.
-   The `nil_supported` and `faults` flag(s) passed into the service
    proxy using \*\*kwargs. In addition to these flags, a `http_proxy`
    flag has been added and is passed to the `urllib2.Request` object.
    The following args are supported:
    -   `faults` = Raise faults raised by server (default:`True`), else
        return tuple from service method invocation as (HTTP code,
        object).
    -   `nil_supported` = The bindings will set the `xsi:nil="true"` on
        nodes that have a `value=None` when this flag is `True`
        (default:`True`). Otherwise, an empty node `<x/>` is sent.
    -   `proxy` = An HTTP proxy to be specified on requests
        (default:`{}`). The proxy is defined as `{protocol:proxy,}`.
-   HTTP proxy supported (see above).
-   `ServiceProxy` refactored to delegate to a `SoapClient`. Since the
    service proxy exposes web services via `getattr()`, any attribute
    (including methods) provided by the `ServiceProxy` class hides WS
    operations defined by the WSDL. So, by moving everything to the
    `SoapClient`, WSDL operations are no longer hidden without having to
    use *hokey* names for attributes and methods in the service proxy.
    Instead, the service proxy has `__client__` and `__factory__`
    attributes (which really should be at low risk for name collision).
    For now the `get_instance()` and `get_enum()` methods have not been
    moved to preserve backward compatibility. Although, the preferred
    API change would to replace:

        > service = ServiceProxy('myurl')
        > person = service.get_instance('person')

    with something like:

        > service = ServiceProxy('myurl')
        > person = service.__factory__.get_instance('person')

    After a few releases giving time for users to switch the new API,
    the `get_instance()` and `get_enum()` methods may be removed with a
    notice in big letters.

-   Fixed problem where a WSDL does not define a `<schema/>` section and
    `suds` can not resolve the prefixes for the
    `http://www.w3.org/2001/XMLSchema` namespace to detect builtin types
    such as `xs:string`.

**version 0.1.7 (2008-04-08)**

-   Added `Binding.nil_supported` to control how property values (out) =
    `None` and empty tag (in) are processed.
    -   `service.binding.nil_supported = True` \-- means that property
        values = `None` are marshalled (out) as `<x xsi:nil=true/>` and
        \<x/\> is unmarshalled as `''` and `<x xsi:nil/>` is
        unmarshalled as `None`.
    -   `service.binding.nil_supported = False` \-- means that property
        values = `None` are marshalled (out) as `<x/>` *and*
        `<x xsi:nil=true/>` is unmarshalled as `None`. The `xsi:nil` is
        really ignored.
    -   THE DEFAULT IS `True`.
-   Sax handler updated to handle `multiple character()` callbacks when
    the sax parser \"chunks\" the text. When the `node.text` is `None`,
    the `node.text` is set to the characters. Else, the characters are
    appended. Thanks - \'<andrea.spinelli@imteam.it>\'.
-   Replaced special `text` attribute with `__text__` to allow for
    natural elements named \"text\".
-   Add unicode support by:
    -   Add `__unicode__()` to all classes with `__str__()`.
    -   Replace all `str()` calls with `unicode()`.
    -   `__str__()` returns UTF-8 encoded result of `__unicode__()`.
-   XML output encoded as UTF-8 which matches the HTTP header and
    supports unicode.
-   `SchemaCollection` changed to provide the `builtin()` and `custom()`
    methods. To support this, `findPrefixes()` was added to the
    `Element` in `sax.py`. This is a better approach anyway since the
    WSDL and schemas may have many prefixes to
    \'<http://www.w3.org/2001/XMLSchema>\'. Tested using both doc/lit
    and rpc/lit bindings.
-   Refactored bindings packages from document & rpc to literal &
    encoded.
-   Contains the completion of *full* namespace support as follows:
    -   Namespace prefixes are no longer stripped from attribute values
        that reference types defined in the WSDL.
    -   Schema\'s imported using `<import/>` should properly handle
        namespace and prefix mapping and re-mapping as needed.
    -   All types are resolved, using fully qualified (w/ namespaces)
        lookups.
    -   `Schema.get_type()` supports paths with and without ns prefixes.
        When no prefix is specified the type is matched using the
        schema\'s target namespace.
-   Property maintains attribute names (keys) in the order added. This
    also means that `get_item()` and `get_names()` return ordered
    values. Although, I suspect ordering really needs to be done in the
    marshaller using the order specified in the WSDL/schema.
-   Major refactoring of the `schema.py`. The primary goals is
    preparation for type lookups that are fully qualified by namespace.
    Once completed, the prefixes on attribute values will no longer be
    stripped (purged). Change summary:
    1)  `SchemaProperty` overlay classes created at `__init__()` instead
        of on-demand.
    2)  schema imports performed by new `Import` class instead of by
        `Schema`.
    3)  Schema loads top level properties using a factory.
    4)  All `SchemaProperty` /children/ lists are sorted by `__cmp__()`
        in `SchemaProperty` derived classes. This ensures that types
        with the same name are resolved in the following order
        (`Import`, `Complex`, `Simple`, `Element`).
    5)  All /children/ `SchemaProperty` lists are constructed at
        `__init__()` instead of on-demand.
    6)  The SchemaGroup created and WSDL class updated. This works
        better then having the WSDL aggregate the `<schema/>` nodes
        which severs linkage to the WSDL parent element that have
        namespace prefix mapping.
    7)  `<import/>` element handles properly in that both namespace
        remapping and prefix re-mapping of the imported schema\'s
        `targetNamespace` and associated prefix mapping - is performed.
        E.g. SCHEMA-A has prefix `tns` mapped as `xmlns:tns=http://nsA`
        and has `targetNamespace='http://nsA'`. SCHEMA-B is importing
        schema A and has prefix `abc` mapped as
        `xmlns:abc='http://nsABC'`. SCHEMA-B imports A as
        `<import namespace=http://nsB xxx schemaLocation=http://nsA/schema-a.xsd>`.
        So, since SCHEMA-B will be referencing elements of SCHEMA-A with
        prefix `abc` such as `abc:something`, SCHEMA-A\'s
        `targetNamespace` must be updated as `http://nsABC` and all
        elements with `type=tns:something` must be updated to be
        `type=abc:something` so they can be resolved.
-   Fixes unmarshalling problem where nodes are added to property as
    (text, value). This was introduced when the bindings were
    refactored.
-   Fixed various `Property` print problems.

Notes:

> Thanks to Jesper Noehr of Coniuro for the majority of the rpc/literal
> binding and for lots of collaboration on `#suds`.

**version 0.1.6 (2008-03-06)**

-   Provides proper handling of WSDLs that contain schema sections
    containing XSD schema imports:
    `<import namespace="" schemaLocation=""?>`. The referenced schemas
    are imported when a `schemaLocation` is specified.
-   Raises exceptions for HTTP status codes not already handled.

**version 0.1.5 (2008-02-21)**

-   Provides better logging in the modules get logger by hierarchal
    names.
-   Refactored as needed to truly support other bindings.
-   Add `sax` module which replaces `ElementTree`. This is faster,
    simpler and handles namespaces (prefixes) properly.

**version 0.1.4 (2007-12-21)**

-   Provides for service method parameters to be `None`.
-   Add proper handling of method params that are lists of property
    objects.

**version 0.1.3 (2007-12-19)**

-   Fixes problem where nodes marked as a collection (`maxOccurs` \> 1)
    not creating property objects with `value=[]` when mapped-in with \<
    2 values by the `DocumentReader`. Caused by missing the
    `` bindings.Document.ReplyHint.stripns()` (which uses ``DocumentReader.stripns()`) conversion to`DocumentReader.stripn()`now returning a tuple`(ns,
    tag)\`\` as of 0.1.2.

**version 0.1.2 (2007-12-18)**

-   This release contains an update to property adds:
    -   `Metadata` support.
    -   Overrides: `__getitem__`, `__setitem__`, `__contains__`.
    -   Changes property(reader\|writer) to use the `property.metadata`
        to handle namespaces for XML documents.
    -   Fixes `setup.py` requires.

**version 0.1.1 (2007-12-17)**

-   This release marks the first release in fedora hosted.
