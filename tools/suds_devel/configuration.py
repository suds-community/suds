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
Basic configuration support shared in different development utility scripts.

"""

import os.path
import sys

# Must not use the six Python 2/3 compatibility package from here as this
# module gets used from the script for setting up basic development
# environments, and that script needs to be runnable even before the six
# package has been installed.
if sys.version_info < (3,):
    import ConfigParser as configparser
else:
    import configparser

from suds_devel.environment import Environment
import suds_devel.utility as utility


class BadConfiguration(Exception):
    def __init__(self, message):
        Exception.__init__(self, message)


class Config(object):

    # Typed option values.
    BOOLEAN_TRUE  = ('1', 'yes', 'true', 'on', '+')
    BOOLEAN_FALSE = ('0', 'no', 'false', 'off', '-')
    IF_NEEDED     = ('maybe', '?',
                     'ifneeded', 'if needed',
                     'asneeded', 'as needed',
                     'ondemand', 'on demand')

    class TriBool:
        Yes = object()
        IfNeeded = object()
        No = object()

    def __init__(self, script, project_folder, ini_file):
        """
        Initialize new script configuration.

        External configuration parameters may be specified relative to the
        following folders:
          * script - relative to the current working folder
          * project_folder - relative to the script folder
          * ini_file - relative to the project folder

        """
        self.__init_script_folder(script)
        self.__init_project_folder(project_folder)
        self.__init_ini_file(ini_file)
        self.__init_reader()

    def _get_bool(self, section, option):
        x = self._reader.get(section, option).lower()
        if x in self.BOOLEAN_TRUE:
            return True
        if x in self.BOOLEAN_FALSE:
            return False
        raise BadConfiguration("Option '%s.%s' must be a boolean value." % (
            section, option))

    def _get_tribool(self, section, option):
        x = self._reader.get(section, option).lower()
        if x in self.BOOLEAN_TRUE:
            return Config.TriBool.Yes
        if x in self.BOOLEAN_FALSE:
            return Config.TriBool.No
        if x in self.IF_NEEDED:
            return Config.TriBool.IfNeeded
        raise BadConfiguration("Option '%s.%s' must be Yes, No or IfNeeded." %
            (section, option))

    def _read_environment_configuration(self):
        section_prefix = "env:"
        command_option = "command"
        self.python_environments = []
        for section in self._reader.sections():
            if section.lower().startswith(section_prefix):
                name = section[len(section_prefix):]
                command = self._reader.get(section, command_option)
                if not command:
                    raise BadConfiguration("'%s.%s' environment command "
                        "configuration option must not be empty." % (section,
                        command_option))
                self.python_environments.append(Environment(name, command))

    def __init_ini_file(self, ini_file):
        self.ini_file = os.path.join(self.project_folder, ini_file)
        self.ini_file = os.path.normpath(self.ini_file)
        if not os.path.isfile(self.ini_file):
            raise BadConfiguration("Missing configuration file '%s'." % (
                self.ini_file,))

    def __init_project_folder(self, project_folder):
        p = os.path.normpath(os.path.join(self.script_folder, project_folder))
        if not os.path.isdir(p):
            raise BadConfiguration("Could not find project folder '%s'." % p)
        self.project_folder = p

    def __init_reader(self):
        try:
            f = open(self.ini_file, "r")
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception:
            raise BadConfiguration("Can not access configuration file '%s' - "
                "%s." % (self.ini_file, sys.exc_info()[1]))
        try:
            print("Reading configuration file '%s'..." % (self.ini_file,))
            self._reader = configparser.ConfigParser()
            self._reader.readfp(f)
        finally:
            f.close()

    def __init_script_folder(self, script):
        self.script_folder = utility.script_folder(script)
        if not self.script_folder:
            raise BadConfiguration("Could not determine script folder.")
