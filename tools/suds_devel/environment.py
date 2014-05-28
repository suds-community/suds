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
Class representing a single Python environment.

Includes support for:
  - fetching information about a specific Python environment
  - executing a command in a specific Python environment

"""

import sys
have_subprocess_devnull = sys.version_info >= (3, 3)
if not have_subprocess_devnull:
    import os
import subprocess


class BadEnvironment(Exception):
    """
    Problem occurred while scanning a Python environment.

    The problem may be either a technical one in the scanning process itself,
    or it may be a problem with something detected about the Python environment
    in question, e.g. it might be using an incompatible Python version.

    Specifying the environment scan result information when constructing this
    exception is optional and may be added to an exception later on using the
    set_raw_scan_results() method.

    """

    def __init__(self, message, out=None, err=None, exit_code=None):
        Exception.__init__(self, message)
        self.message = message
        self.out = out
        self.err = err
        self.exit_code = exit_code

    def raw_scan_results(self):
        return self.out, self.err, self.exit_code

    def set_raw_scan_results(self, out, err, exit_code):
        assert self.out is None
        assert self.err is None
        assert self.exit_code is None
        self.out = out
        self.err = err
        self.exit_code = exit_code


class _UndefinedParameter:
    """Internal class used to indicate undefined parameter values."""
    pass


class Environment:
    """
    Represents a single Python environment.

    Allows running commands using the environment's Python interpreter.
    Allows running an initial Python environment scan to collect information
    about it.

    Note that most of the information about the environment will not be
    available until the initial environment scan is run.

    """

    def __init__(self, name, command):
        self.__name = name
        self.__command = command
        self.initial_scan_completed = False

    def command(self):
        return self.__command

    def description(self):
        return "%s on %s" % (self.sys_version, self.sys_platform)

    def execute(self, args=[], input=None, capture_output=False,
            cwd=_UndefinedParameter):
        stdin = subprocess.PIPE
        close_stdin = False
        if input is None:
            if have_subprocess_devnull:
                stdin = subprocess.DEVNULL
            else:
                stdin = open(os.devnull, "r")
                close_stdin = True
        try:
            kwargs = {}
            kwargs["stdin"] = stdin
            if capture_output:
                kwargs["stdout"] = subprocess.PIPE
                kwargs["stderr"] = subprocess.PIPE
            if cwd is not _UndefinedParameter:
                kwargs["cwd"] = cwd
            kwargs["universal_newlines"] = True
            popen = subprocess.Popen([self.command()] + args, **kwargs)
            out, err = popen.communicate(input)
        finally:
            if close_stdin:
                stdin.close()
        return out, err, popen.returncode

    def name(self):
        return self.__name

    def run_initial_scan(self):
        self.initial_scan_completed = False
        scanner = self.__initial_scanner()
        try:
            scan_results = scanner.scan(self)
            self.__collect_scanned_values(scan_results)
            self.__parse_scanned_version_info()
            self.initial_scan_completed = True
            self.__check_python_version()
        except BadEnvironment:
            sys.exc_info()[1].set_raw_scan_results(*scanner.raw_scan_results())
            raise
        return scanner.raw_scan_results()

    def __check_python_version(self):
        if self.sys_version_info < (2, 4):
            raise BadEnvironment("Unsupported Python version (%s, %s-bit)"
                % (self.python_version, self.pointer_size_in_bits))

    def __collect_scanned_values(self, values):
        v = values
        # System.
        self.platform_architecture = v["platform.architecture"]
        self.pointer_size_in_bits = v["pointer size in bits"]
        self.sys_path = v["sys.path"]
        self.sys_version = v["sys.version"]
        self.sys_version_info_formatted = v["sys.version_info (formatted)"]
        self.sys_version_info_raw = v["sys.version_info (raw)"]
        self.sys_platform = v["sys.platform"]
        self.sys_executable = v["sys.executable"]
        # Packages.
        self.ctypes_version = v["ctypes version"]
        self.pip_version = v["pip version"]
        self.pytest_version = v["pytest version"]
        self.setuptools_version = v["setuptools version"]
        self.virtualenv_version = v["virtualenv version"]
        # Extra package info.
        self.setuptools_zipped_egg = v["setuptools zipped egg"]

    def __construct_python_version(self):
        """
        Construct a setuptools compatible Python version string.

        Constructed based on the environment's reported sys.version_info.

        """
        major, minor, micro, release_level, serial = self.sys_version_info
        assert release_level in ("alfa", "beta", "candidate", "final")
        assert release_level != "final" or serial == 0
        parts = [str(major), ".", str(minor), ".", str(micro)]
        if release_level != "final":
            parts.append(release_level[0])
            parts.append(str(serial))
        self.python_version = "".join(parts)

    @staticmethod
    def __initial_scanner():
        s = EnvironmentScanner()

        s.add_import("os.path")
        s.add_import("platform")
        s.add_import("struct")
        s.add_import("sys")

        s.add_function("""\
