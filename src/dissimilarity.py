#!/usr/bin/env python
"""
    dissimilarity - python module for classes and methods related to similarity
                    measuring between two sets of data.
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

import math


def norm(x):
    """
    Return norm of numeric vector x.
    """
    return math.sqrt(sum([x_i**2 for x_i in x]))


def dot_product(x, y):
    """
    Return dot product of numeric vectors 'x' and 'y'.
    """
    return sum([(x[i] * y[i]) for i in range(len(x))])


class Dissimilarity:
    """
    Abstraction for different measures of dissimilarity between two sets or
    vectors.
    """


class EuclidianDistance(Dissimilarity):
    """
    Euclidian distance between two vectors.
    """
    def __call__(self, x, y):
        """
        Return euclidian distance between vectors 'x' and 'y'.
        """
        sum_pow = sum([((x[i] - y[i]) ** 2) for i in range(len(x))])
        return math.sqrt(sum_pow)


class CosineDissimilarity(Dissimilarity):
    """
    Dissimilarity measure complementary to the cosine similarity
    which is defined by the cosine of the angle between two vectors.
    """
    def __call__(self, x, y):
        """
        Return complement of the cosine of angle between vectors 'x' and 'y'.
        """
        return 1-(float(dot_product(x, y)/(norm(x)*norm(y))))


class JaccardDistance(Dissimilarity):
    """
    Dissimilarity measure complentary to Jaccard Index which is defined by
    the quantity of common values divided by the size of the two sets union.
    """
    def __call__(self, x, y):
        """
        Return Jaccard Index between sets 'x' and 'y'.
        """
        common = [v for v in x if v in y]
        return 1-(float(len(common))/(len(x)+len(y)-len(common)))


class DiffCoefficient(Dissimilarity):
    """
    Measure the difference between the two sets in terms of how many items
    should be added and removed from one set to transform it into the
    other set. Similar to edit distance, but the items positions are not
    relevant for sets.
    """
    def __call__(self, x, y):
        """
        Return the diff coeficient between sets 'x' and 'y'.
        """
        add = [v for v in x if v not in y]
        delete = [v for v in y if v not in x]
        common = [v for v in x if v in y]

        return float((len(add)+len(delete))/(len(x)+len(y)-len(common)))
