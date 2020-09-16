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
"poor man's tox" development script used on Windows to run the full suds-jurko
test suite using multiple Python interpreter versions.

Intended to be used as a general 'all tests passed' check. To see more detailed
information on specific failures, run the failed test group manually,
configured for greater verbosity than done here.

"""

import os.path
import shutil
import sys

from suds_devel.configuration import BadConfiguration, Config, configparser
from suds_devel.environment import BadEnvironment
import suds_devel.utility as utility


class MyConfig(Config):

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
        try:
            self._read_environment_configuration()
        except configparser.Error:
            raise BadConfiguration(sys.exc_info()[1].message)


def _prepare_configuration():
    # We know we are a regular stand-alone script file and not an imported
    # module (either frozen, imported from disk, zip-file, external database or
    # any other source). That means we can safely assume we have the __file__
    # attribute available.
    global config
    config = MyConfig(__file__, "..", "setup.cfg")


def _print_title(env, message_fmt):
    separator = "-" * 63
    print("")
    print(separator)
    print("--- " + message_fmt % (env.name(),))
    print(separator)


def _report_startup_information():
    print("Running in folder: '%s'" % (os.getcwd(),))


def _run_tests(env):
    if env.sys_version_info >= (3,):
        _print_title(env, "Building suds for Python %s")
        build_folder = os.path.join(config.project_folder, "build")
        if os.path.isdir(build_folder):
            shutil.rmtree(build_folder)

    # Install the project into the target Python environment in editable mode.
    # This will actually build Python 3 sources in case we are using a Python 3
    # environment.
    setup_cmd = ["setup.py", "-q", "develop"]
    _, _, return_code = env.execute(setup_cmd, cwd=config.project_folder)
    if return_code != 0:
        return False

    test_folder = os.path.join(config.project_folder, "tests")
    pytest_cmd = ["-m", "pytest", "-q", "-x", "--tb=short"]

    _print_title(env, "Testing suds with Python %s")
    _, _, return_code = env.execute(pytest_cmd, cwd=test_folder)
    if return_code != 0:
        return False

    _print_title(env, "Testing suds with Python %s - no assertions")
    pytest_cmd.insert(0, "-O")
    _, _, return_code = env.execute(pytest_cmd, cwd=test_folder)
    return return_code == 0


def _run_tests_in_all_environments():
    if not config.python_environments:
        raise BadConfiguration("No Python environments configured.")
    for env in config.python_environments:
        if not env.initial_scan_completed:
            _print_title(env, "Scanning environment Python %s")
            env.run_initial_scan()
        if not _run_tests(env):
            return False
    return True


def main():
    try:
        _report_startup_information()
        _prepare_configuration()
        success = _run_tests_in_all_environments()
    except (BadConfiguration, BadEnvironment):
        utility.report_error(sys.exc_info()[1])
        return -2
    print("")
    if not success:
        print("Test failed.")
        return -3
    print("All tests passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