def version_info_string():
    major, minor, micro, release_level, serial = sys.version_info
    if not (isinstance(major, int) and isinstance(minor, int) and
        isinstance(micro, int) and isinstance(release_level, str) and
        isinstance(serial, int)) or "," in release_level:
        return ""
    # At least Python versions 2.7.6 & 3.1.3 require an explicit tuple() cast.
    return "%d,%d,%d,%s,%d" % tuple(sys.version_info)
""")
        s.add_function("""\
def setuptools_zipped_egg():
    try:
        from pkg_resources import (
            DistributionNotFound, EGG_DIST, get_distribution)
    except ImportError:
        return Skip
    try:
        d = get_distribution("setuptools")
    except DistributionNotFound:
        return Skip
    if d.precedence != EGG_DIST or not os.path.isfile(d.location):
        return Skip  # file = zipped egg; folder = unzipped egg
    return d.location
""")

        s.add_field("platform.architecture", "platform.architecture()")
        s.add_field("pointer size in bits", '8 * struct.calcsize("P")')
        s.add_field("sys.executable")
        s.add_field("sys.path")
        s.add_field("sys.platform")
        s.add_field("sys.version")
        s.add_field("sys.version_info (formatted)", "version_info_string()")
        s.add_field("sys.version_info (raw)", "sys.version_info")

        s.add_package_version_field("ctypes", default=None)
        s.add_package_version_field("pip", default=None)
        s.add_package_version_field("pytest", default=None)
        s.add_package_version_field("setuptools", default=None)
        s.add_package_version_field("virtualenv", default=None)

        s.add_field("setuptools zipped egg", "setuptools_zipped_egg()", None)
        return s

    def __parse_scanned_version_info(self):
        """Parses the environment's formatted version info string."""
        string = self.sys_version_info_formatted
        try:
            major, minor, micro, release_level, serial = string.split(",")
            if (release_level in ("alfa", "beta", "candidate", "final") and
                    (release_level != "final" or serial == "0") and
                    major.isdigit() and  # --- --- --- --- --- --- --- --- ---
                    minor.isdigit() and  # Explicit isdigit() checks to detect
                    micro.isdigit() and  # leading/trailing whitespace.
                    serial.isdigit()):   # --- --- --- --- --- --- --- --- ---
                self.sys_version_info = (int(major), int(minor), int(micro),
                    release_level, int(serial))
                self.__construct_python_version()
                return
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception:
            pass
        raise BadEnvironment("Unsupported Python version (%s)" % (string,))


