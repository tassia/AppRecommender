#!/usr/bin/python

#  AppRecommender - A GNU/Linux application recommender
#
#  Copyright (C) 2010  Tassia Camoes <tassia@gmail.com>
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.

import math
import stats

def norm(x):
    """ Return vector norm. """
    return math.sqrt(sum([x_i**2 for x_i in x]))

def dot_product(x,y):
    """ Return dot product of vectors 'x' and 'y'. """
    return sum([(x[i] * y[i]) for i in range(len(x))])

class SimilarityMeasure:
    """ Abstraction for diferent similarity measure approaches. """

class Distance(SimilarityMeasure):
    """ Euclidian distance measure. """
    def __call__(self,x,y):
        """ Return euclidian distance between vectors 'x' and 'y'. """
        sum_pow = sum([((x[i] - y[i]) ** 2) for i in range(len(x))])
        return math.sqrt(sum_pow)

class Cosine(SimilarityMeasure):
    """ Cosine similarity measure. """
    def __call__(self,x,y):
        """ Return cosine of angle between vectors 'x' and 'y'. """
        return float(dot_product(x,y)/(norm(x)*norm(y)))

class Pearson(SimilarityMeasure):
    """ Pearson coeficient measure. """ # FIXME: ZeroDivisionError
    def __call__(self,x,y):
        """ Return Pearson coeficient between vectors 'x' and 'y'. """
        return stats.pearsonr(x,y)

class Spearman(SimilarityMeasure):
    """ Spearman correlation measure. """ # FIXME: ZeroDivisionError
    def __call__(self,x,y):
        """ Return Spearman correlation between vectors 'x' and 'y'. """
        return stats.spearmanr(x,y)

class Tanimoto(SimilarityMeasure):
    " Tanimoto coeficient measure. """
    def __call__(self,x,y):
        """ Return Tanimoto coeficient between vectors 'x' and 'y'. """
        z = [v for v in x if v in y]
        return float(len(z))/(len(x)+len(y)-len(z))
