#!/usr/bin/env python
"""
    strategy - python module for classes and methods related to recommendation
               strategies.
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

import os, re
import xapian
from data import *
from singleton import Singleton
import recommender

class ReputationHeuristic(Singleton):
    """
    Abstraction for diferent reputation heuristics.
    """
    pass

class BugsHeuristic(ReputationHeuristic):
    """
    Reputation heuristic based on quantity of open bugs.
    """
    pass

class RCBugsHeuristic(ReputationHeuristic):
    """
    Reputation heuristic based on quantity of RC bugs.
    """
    pass

class PopularityHeuristic(ReputationHeuristic):
    """
    Reputation heuristic based on popularity of packages.
    """
    pass

class PkgMatchDecider(xapian.MatchDecider):
    """
    Extend xapian.MatchDecider to not consider installed packages.
    """

    def __init__(self, installed_pkgs):
        """
        Set initial parameters.
        """
        xapian.MatchDecider.__init__(self)
        self.installed_pkgs = installed_pkgs

    def __call__(self, doc):
        """
        True if the package is not already installed.
        """
        return doc.get_data() not in self.installed_pkgs

class UserMatchDecider(xapian.MatchDecider):
    """
    Extend xapian.MatchDecider to match similar profiles.
    """

    def __init__(self, profile):
        """
        Set initial parameters.
        """
        xapian.MatchDecider.__init__(self)
        self.profile = profile
        print "mdecider:",profile

    def __call__(self, doc):
        """
        True if the user has more the half of packages from profile.
        """
        profile_size = len(self.profile)
        pkg_match=0
        for term in doc:
            if term.term in self.profile:
                pkg_match = pkg_match+1
        print "id",doc.get_docid(),"match",pkg_match
        return pkg_match >= profile_size/2 

class PkgExpandDecider(xapian.ExpandDecider):
    """
    Extend xapian.ExpandDecider to consider packages only.
    """

    def __init__(self):
        """
        Call base class init.
        """
        xapian.ExpandDecider.__init__(self)

    def __call__(self, term):
        """
        True if the term is a package.
        """
        return not term.startswith("XT")

class TagExpandDecider(xapian.ExpandDecider):
    """
    Extend xapian.ExpandDecider to consider tags only.
    """

    def __init__(self, profile):
        """
        Call base class init.
        """
        xapian.ExpandDecider.__init__(self)

    def __call__(self, doc):
        """
        True if the user has more the half of packages from profile.
        """
        return term.startswith("XT")

class RecommendationStrategy:
    """
    Base class for recommendation strategies.
    """
    pass

class ItemReputationStrategy(RecommendationStrategy):
    """
    Recommendation strategy based on items reputation.
    """
    def run(self,items_list,heuristic):
        """
        Perform recommendation strategy.
        """
        logging.critical("Item reputation recommendation strategy is not yet implemented.")
        raise Error

class ContentBasedStrategy(RecommendationStrategy):
    """
    Content-based recommendation strategy.
    """
    def run(self,rec,user):
        """
        Perform recommendation strategy.
        """
        profile = user.txi_tag_profile(rec.items_repository,50)
        qp = xapian.QueryParser()
        query = qp.parse_query(profile)
        enquire = xapian.Enquire(rec.items_repository)
        enquire.set_query(query)

        try:
            mset = enquire.get_mset(0, 20, None, PkgMatchDecider(user.items()))
        except xapian.DatabaseError as error:
            logging.critical(error.get_msg())
            raise Error

        item_score = {}
        for m in mset:
            item_score[m.document.get_data()] = m.rank
        return recommender.RecommendationResult(item_score,20)

class AxiContentBasedStrategy(RecommendationStrategy):
    """
    Content-based recommendation strategy based on Apt-xapian-index.
    """
    def run(self,rec,user):
        """
        Perform recommendation strategy.
        """
        profile = user.axi_tag_profile(rec.items_repository,50)
        query = xapian.Query(xapian.Query.OP_OR,profile)
        enquire = xapian.Enquire(rec.items_repository)
        enquire.set_query(query)

        try:
            mset = enquire.get_mset(0, 20, None, PkgMatchDecider(user.items()))
        except xapian.DatabaseError as error:
            logging.critical(error.get_msg())
            raise Error

        item_score = {}
        for m in mset:
            item_score[m.document.get_data()] = m.rank
        return recommender.RecommendationResult(item_score,20)

class CollaborativeStrategy(RecommendationStrategy):
    """
    Colaborative recommendation strategy.
    """
    #def run(self,rec,user,similarity_measure):
    def run(self,rec,user):
        """
        Perform recommendation strategy.
        """
        profile = user.maximal_pkg_profile()
        query = xapian.Query(xapian.Query.OP_OR,profile)
        enquire = xapian.Enquire(rec.users_repository)
        enquire.set_query(query)

        try:
            #mset = enquire.get_mset(0, 182, None, UserMatchDecider(profile))
            mset = enquire.get_mset(0, 20)
        except xapian.DatabaseError as error:
            logging.critical(error.get_msg())
            raise Error

        rset = xapian.RSet()
        for m in mset:
            rset.add_document(m.document.get_docid())
            logging.debug("Counting as relevant submission %s" %
                           m.document.get_data())

        eset = enquire.get_eset(20,rset,PkgExpandDecider())
        rank = 0
        item_score = {}
        for term in eset:
            item_score[term.term] = rank
            rank = rank+1

        return recommender.RecommendationResult(item_score,20)

class KnowledgeBasedStrategy(RecommendationStrategy):
    """
    Knowledge-based recommendation strategy.
    """
    def run(self,user,knowledge_repository):
        """
        Perform recommendation strategy.
        """
        logging.critical("Knowledge-based recommendation strategy is not yet implemented.")
        raise Error

class DemographicStrategy(RecommendationStrategy):
    """
    Recommendation strategy based on demographic data.
    """
    def run(self,user,items_repository):
        """
        Perform recommendation strategy.
        """
        logging.critical("Demographic recommendation strategy is not yet implemented.")
        raise Error
