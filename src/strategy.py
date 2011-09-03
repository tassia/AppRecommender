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

import xapian
from singleton import Singleton
import recommender
import data
import logging
from error import Error

class PkgMatchDecider(xapian.MatchDecider):
    """
    Extend xapian.MatchDecider to not consider installed packages.
    """
    def __init__(self, pkgs_list):
        """
        Set initial parameters.
        """
        xapian.MatchDecider.__init__(self)
        self.pkgs_list = pkgs_list

    def __call__(self, doc):
        """
        True if the package is not already installed.
        """
        pkg = doc.get_data()
        is_new = pkg not in self.pkgs_list
        if "kde" in pkg:
            return is_new and "kde" in self.pkgs_list
        if "gnome" in pkg:
            return is_new and "gnome" in self.pkgs_list
        return is_new

class PkgExpandDecider(xapian.ExpandDecider):
    """
    Extend xapian.ExpandDecider to consider packages only.
    """
    def __init__(self, pkgs_list):
        """
        Set initial parameters.
        """
        xapian.ExpandDecider.__init__(self)
        self.pkgs_list = pkgs_list

    def __call__(self, term):
        """
        True if the term is a package.
        """
        pkg = term.lstrip("XP") 
        is_new_pkg = pkg not in self.pkgs_list and term.startswith("XP")
        if "kde" in pkg:
            return is_new_pkg and "kde" in self.pkgs_list
        if "gnome" in pkg:
            return is_new_pkg and "gnome" in self.pkgs_list
        return is_new_pkg

class TagExpandDecider(xapian.ExpandDecider):
    """
    Extend xapian.ExpandDecider to consider tags only.
    """
    def __call__(self, term):
        """
        True if the term is a package tag.
        """
        return term.startswith("XT")

class RecommendationStrategy:
    """
    Base class for recommendation strategies.
    """
    pass

class ContentBased(RecommendationStrategy):
    """
    Content-based recommendation strategy based on Apt-xapian-index.
    """
    def __init__(self,content,profile_size):
        self.description = "Content-based"
        self.content = content
        self.profile_size = profile_size

    def get_sugestion_from_profile(self,rec,user,profile,recommendation_size):
        query = xapian.Query(xapian.Query.OP_OR,profile)
        print query
        enquire = xapian.Enquire(rec.items_repository)
        enquire.set_weighting_scheme(rec.weight)
        enquire.set_query(query)
        # Retrieve matching packages
        try:
            mset = enquire.get_mset(0, recommendation_size, None,
                                    PkgMatchDecider(user.items()))
        except xapian.DatabaseError as error:
            logging.critical("Content-based strategy: "+error.get_msg())

        # Compose result dictionary
        item_score = {}
        ranking = []
        for m in mset:
            item_score[m.document.get_data()] = m.weight
            ranking.append(m.document.get_data())

        result = recommender.RecommendationResult(item_score,ranking)
        return result

    def run(self,rec,user,recommendation_size):
        """
        Perform recommendation strategy.
        """
        logging.debug("Composing user profile...")
        profile = user.content_profile(rec.items_repository,self.content,
                                       self.profile_size,rec.valid_tags)
        logging.debug(profile)
        result = self.get_sugestion_from_profile(rec,user,profile,recommendation_size)
        return result

class Collaborative(RecommendationStrategy):
    """
    Colaborative recommendation strategy.
    """
    def get_user_profile(self,user,rec):
        logging.debug("Composing user profile...")
        profile = ["XP"+package for package in
                   user.filter_pkg_profile(rec.valid_pkgs)]
        logging.debug(profile)
        return profile

    def get_enquire(self,rec):
        enquire = xapian.Enquire(rec.users_repository)
        enquire.set_weighting_scheme(rec.weight)
        return enquire

    def get_rset_from_profile(self,profile):
        # Create document to represent user profile and mark it as relevant
        return rset

    def get_neighborhood(self,user,rec):
        profile = self.get_user_profile(user,rec)
        #query = xapian.Query(xapian.Query.OP_OR,profile)
        query = xapian.Query(xapian.Query.OP_ELITE_SET,profile)
        enquire = self.get_enquire(rec)
        enquire.set_query(query)
        # Retrieve matching users
        try:
            mset = enquire.get_mset(0, self.neighbours)
        except xapian.DatabaseError as error:
            logging.critical("Could not compose user neighborhood.\n "+error.get_msg())
            raise Error
        return mset

    def get_neighborhood_rset(self,user,rec):
        mset = self.get_neighborhood(user,rec)
        rset = xapian.RSet()
        for m in mset:
            rset.add_document(m.document.get_docid())
        return rset

    def get_result_from_eset(self,eset):
        # compose result dictionary
        item_score = {}
        ranking = []
        for e in eset:
            package = e.term.lstrip("XP")
            item_score[package] = e.weight
            ranking.append(package)
        return recommender.RecommendationResult(item_score, ranking)

