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
Manipulating egg distributions.

"""

import os
import os.path

from suds_devel.zip import zip_folder_content


def zip_eggs_in_folder(folder):
    """
    Make all egg distributions in the given folder be stored as egg files.

    In case setuptools downloads one of its target packages as an unzipped egg
    folder (e.g. if installed from an already installed unzipped egg), we need
    to zip it ourselves. This is because there seems to be no way to make
    setuptools perform an installation from a local unzipped egg folder.
    Specifying either that folder or its parent folder as a setuptools
    find-links URL just makes the folder be treated as a regular non-egg
    folder.

    """
    eggs = _detect_eggs_in_folder(folder)
    for egg in eggs:
        egg.normalize()


# Egg distribution related file & folder name extensions.
_egg_ext = os.extsep + "egg"
_zip_ext = _egg_ext + os.extsep + "zip"


class _Egg:
    """
    Represents a single egg distribution.

    Helps track & manage formats the distribution is stored in:
      - zipped egg file with .egg extension
      - zipped egg file with .egg.zip extension
      - unzipped egg folder

    """

    # Indicators whether the egg distribution has a '.egg' file or folder.
    NONE = object()
    FILE = object()
    FOLDER = object()

    def __init__(self, path, egg, zip):
        assert egg in (_Egg.NONE, _Egg.FILE, _Egg.FOLDER)
        assert zip.__class__ is bool
        assert zip or egg is not _Egg.NONE
        self.__path = path
        self.__egg = egg
        self.__zip = zip

    def has_egg_file(self):
        return self.__egg is _Egg.FILE

    def has_egg_folder(self):
        return self.__egg is _Egg.FOLDER

    def has_zip(self):
        return self.__zip

    def normalize(self):
        """
        Makes sure this egg distribution is stored only as an egg file.

        The egg file will be created from another existing distribution format
        if needed.

        """
        if self.has_egg_file():
            if self.has_zip():
                self.__remove_zip()
        else:
            if self.has_egg_folder():
                if not self.has_zip():
                    self.__zip_egg_folder()
                self.__remove_egg_folder()
            self.__rename_zip_to_egg()

    def set_egg(self, egg):
        assert egg in (_Egg.FILE, _Egg.FOLDER)
        assert self.__egg is _Egg.NONE
        self.__egg = egg

    def set_zip(self):
        assert not self.__zip
        self.__zip = True

    def __path_egg(self):
        return self.__path + _egg_ext

    def __path_zip(self):
        return self.__path + _zip_ext

    def __remove_egg_folder(self):
        assert self.has_egg_folder()
        import shutil
        shutil.rmtree(self.__path_egg())
        self.__egg = _Egg.NONE

    def __remove_zip(self):
        assert self.has_zip()
        os.remove(self.__path_zip())
        self.__zip = False

    def __rename_zip_to_egg(self):
        assert self.has_zip()
        assert not self.has_egg_file()
        assert not self.has_egg_folder()
        os.rename(self.__path_zip(), self.__path_egg())
        self.__egg = _Egg.FILE
        self.__zip = False

    def __zip_egg_folder(self):
        assert self.has_egg_folder()
        assert not self.has_zip()
        zip_folder_content(self.__path_egg(), self.__path_zip())
        self.__zip = True


def _detect_eggs_in_folder(folder):
    """
    Detect egg distributions located in the given folder.

    Only direct folder content is considered and subfolders are not searched
    recursively.

    """
    eggs = {}
    for x in os.listdir(folder):
        zip = x.endswith(_zip_ext)
        if zip:
            root = x[:-len(_zip_ext)]
            egg = _Egg.NONE
        elif x.endswith(_egg_ext):
            root = x[:-len(_egg_ext)]
            if os.path.isdir(os.path.join(folder, x)):
                egg = _Egg.FOLDER
            else:
                egg = _Egg.FILE
        else:
            continue
        try:
            info = eggs[root]
        except KeyError:
            eggs[root] = _Egg(os.path.join(folder, root), egg, zip)
        else:
            if egg is not _Egg.NONE:
                info.set_egg(egg)
            if zip:
                info.set_zip()
    return eggs.values()
