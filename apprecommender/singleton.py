#!/usr/bin/env python
"""
    singleton - python class that implements singleton design pattern.
"""
__author__ = "Tassia Camoes Araujo <tassia@gmail.com>"
__copyright__ = "Copyright (C) 2011 Tassia Camoes Araujo"
__license__ = """
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""


class Singleton(object):
    """
    Base class for inheritance of only-one-instance classes.
    Singleton design pattern.
    """
    def __new__(cls, *args, **kwargs):
        """
        Creates a new instance of the class only if none already exists.
        """
        if '_inst' not in vars(cls):
            cls._inst = object.__new__(cls)
        return cls._inst