class Knn(Collaborative):
    """
    KNN based packages tf-idf weights.
    """
    def __init__(self,k):
        self.description = "Knn"
        self.neighbours = k

    def run(self,rec,user,recommendation_size):
        """
        Perform recommendation strategy.
        """
        neighborhood = self.get_neighborhood(user,rec)
        weights = data.tfidf_weighting(rec.users_repository,neighborhood,
                                       PkgExpandDecider(user.items()))
        item_score = {}
        ranking = []
        for pkg in weights[:recommendation_size]:
            package = pkg[0].lstrip("XP")
            item_score[package] = pkg[1]
            ranking.append(package)
        result = recommender.RecommendationResult(item_score, ranking)
        return result

class KnnPlus(Collaborative):
    """
    KNN based packages tf-idf weights.
    """
    def __init__(self,k):
        self.description = "Knn"
        self.neighbours = k

    def run(self,rec,user,recommendation_size):
        """
        Perform recommendation strategy.
        """
        neighborhood = self.get_neighborhood(user,rec)
        weights = data.tfidf_plus(rec.users_repository,neighborhood,
                                  PkgExpandDecider(user.items()))
        item_score = {}
        ranking = []
        for pkg in weights[:recommendation_size]:
            package = pkg[0].lstrip("XP")
            item_score[package] = pkg[1]
            ranking.append(package)
        result = recommender.RecommendationResult(item_score, ranking)
        return result

class KnnEset(Collaborative):
    """
    KNN based on query expansion.
    """
    def __init__(self,k):
        self.description = "KnnEset"
        self.neighbours = k

    def run(self,rec,user,recommendation_size):
        """
        Perform recommendation strategy.
        """
        neighbors_rset = self.get_neighborhood_rset(user,rec)
        enquire = self.get_enquire(rec)
        # Retrieve new packages based on neighborhood profile expansion
        eset = enquire.get_eset(recommendation_size,neighbors_rset,
                                PkgExpandDecider(user.items()))
        result = self.get_result_from_eset(eset)
        return result

class CollaborativeEset(Collaborative):
    """
    Colaborative strategy based on query expansion.
    """
    def __init__(self):
        self.description = "Collaborative-Eset"

    def run(self,rec,user,recommendation_size):
        """
        Perform recommendation strategy.
        """
        temp_index = xapian.WritableDatabase("/tmp/Database",xapian.DB_CREATE_OR_OVERWRITE)
        profile = self.get_user_profile(user,rec)
        doc = xapian.Document()
        for pkg in profile:
            doc.add_term(pkg)
        doc.add_term("TO_BE_DELETED")
        docid = temp_index.add_document(doc)
        temp_index.add_database(rec.users_repository)
        rset = xapian.RSet()
        rset.add_document(docid)
        # rset = self.get_rset_from_profile(profile)
        enquire = xapian.Enquire(temp_index)
        enquire.set_weighting_scheme(rec.weight)
        eset = enquire.get_eset(recommendation_size,rset,
                                PkgExpandDecider(user.items()))
        result = self.get_result_from_eset(eset)
        return result

class KnnContent(Collaborative):
    """
    Hybrid "Colaborative through content" recommendation strategy.
    """
    def __init__(self,k):
        self.description = "Knn-Content"
        self.neighbours = k

    def run(self,rec,user,recommendation_size):
        """
        Perform recommendation strategy.
        """
        neighborhood = self.get_neighborhood(user,rec)
        weights = data.tfidf_weighting(rec.users_repository,neighborhood,
                                       PkgExpandDecider(user.items()))
        profile = [w[0] for w in weights][:rec.cfg.profile_size]
        result = ContentBased("tag",rec.cfg.profile_size).get_sugestion_from_profile(rec,user,profile,recommendation_size)
        return result

class KnnContentEset(Collaborative):
    """
    Hybrid "Colaborative through content" recommendation strategy.
    """
    def __init__(self,k):
        self.description = "Knn-Content-Eset"
        self.neighbours = k

    def run(self,rec,user,recommendation_size):
        """
        Perform recommendation strategy.
        """
        neighbors_rset = self.get_neighborhood_rset(user,rec)
        enquire = self.get_enquire(rec)
        # Retrieve relevant tags based on neighborhood profile expansion
        eset = enquire.get_eset(rec.cfg.profile_size,neighbors_rset,
                                TagExpandDecider())
        profile = [e.term for e in eset]
        result = ContentBased("tag",rec.cfg.profile_size).get_sugestion_from_profile(rec,user,profile,recommendation_size)
        return result

class Demographic(RecommendationStrategy):
    """
    Hybrid rotation strategy based on demographic data.
    """
    def __init__(self,strategy_str):
        self.description = "Demographic"
        self.strategy_str = strategy_str.lstrip("demo_")

    def run(self,rec,user,recommendation_size):
        """
        Perform recommendation strategy.
        """
        program_profile = user.filter_pkg_profile(os.path.join(rec.cfg.filters_dir,"programs"))
        desktop_profile = user.filter_pkg_profile(os.path.join(rec.cfg.filters_dir,"desktopapps"))
        if (len(desktop_profile)>10 or
            len(desktop_profile)>len(program_profile)/2):
            rec.set_strategy(self.strategy_str)
            # Redefine repositories after configuring strategy
            rec.items_repository = rec.axi_desktopapps
            rec.valid_pkgs = rec.valid_desktopapps
            if "col" in self.strategy_str:
                rec.users_repository = rec.popcon_desktopapps
        return rec.get_recommendation(user,recommendation_size)