class EnvironmentScanner:
    """
    Allows scanning a given Python environment for specific information.

    Runs a scanner script in the given Python environment, crafted based on the
    information we wish to find out about the environment, and then collects
    and returns the requested information.

    """

    # Explicitly specified scan output start & finish markers allow us to
    # safely ignore extra output that might be added by the environment's
    # Python interpreter startup. This can be useful, for instance, if you want
    # to debug this script by having the Python interpreter startup script
    # output the exact calls made to the Python interpreter.
    SCAN_START_MARKER = "--- SCAN START ---"
    SCAN_FINISH_MARKER = "--- SCAN FINISH ---"

    __scanner_script__startup = """\
class Skip:
    pass

def print_field(id, value):
    if value is not Skip:
        print("%s: %s" % (id, value))
"""

    # If available, setuptools can give us more detailed version information
    # read from the package's meta-data than simply reading it from its
    # __version__ attribute. For example, in case of setuptools it can tell us
    # that we are dealing with version '3.7dev' while __version__ would tell us
    # just '3.7'. Also, some older packages, such as pip 1.1, may not have a
    # __version__ attribute set in their main module at all.
    __scanner_script__package_version_scanner = """\
def package_version(package_name):
    try:
        package = __import__(package_name, {}, {}, ("__version__",))
    except (KeyboardInterrupt, SystemExit):
        raise
    except Exception:
        return Skip  # No package - no version.
    try:
        version = package.__version__
    except AttributeError:
        version = "unknown"
    try:
        from pkg_resources import (DistributionNotFound, get_distribution)
    except ImportError:
        return version
    try:
        return get_distribution(package_name).version
    except DistributionNotFound:
        return version
"""

    def __init__(self):
        self.__out = None
        self.__err = None
        self.__exit_code = None
        self.__scan_for_version_info = False
        self.__extra_script_functions = []
        self.__extra_script_imports = []
        self.__fields = []

    def add_field(self, id, getter=None, default=_UndefinedParameter):
        if getter is None:
            getter = id
        self.__add_field(id, "print_field(%r, %s)" % (id, getter), default)

    def add_function(self, code):
        self.__extra_script_functions.append(code)

    def add_import(self, module_name):
        self.__extra_script_imports.append(module_name)

    def add_package_version_field(self, package_name, default=_UndefinedParameter):
        self.__scan_for_version_info = True
        field_id = "%s version" % (package_name,)
        field_getter = "print_field(%r, package_version(%r))" % (
            field_id, package_name)
        self.__add_field(field_id, field_getter, default)

    def raw_scan_results(self):
        return self.__out, self.__err, self.__exit_code

    def scan(self, environment):
        self.__scan(environment)
        raw_data = self.__parse_raw_scanner_output()
        return self.__map_raw_data_to_expected_fields(raw_data)

    def __add_field(self, id, getter, default):
        assert id not in [x[0] for x in self.__fields]
        self.__fields.append((id, getter, default))

    @staticmethod
    def __extract_value(raw_data, id, default):
        if default is not _UndefinedParameter:
            return raw_data.pop(id, default)
        try:
            return raw_data.pop(id)
        except KeyError:
            raise BadEnvironment("Missing scan output record (%s)" % (
                sys.exc_info()[1],))

    def __map_raw_data_to_expected_fields(self, raw_data):
        scanner_results = {}
        for id, getter, default in self.__fields:
            assert id not in scanner_results
            scanner_results[id] = self.__extract_value(raw_data, id, default)
        if raw_data:
            raise BadEnvironment("Extra scan output records (%s)" % (
                ",".join(raw_data.keys()),))
        return scanner_results

    def __parse_raw_scanner_output(self):
        assert self.__scanned()
        result = {}
        in_scanner_output = False
        for line in self.__out.split("\n"):
            if not in_scanner_output:
                in_scanner_output = line.startswith(self.SCAN_START_MARKER)
                continue
            if line.startswith(self.SCAN_FINISH_MARKER):
                return result
            split_result = line.split(": ", 1)
            if len(split_result) != 2:
                raise BadEnvironment("Error parsing scan output record")
            key, value = split_result
            if key in result:
                raise BadEnvironment("Duplicate scan output record (%s)" %
                    (key,))
            result[key] = value
        if not in_scanner_output:
            raise BadEnvironment("No valid scan output detected")
        raise BadEnvironment("Scan output truncated")

    def __scan(self, environment):
        assert not self.__scanned()
        try:
            self.__out, self.__err, self.__exit_code = environment.execute(
                input=self.__scanner_script(), capture_output=True)
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception:
            e_type, e = sys.exc_info()[:2]
            try:
                raise BadEnvironment("%s: %s" % (e_type.__name__, e))
            finally:
                del e  # explicitly break circular reference chain in Python 3
        if self.__exit_code != 0:
            raise BadEnvironment("Scan failed (exit code %d)" %
                (self.__exit_code,))
        if self.__err:
            raise BadEnvironment("Scan failed (error output detected)")
        if not self.__out:
            raise BadEnvironment("Scan failed (no output)")

    def __scanned(self):
        return self.__exit_code is not None

    def __scanner_script(self):
        script_lines = []
        if self.__extra_script_imports:
            for x in self.__extra_script_imports:
                script_lines.append("import %s" % (x,))
            script_lines.append("")
        script_lines.append(self.__scanner_script__startup)
        script_lines.append("")
        if self.__scan_for_version_info:
            script_lines.append(self.__scanner_script__package_version_scanner)
        script_lines.extend(self.__extra_script_functions)
        script_lines.append("")
        script_lines.append('print("%s")' % (self.SCAN_START_MARKER,))
        script_lines.extend(getter for id, getter, default in self.__fields)
        script_lines.append('print("%s")' % (self.SCAN_FINISH_MARKER,))
        script_lines.append("")
        return "\n".join(script_lines)
