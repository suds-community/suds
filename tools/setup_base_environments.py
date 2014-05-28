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
Sets up base Python development environments used by this project.

These are the Python environments from which multiple virtual environments can
then be spawned as needed.

The environments should have the following Python packages installed:
  * setuptools (for installing pip)
  * pip (for installing everything except itself)
  * pytest (for running the project's test suite)
  * six (Python 2/3 compatibility layer used in the project's test suite)
  * virtualenv (for creating virtual Python environments)
plus certain specific Python versions may require additional backward
compatibility support packages.

"""
#TODO: Python 3.4.0 comes with setuptools & pip preinstalled but they can be
# installed and/or upgraded manually if needed so we choose not to use their
# built-in installations, i.e. the built-in ensurepip module. Consider using
# the built-in ensurepip module if regular setuptools/pip installation fails
# for some reason or has been configured to run locally.
#TODO: logging
#TODO: command-line option support
#TODO: support for additional configuration files, e.g. ones that are developer
# or development environment specific.
#TODO: warn if multiple environments use the same executable
#TODO: make the script importable
#TODO: report when the installed package version is newer than the last tested
# one
#TODO: hold a list of last tested package versions and report a warning if a
# newer one is encountered
#  > # Where no Python package version has been explicitly specified, the
#  > # following 'currently latest available' package release has been
#  > # successfully used:
#  > "last tested package version": {
#  >     "argparse": "1.2.1",
#  >     "backports.ssl_match_hostname": "3.4.0.2",
#  >     "colorama": "0.3.1",
#  >     "pip": "1.5.5",
#  >     "py": "1.4.20",
#  >     "pytest": "2.5.2",
#  >     "setuptools": "3.6",
#  >     "virtualenv": "1.11.5"},
#TODO: automated checking for new used package versions, e.g. using PyPI XRC
# API:
#  > import xmlrpc.client as xrc
#  > client = xrc.ServerProxy("http://pypi.python.org/pypi")
#  > client.package_releases("six")  # just the latest release
#  > client.package_releases("six", True)  # all releases
#TODO: option to break on bad environments
#TODO: verbose option to report bad environment detection output
#TODO: verbose option to report all environment detection output
#TODO: verbose option to report environment details
#TODO: Consider running the environment scanner script from an empty temporary
# folder to avoid importing random same-named modules from the current working
# folder. An alternative would be to play around with sys.path in the scanner
# script, e.g. remove its first element. Also, we might want to clear out any
# globally set Python environment variables such as PYTHONPATH.
#TODO: collect stdout, stderr & log outputs for each easy_install/pip run
#TODO: configurable - avoid downloads if a suitable locally downloaded source
# is available (ez_setup, setuptools, pip)
#TODO: 244 downloads must come before 243 installation
#TODO: support configuring what latest suitable version we want to use if
# available in the following layers:
#  - already installed
#  - local installation cache (can not find out the latest available content,
#    can only download to it or install from it)
#  - pypi
# related configuration options:
#  - allow already installed,
#  - allow locally downloaded,
#  - allow pypi
#TODO: if you want better local-cache support - use devpi:
#  - better caching support and version detection
#  - devpi & pypi usage transparent
#  - we'll need a script for installing & setting up the devpi server
#TODO: parallelization
#TODO: concurrency support - file locking required for:
# installation cache folder:
#   downloading (write)
#   zipping eggs (write)
#   installing from local folder (read)
# Python environment installation area:
#   installing new packages (write)
#   running Python code (read)
#TODO: test whether we can upgrade pip in-place
#TODO: test how we can make pip safe to use when there are multiple pip based
# installations being run at the same time by the same user - specify some
# global folders, like the temp build folder, explicitly
#TODO: Detect most recent packages on PyPI, but do that at most once in a
# single script run, or with a separate script, or use devpi. Currently, if a
# suitable package is found locally, a more suitable one will not be checked
# for on PyPI.
#TODO: Recheck error handling to make sure all failed commands are correctly
# detected. Some might not set a non-0 exit code on error and so their output
# must be used as a success/failure indicator.

import itertools
import os
import os.path
import re
import sys
import tempfile

from suds_devel.configuration import BadConfiguration, Config, configparser
from suds_devel.egg import zip_eggs_in_folder
from suds_devel.environment import BadEnvironment, Environment
from suds_devel.exception import EnvironmentSetupError
from suds_devel.parse_version import parse_version
from suds_devel.requirements import (pytest_requirements, six_requirements,
    virtualenv_requirements)
import suds_devel.utility as utility


# -------------
# Configuration
# -------------

class MyConfig(Config):

    # Section names.
    SECTION__ACTIONS = "setup base environments - actions"
    SECTION__FOLDERS = "setup base environments - folders"
    SECTION__REUSE_PREINSTALLED_SETUPTOOLS =  \
        "setup base environments - reuse pre-installed setuptools"

    def __init__(self, script, project_folder, ini_file):
        """
        Initialize new script configuration.

        External configuration parameters may be specified relative to the
        following folders:
          * script - relative to the current working folder
          * project_folder - relative to the script folder
          * ini_file - relative to the project folder

        """
        super(MyConfig, self).__init__(script, project_folder, ini_file)
        self.__cached_paths = {}
        try:
            self.__read_configuration()
        except configparser.Error:
            raise BadConfiguration(sys.exc_info()[1].message)

    def ez_setup_folder(self):
        return self.__get_cached_path("ez_setup folder")

    def installation_cache_folder(self):
        return self.__get_cached_path("installation cache")

    def pip_download_cache_folder(self):
        return self.__get_cached_path("pip download cache")

    def __get_cached_path(self, option):
        try:
            return self.__cached_paths[option]
        except KeyError:
            x = self.__cached_paths[option] = self.__get_path(option)
            return x

    def __get_path(self, option):
        try:
            folder = self._reader.get(self.SECTION__FOLDERS, option)
        except (configparser.NoOptionError, configparser.NoSectionError):
            return
        except configparser.Error:
            raise BadConfiguration("Error reading configuration option "
                "'%s.%s' - %s" % (self.SECTION__FOLDERS, option,
                sys.exc_info()[1]))
        base_paths = {
            "project-folder": self.project_folder,
            "script-folder": self.script_folder,
            "ini-folder": os.path.dirname(self.ini_file)}
        folder_parts = re.split("[\\/]{2}", folder, maxsplit=1)
        base_path = None
        if len(folder_parts) == 2:
            base_path = base_paths.get(folder_parts[0].lower())
            if base_path is not None:
                folder = folder_parts[1]
        if not folder:
            raise BadConfiguration("Configuration option '%s.%s' invalid. A "
                "valid relative path must not be empty. Use '.' to represent "
                "the base folder." % (section, option))
        if base_path is None:
            base_path = base_paths.get("ini-folder")
        return os.path.normpath(os.path.join(base_path, folder))

    def __read_configuration(self):
        self._read_environment_configuration()

        section = self.SECTION__REUSE_PREINSTALLED_SETUPTOOLS
        self.reuse_old_setuptools = self._get_bool(section, "old")
        self.reuse_best_setuptools = self._get_bool(section, "best")
        self.reuse_future_setuptools = self._get_bool(section, "future")

        section = self.SECTION__ACTIONS
        self.report_environment_configuration = (
            self._get_bool(section, "report environment configuration"))
        self.report_raw_environment_scan_results = (
            self._get_bool(section, "report raw environment scan results"))
        self.setup_setuptools = (
            self._get_tribool(section, "setup setuptools"))
        self.download_installations = (
            self._get_tribool(section, "download installations"))
        self.install_environments = (
            self._get_tribool(section, "install environments"))


def _prepare_configuration():
    # We know we are a regular stand-alone script file and not an imported
    # module (either frozen, imported from disk, zip-file, external database or
    # any other source). That means we can safely assume we have the __file__
    # attribute available.
    global config
    config = MyConfig(__file__, "..", "setup.cfg")


# --------------------
# Environment scanning
# --------------------

def report_environment_configuration(env):
    if not (env and env.initial_scan_completed):
        return
    print("  ctypes version: %s" % (env.ctypes_version,))
    print("  pip version: %s" % (env.pip_version,))
    print("  pytest version: %s" % (env.pytest_version,))
    print("  python version: %s" % (env.python_version,))
    print("  setuptools version: %s" % (env.setuptools_version,))
    if env.setuptools_zipped_egg is not None:
        print("  setuptools zipped egg: %s" % (env.setuptools_zipped_egg,))
    print("  virtualenv version: %s" % (env.virtualenv_version,))


def report_raw_environment_scan_results(out, err, exit_code):
    if out is None and err is None and exit_code is None:
        return
    print("-----------------------------------")
    print("--- RAW SCAN RESULTS --------------")
    print("-----------------------------------")
    if exit_code is not None:
        print("*** EXIT CODE: %d" % (exit_code,))
    for name, value in (("STDOUT", out), ("STDERR", err)):
        if value:
            print("*** %s:" % (name,))
            sys.stdout.write(value)
            if value[-1] != "\n":
                sys.stdout.write("\n")
    print("-----------------------------------")


class ScanProgressReporter:
    """
    Reports scanning progress to the user.

    Takes care of all the gory progress output formatting details so they do
    not pollute the actual scanning logic implementation.

    A ScanProgressReporter's output formatting logic assumes that the reporter
    is the one with full output control between calls to a its report_start() &
    report_finish() methods. Therefore, user code must not do any custom output
    during that time or it risks messing up the reporter's output formatting.

    """

    def __init__(self, environments):
        self.__max_name_length = max(len(x.name()) for x in environments)
        self.__count = len(environments)
        self.__count_width = len(str(self.__count))
        self.__current = 0
        self.__reporting = False
        print("Scanning Python environments...")

    def report_start(self, name):
        assert len(name) <= self.__max_name_length
        assert self.__current <= self.__count
        assert not self.__reporting
        self.__reporting = True
        self.__current += 1
        name_padding = " " * (self.__max_name_length - len(name))
        sys.stdout.write("[%*d/%d] Scanning '%s'%s - " % (self.__count_width,
            self.__current, self.__count, name, name_padding))
        sys.stdout.flush()

    def report_finish(self, report):
        assert self.__reporting
        self.__reporting = False
        print(report)


class ScannedEnvironmentTracker:
    """Helps track scanned Python environments and report duplicates."""

    def __init__(self):
        self.__names = set()
        self.__last_name = None
        self.__environments = []

    def environments(self):
        return self.__environments

    def track_environment(self, env):
        assert env not in self.__environments
        assert env.name() == self.__last_name
        self.__environments.append(env)

    def track_name(self, name):
        if name in self.__names:
            raise BadConfiguration("Python environment '%s' configured "
                "multiple times." % (name,))
        self.__names.add(name)
        self.__last_name = name


def scan_python_environment(env, progress_reporter, environment_tracker):
    environment_tracker.track_name(env.name())
    # N.B. No custom output allowed between calls to our progress_reporter's
    # report_start() & report_finish() methods or we risk messing up its output
    # formatting.
    progress_reporter.report_start(env.name())
    try:
        try:
            out, err, exit_code = env.run_initial_scan()
        except:
            progress_reporter.report_finish("----- %s" % (_exc_str(),))
            raise
    except BadEnvironment:
        out, err, exit_code = sys.exc_info()[1].raw_scan_results()
    else:
        progress_reporter.report_finish(env.description())
        environment_tracker.track_environment(env)
    if config.report_raw_environment_scan_results:
        report_raw_environment_scan_results(out, err, exit_code)
    if config.report_environment_configuration:
        report_environment_configuration(env)


def scan_python_environments():
    environments = config.python_environments
    if not environments:
        raise BadConfiguration("No Python environments configured.")
    progress_reporter = ScanProgressReporter(environments)
    environment_tracker = ScannedEnvironmentTracker()
    for env in environments:
        scan_python_environment(env, progress_reporter, environment_tracker)
    return environment_tracker.environments()


# ------------------------------------------
# Generic functionality local to this module
# ------------------------------------------

def _create_installation_cache_folder_if_needed():
    assert config.installation_cache_folder() is not None
    if not os.path.isdir(config.installation_cache_folder()):
        print("Creating installation cache folder...")
        # os.path.abspath() to avoid ".." entries in the path that would
        # otherwise confuse os.makedirs().
        os.makedirs(os.path.abspath(config.installation_cache_folder()))


def _exc_str():
    exc_type, exc = sys.exc_info()[:2]
    type_desc = []
    if exc_type.__module__ and exc_type.__module__ != "__main__":
        type_desc.append(exc_type.__module__)
    type_desc.append(exc_type.__name__)
    desc = ".".join(type_desc), str(exc)
    return ": ".join(x for x in desc if x)


def _report_configuration():
    folder = config.installation_cache_folder()
    if folder is not None:
        print("Installation cache folder: '%s'" % (folder,))
    folder = config.pip_download_cache_folder()
    if folder is not None:
        print("PIP download cache folder: '%s'" % (folder,))


def _report_startup_information():
    print("Running in folder: '%s'" % (os.getcwd(),))


# ----------------------------------
# Processing setuptools installation
# ----------------------------------

def process_setuptools(env, actions):
    if "setup setuptools" not in actions:
        return
    installer = _ez_setup_script(env)
    if _reuse_pre_installed_setuptools(env, installer):
        return
    _avoid_setuptools_zipped_egg_upgrade_issue(env, installer)
    try:
        # 'ez_setup' script will download its setuptools installation to the
        # 'current working folder'. If we are using an installation cache
        # folder, we run the script from there to get the downloaded setuptools
        # installation stored together with all of the other used
        # installations. If we are not, then just have it downloaded to the
        # current folder.
        if config.installation_cache_folder() is not None:
            _create_installation_cache_folder_if_needed()
        installer.execute(cwd=config.installation_cache_folder())
    except (KeyboardInterrupt, SystemExit):
        raise
    except Exception:
        raise EnvironmentSetupError("setuptools installation failed - %s" % (
            _exc_str(),))


class _ez_setup_script:
    """setuptools project's ez_setup installer script."""

    def __init__(self, env):
        self.__env = env
        if not config.ez_setup_folder():
            self.__error("ez_setup folder not configured")
        self.__ez_setup_folder = config.ez_setup_folder()
        self.__cached_script_path = None
        self.__cached_setuptools_version = None
        if not os.path.isfile(self.script_path()):
            self.__error("installation script '%s' not found" % (
                self.script_path(),))

    def execute(self, cwd=None):
        script_path = self.script_path()
        kwargs = {}
        if cwd:
            kwargs["cwd"] = cwd
            script_path = os.path.abspath(script_path)
        self.__env.execute([script_path], **kwargs)

    def script_path(self):
        if self.__cached_script_path is None:
            self.__cached_script_path = self.__script_path()
        return self.__cached_script_path

    def setuptools_version(self):
        if self.__cached_setuptools_version is None:
            self.__cached_setuptools_version = self.__setuptools_version()
        return self.__cached_setuptools_version

    def __error(self, msg):
        raise EnvironmentSetupError("Can not install setuptools - %s." % (
            msg,))

    def __script_path(self):
        import suds_devel.ez_setup_versioned as ez
        script_name = ez.script_name(self.__env.sys_version_info)
        return os.path.join(self.__ez_setup_folder, script_name)

    def __setuptools_version(self):
        """Read setuptools version from the underlying ez_setup script."""
        # Read the script directly as a file instead of importing it as a
        # Python module and reading the value from the loaded module's global
        # DEFAULT_VERSION variable. Not all ez_setup scripts are compatible
        # with all Python environments and so importing them would require
        # doing so using a separate process run in the target Python
        # environment instead of the current one.
        f = open(self.script_path(), "r")
        try:
            matcher = re.compile(r'\s*DEFAULT_VERSION\s*=\s*"([^"]*)"\s*$')
            for i, line in enumerate(f):
                if i > 50:
                    break
                match = matcher.match(line)
                if match:
                    return match.group(1)
        finally:
            f.close()
        self.__error("error parsing setuptools installation script '%s'" % (
            self.script_path(),))


def _avoid_setuptools_zipped_egg_upgrade_issue(env, ez_setup):
    """
    Avoid the setuptools self-upgrade issue.

    setuptools versions prior to version 3.5.2 have a bug that can cause their
    upgrade installations to fail when installing a new zipped egg distribution
    over an existing zipped egg setuptools distribution with the same name.

    The following Python versions are not affected by this issue:
      Python 2.4 - use setuptools 1.4.2 - installs itself as a non-zipped egg
      Python 2.6+ - use setuptools versions not affected by this issue
    That just leaves Python versions 2.5.x to worry about.

    This problem occurs because of an internal stale cache issue causing the
    upgrade to read data from the new zip archive at a location calculated
    based on the original zip archive's content, effectively causing such read
    operations to either succeed (if read content had not changed its
    location), fail with a 'bad local header' exception or even fail silently
    and return incorrect data.

    To avoid the issue, we explicitly uninstall the previously installed
    setuptools distribution before installing its new version.

    """
    if env.sys_version_info[:2] != (2, 5):
        return  # only Python 2.5.x affected by this
    if not env.setuptools_zipped_egg:
        return  # setuptools not pre-installed as a zipped egg
    pv_new = parse_version(ez_setup.setuptools_version())
    if pv_new != parse_version(env.setuptools_version):
        return  # issue avoided since zipped egg archive names will not match
    fixed_version = utility.lowest_version_string_with_prefix("3.5.2")
    if pv_new >= parse_version(fixed_version):
        return  # issue fixed in setuptools
    # We could check for pip and use it for a cleaner setuptools uninstall if
    # available, but YAGNI since only Python 2.5.x environments are affected by
    # the zipped egg upgrade issue.
    os.remove(env.setuptools_zipped_egg)


def _reuse_pre_installed_setuptools(env, installer):
    """
    Return whether a pre-installed setuptools distribution should be reused.

    """
    if not env.setuptools_version:
        return  # no prior setuptools ==> no reuse
    reuse_old = config.reuse_old_setuptools
    reuse_best = config.reuse_best_setuptools
    reuse_future = config.reuse_future_setuptools
    reuse_comment = None
    if reuse_old or reuse_best or reuse_future:
        pv_old = parse_version(env.setuptools_version)
        pv_new = parse_version(installer.setuptools_version())
        if pv_old < pv_new:
            if reuse_old:
                reuse_comment = "%s+ recommended" % (
                    installer.setuptools_version(),)
        elif pv_old > pv_new:
            if reuse_future:
                reuse_comment = "%s+ required" % (
                    installer.setuptools_version(),)
        elif reuse_best:
            reuse_comment = ""
    if reuse_comment is None:
        return  # reuse not allowed by configuration
    if reuse_comment:
        reuse_comment = " (%s)" % (reuse_comment,)
    print("Reusing pre-installed setuptools %s distribution%s." % (
        env.setuptools_version, reuse_comment))
    return True  # reusing pre-installed setuptools


# ---------------------------
# Processing pip installation
# ---------------------------

def calculate_pip_requirements(env_version_info):
    # pip releases supported on older Python versions:
    #   * Python 2.4.x - pip 1.1.
    #   * Python 2.5.x - pip 1.3.1.
    pip_version = None
    if env_version_info < (2, 5):
        pip_version = "1.1"
    elif env_version_info < (2, 6):
        pip_version = "1.3.1"
    requirement_spec = utility.requirement_spec
    requirements = [requirement_spec("pip", pip_version)]
    # Although pip claims to be compatible with Python 3.0 & 3.1 it does not
    # seem to work correctly from within such clean Python environments.
    #   * Tested using pip 1.5.4 & Python 3.1.3.
    #   * pip can be installed using Python 3.1.3 ('py313 -m easy_install pip')
    #     but attempting to use it or even just import its pip Python module
    #     fails.
    #   * The problem is caused by a bug in pip's backward compatibility
    #     support implementation, but can be worked around by installing the
    #     backports.ssl_match_hostname package from PyPI.
    if (3,) <= env_version_info < (3, 2):
        requirements.append(requirement_spec("backports.ssl_match_hostname"))
    return requirements


def download_pip(env, requirements):
    """Download pip and its requirements using setuptools."""
    if config.installation_cache_folder() is None:
        raise EnvironmentSetupError("Local installation cache folder not "
            "defined but required for downloading a pip installation.")
    # Installation cache folder needs to be explicitly created for setuptools
    # to be able to copy its downloaded installation files into it. Seen using
    # Python 2.4.4 & setuptools 1.4.
    _create_installation_cache_folder_if_needed()
    try:
        env.execute(["-m", "easy_install", "--zip-ok", "--multi-version",
            "--always-copy", "--exclude-scripts", "--install-dir",
            config.installation_cache_folder()] + requirements)
        zip_eggs_in_folder(config.installation_cache_folder())
    except (KeyboardInterrupt, SystemExit):
        raise
    except Exception:
        raise EnvironmentSetupError("pip download failed.")


def setuptools_install_options(local_storage_folder):
    """
    Return options to make setuptools use installations from the given folder.

    No other installation source is allowed.

    """
    if local_storage_folder is None:
        return []
    # setuptools expects its find-links parameter to contain a list of link
    # sources (either local paths, file: URLs pointing to folders or URLs
    # pointing to a file containing HTML links) separated by spaces. That means
    # that, when specifying such items, whether local paths or URLs, they must
    # not contain spaces. The problem can be worked around by using a local
    # file URL, since URLs can contain space characters encoded as '%20' (for
    # more detailed information see below).
    #
    # Any URL referencing a folder needs to be specified with a trailing '/'
    # character in order for setuptools to correctly recognize it as a folder.
    #
    # All this has been tested using Python 2.4.3/2.4.4 & setuptools 1.4/1.4.2
    # as well as Python 3.4 & setuptools 3.3.
    #
    # Supporting paths with spaces - method 1:
    # ----------------------------------------
    # One way would be to prepare a link file and pass an URL referring to that
    # link file. The link file needs to contain a list of HTML link tags
    # (<a href="..."/>), one for every item stored inside the local storage
    # folder. If a link file references a folder whose name matches the desired
    # requirement name, it will be searched recursively (as described in method
    # 2 below).
    #
    # Note that in order for setuptools to recognize a local link file URL
    # correctly, the file needs to be named with the '.html' extension. That
    # will cause the underlying urllib2.open() operation to return the link
    # file's content type as 'text/html' which is required for setuptools to
    # recognize a valid link file.
    #
    # Supporting paths with spaces - method 2:
    # ----------------------------------------
    # Another possible way is to use an URL referring to the local storage
    # folder directly. This will cause setuptools to prepare and use a link
    # file internally - with its content read from a 'index.html' file located
    # in the given local storage folder, if it exists, or constructed so it
    # contains HTML links to all top-level local storage folder items, as
    # described for method 1 above.
    if " " in local_storage_folder:
        find_links_param = utility.path_to_URL(local_storage_folder)
        if find_links_param[-1] != "/":
            find_links_param += "/"
    else:
        find_links_param = local_storage_folder
    return ["-f", find_links_param, "--allow-hosts=None"]


def install_pip(env, requirements):
    """Install pip and its requirements using setuptools."""
    try:
        installation_source_folder = config.installation_cache_folder()
        options = setuptools_install_options(installation_source_folder)
        if installation_source_folder is not None:
            zip_eggs_in_folder(installation_source_folder)
        env.execute(["-m", "easy_install"] + options + requirements)
    except (KeyboardInterrupt, SystemExit):
        raise
    except Exception:
        raise EnvironmentSetupError("pip installation failed.")


def process_pip(env, actions):
    download = "download pip installation" in actions
    install = "run pip installation" in actions
    if not download and not install:
        return
    requirements = calculate_pip_requirements(env.sys_version_info)
    if download:
        download_pip(env, requirements)
    if install:
        install_pip(env, requirements)


# ----------------------------------
# Processing pip based installations
# ----------------------------------

def pip_invocation_arguments(env_version_info):
    """
    Returns Python arguments for invoking pip with a specific Python version.

    Running pip based installations on Python prior to 2.7.
      * pip based installations may be run using:
          python -c "import pip;pip.main()" install <package-name-to-install>
        in addition to the regular command:
          python -m pip install <package-name-to-install>
      * The '-m' option can not be used with certain Python versions prior to
        Python 2.7.
          * Whether this is so also depends on the specific pip version used.
          * Seems to not work with Python 2.4 and pip 1.1.
          * Seems to work fine with Python 2.5.4 and pip 1.3.1.
          * Seems to not work with Python 2.6.6 and pip 1.5.4.

    """
    if (env_version_info < (2, 5)) or ((2, 6) <= env_version_info < (2, 7)):
        return ["-c", "import pip;pip.main()"]
    return ["-m", "pip"]


def pip_requirements_file(requirements):
    janitor = None
    try:
        os_handle, file_path = tempfile.mkstemp(suffix=".pip-requirements",
            text=True)
        requirements_file = os.fdopen(os_handle, "w")
        try:
            janitor = utility.FileJanitor(file_path)
            for line in requirements:
                requirements_file.write(line)
                requirements_file.write("\n")
        finally:
            requirements_file.close()
        return file_path, janitor
    except:
        if janitor:
            janitor.clean()
        raise


def prepare_pip_requirements_file_if_needed(requirements):
    """
    Make requirements be passed to pip via a requirements file if needed.

    We must be careful about how we pass shell operator characters (e.g. '<',
    '>', '|' or '^') included in our command-line arguments or they might cause
    problems if run through an intermediate shell interpreter. If our pip
    requirement specifications contain such characters, we pass them using a
    separate requirements file.

    This problem has been encountered on Windows 7 SP1 x64 using Python 2.4.3,
    2.4.4 & 2.5.4.

    """
    if utility.any_contains_any(requirements, "<>|()&^"):
        file_path, janitor = pip_requirements_file(requirements)
        requirements[:] = ["-r", file_path]
        return janitor


def prepare_pip_requirements(env):
    requirements = list(itertools.chain(
        pytest_requirements(env.sys_version_info, env.ctypes_version),
        six_requirements(env.sys_version_info),
        virtualenv_requirements(env.sys_version_info)))
    janitor = prepare_pip_requirements_file_if_needed(requirements)
    return requirements, janitor


def pip_download_cache_options(download_cache_folder):
    if download_cache_folder is None:
        return []
    return ["--download-cache=" + download_cache_folder]


def download_pip_based_installations(env, pip_invocation, requirements,
        download_cache_folder):
    """Download requirements for pip based installation."""
    if config.installation_cache_folder() is None:
        raise EnvironmentSetupError("Local installation cache folder not "
            "defined but required for downloading pip based installations.")
    # Installation cache folder needs to be explicitly created for pip to be
    # able to copy its downloaded installation files into it. The same does not
    # hold for pip's download cache folder which gets created by pip on-demand.
    # Seen using Python 3.4.0 & pip 1.5.4.
    _create_installation_cache_folder_if_needed()
    try:
        pip_options = ["install", "-d", config.installation_cache_folder(),
            "--exists-action=i"]
        pip_options.extend(pip_download_cache_options(download_cache_folder))
        # Running pip based installations on Python 2.5.
        #   * Python 2.5 does not come with SSL support enabled by default and
        #     so pip can not use SSL certified downloads from PyPI.
        #   * To work around this either install the
        #     https://pypi.python.org/pypi/ssl package or run pip using the
        #     '--insecure' command-line options.
        #       * Installing the ssl package seems ridden with problems on
        #         Python 2.5 so this workaround has not been tested.
        if (2, 5) <= env.sys_version_info < (2, 6):
            # There are some potential cases where we do not need to use
            # "--insecure", e.g. if the target Python environment already has
            # the 'ssl' module installed. However, detecting whether this is so
            # does not seem to be worth the effort. The only way to detect
            # whether secure download is supported would be to scan the target
            # environment for this information, e.g. setuptools has this
            # information in its pip.backwardcompat.ssl variable - if it is
            # None, the necessary SSL support is not available. But then we
            # would have to be careful:
            #  - not to run the scan if we already know this information from
            #    some previous scan
            #  - to track all actions that could have invalidated our previous
            #    scan results, etc.
            # It just does not seem to be worth the hassle so for now - YAGNI.
            pip_options.append("--insecure")
        env.execute(pip_invocation + pip_options + requirements)
    except (KeyboardInterrupt, SystemExit):
        raise
    except Exception:
        raise EnvironmentSetupError("pip based download failed.")


def run_pip_based_installations(env, pip_invocation, requirements,
        download_cache_folder):
    # 'pip' download caching system usage notes:
    # 1. When not installing from our own local installation storage folder, we
    #    can still use pip's internal download caching system.
    # 2. We must not enable pip's internal download caching system when
    #    installing from our own local installation storage folder. In that
    #    case, pip attempts to populate its cache from our local installation
    #    folder, but that logic fails when our folder contains a wheel (.whl)
    #    distribution. More precisely, it fails attempting to store the wheel
    #    distribution file's content type information. Tested using Python
    #    3.4.0 & pip 1.5.4.
    try:
        pip_options = ["install"]
        if config.installation_cache_folder() is None:
            pip_options.extend(pip_download_cache_options(
                download_cache_folder))
        else:
            # pip allows us to identify a local folder containing predownloaded
            # installation packages using its '-f' command-line option taking
            # an URL parameter. However, it does not require the URL to be
            # URL-quoted and it does not even seem to recognize URLs containing
            # %xx escaped characters. Tested using an installation cache folder
            # path containing spaces with Python 3.4.0 & pip 1.5.4.
            installation_cache_folder_URL = utility.path_to_URL(
                config.installation_cache_folder(), escape=False)
            pip_options.extend(["-f", installation_cache_folder_URL,
                "--no-index"])
        env.execute(pip_invocation + pip_options + requirements)
    except (KeyboardInterrupt, SystemExit):
        raise
    except Exception:
        raise EnvironmentSetupError("pip based installation failed.")


def post_pip_based_installation_fixups(env):
    """Apply simple post-installation fixes for pip installed packages."""
    if env.sys_version_info[:2] == (3, 1):
        from suds_devel.patch_pytest_on_python_31 import patch
        patch(env)


def process_pip_based_installations(env, actions, download_cache_folder):
    download = "download pip based installations" in actions
    install = "run pip based installations" in actions
    if not download and not install:
        return
    pip_invocation = pip_invocation_arguments(env.sys_version_info)
    janitor = None
    try:
        requirements, janitor = prepare_pip_requirements(env)
        if download:
            download_pip_based_installations(env, pip_invocation, requirements,
                download_cache_folder)
        if install:
            run_pip_based_installations(env, pip_invocation, requirements,
                download_cache_folder)
            post_pip_based_installation_fixups(env)
    finally:
        if janitor:
            janitor.clean()


# ------------------------------
# Processing Python environments
# ------------------------------

def enabled_actions_for_env(env):
    """Returns actions to perform when processing the given environment."""
    def enabled(config_value, required):
        if config_value is Config.TriBool.No:
            return False
        if config_value is Config.TriBool.Yes:
            return True
        assert config_value is Config.TriBool.IfNeeded
        return bool(required)

    # Some old Python versions do not support HTTPS downloads and therefore can
    # not download installation packages from PyPI. To run setuptools or pip
    # based installations on such Python versions, all the required
    # installation packages need to be downloaded locally first using a
    # compatible Python version (e.g. Python 2.4.4 for Python 2.4.3) and then
    # installed locally.
    download_supported = not ((2, 4, 3) <= env.sys_version_info < (2, 4, 4))

    local_install = config.installation_cache_folder() is not None

    actions = set()

    pip_required = False
    run_pip_based_installations = enabled(config.install_environments, True)
    if run_pip_based_installations:
        actions.add("run pip based installations")
        pip_required = True
    if download_supported and enabled(config.download_installations,
            local_install and run_pip_based_installations):
        actions.add("download pip based installations")
        pip_required = True

    setuptools_required = False
    run_pip_installation = enabled(config.install_environments, pip_required)
    if run_pip_installation:
        actions.add("run pip installation")
        setuptools_required = True
    if download_supported and enabled(config.download_installations,
            local_install and run_pip_installation):
        actions.add("download pip installation")
        setuptools_required = True

    if enabled(config.setup_setuptools, setuptools_required):
        actions.add("setup setuptools")

    return actions


def print_environment_processing_title(env):
    title_length = 73
    print("-" * title_length)
    title = "--- %s - Python %s " % (env.name(), env.python_version)
    title += "-" * max(0, title_length - len(title))
    print(title)
    print("-" * title_length)


def process_Python_environment(env):
    actions = enabled_actions_for_env(env)
    if not actions:
        return
    print_environment_processing_title(env)
    process_setuptools(env, actions)
    process_pip(env, actions)
    process_pip_based_installations(env, actions,
        config.pip_download_cache_folder())


def process_python_environments(python_environments):
    for env in python_environments:
        try:
            process_Python_environment(env)
        except EnvironmentSetupError:
            utility.report_error(sys.exc_info()[1])


def main():
    try:
        _report_startup_information()
        _prepare_configuration()
        _report_configuration()
        python_environments = scan_python_environments()
    except BadConfiguration:
        utility.report_error(sys.exc_info()[1])
        return -2
    process_python_environments(python_environments)
    return 0


if __name__ == "__main__":
    sys.exit(main())
