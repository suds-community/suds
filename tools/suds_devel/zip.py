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
Zip compression related utilities.

"""

import os
import os.path
import sys
import zipfile

from suds_devel.utility import path_iter


def zip_folder_content(folder, zip_file):
    success = False
    zippy = zipfile.ZipFile(zip_file, "w", _zip_compression())
    try:
        archiver = _Archiver(zippy, folder)
        for root, folders, files in os.walk(folder):
            archiver.add_folder_with_files(root, files)
        success = True
    finally:
        zippy.close()
        if not success:
            os.remove(zip_file)


class _Archiver:

    def __init__(self, zip_file, folder):
        self.__zip_file = zip_file
        self.__base_folder_parts = list(path_iter(folder))

    def add_folder_with_files(self, folder, files):
        path_prefix = self.__path_prefix(folder)
        for file in files:
            assert file
            file_path = os.path.join(folder, file)
            self.__zip_file.write(file_path, path_prefix + file)
        # If no files are present in this folder and this is not the base
        # folder then we need to add the folder itself as an explicit entry.
        if not files and path_prefix:
            # Old Python versions did not support using the ZipFile.write()
            # method on folders so we do it manually by adding a 0-size entry
            # using ZipFile.writestr(). Encountered using Python 2.4.3.
            # N.B. An archived folder name must include a trailing slash, which
            # is exactly what we have in our prepared path_prefix value.
            self.__zip_file.writestr(path_prefix, "")

    def __path_prefix(self, folder):
        """
        Path prefix to be used when archiving any items from the given folder.

        Expects the folder to be located under the base folder path and the
        returned path prefix does not include the base folder information. This
        makes sure we include just the base folder's content in the archive,
        and not the base folder itself.

        """
        path_parts = path_iter(folder)
        _skip_expected(path_parts, self.__base_folder_parts)
        result = "/".join(path_parts)
        if result:
            result += "/"
        return result


# Mimic the next() built-in introduced in Python 2.6. Does not need to be
# perfect but only as good as we need it internally in this module.
if sys.version_info < (2, 6):
    def _iter_next(iter):
        return iter.next()
else:
    _iter_next = next


def _skip_expected(iter, expected):
    for expected_value in expected:
        value = _iter_next(iter)
        assert value == expected_value


_zip_compression_value = None

def _zip_compression():
    global _zip_compression_value
    if _zip_compression_value is None:
        try:
            import zlib
            _zip_compression_value = zipfile.ZIP_DEFLATED
        except ImportError:
            _zip_compression_value = zipfile.ZIP_STORED
    return _zip_compression_value
