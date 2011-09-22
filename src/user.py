#!/usr/bin/env python
"""
    user - python module for classes and methods related to recommenders' users.
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

import os
import random
import commands
import datetime
import xapian
import logging
import apt
from error import Error
from singleton import Singleton
import data
import operator
import math

class FilterTag(xapian.ExpandDecider):
    """
    Extend xapian.ExpandDecider to consider only tag terms.
    """
    def __init__(self, valid_tags):
        """
        Set initial parameters.
        """
        xapian.ExpandDecider.__init__(self)
        self.valid_tags = valid_tags

    def __call__(self, term):
        """
        Return true if the term is a tag, else false.
        """
        if self.valid_tags:
            is_valid = term.lstrip("XT") in self.valid_tags
        else:
            is_valid = 1
        return term.startswith("XT") and is_valid

class FilterDescription(xapian.ExpandDecider):
    """
    Extend xapian.ExpandDecider to consider only package description terms.
    """
    def __call__(self, term):
        """
        Return true if the term or its stemmed version is part of a package
        description.
        """
        return term.islower() or term.startswith("Z")

class FilterTag_or_Description(xapian.ExpandDecider):
    """
    Extend xapian.ExpandDecider to consider only package description terms.
    """
    def __init__(self, valid_tags):
        """
        Set initial parameters.
        """
        xapian.ExpandDecider.__init__(self)
        self.valid_tags = valid_tags

    def __call__(self, term):
        """
        Return true if the term or its stemmed version is part of a package
        description.
        """
        is_tag = FilterTag(self.valid_tags)(term)
        is_description = FilterDescription()(term)
        return is_tag or is_description

class DemographicProfile(Singleton):
    def __init__(self):
        self.admin   = set(["admin", "hardware", "mail", "protocol",
                            "network", "security", "web", "interface::web"])
        self.devel   = set(["devel", "role::devel-lib", "role::shared-lib"])
        self.desktop = set(["x11", "accessibility", "game", "junior", "office",
                            "interface::x11"])
        self.art     = set(["field::arts", "sound"])
        self.science = set(["science", "biology", "field::astronomy",
                            "field::aviation",  "field::biology",
                            "field::chemistry", "field::eletronics",
                            "field::finance", "field::geography",
                            "field::geology", "field::linguistics",
                            "field::mathematics", "field::medicine",
                            "field::meteorology", "field::physics",
                            "field::statistics"])

    def __call__(self,profiles_set):
        demographic_profile = set()
        for profile in profiles_set:
            demographic_profile = (demographic_profile | eval("self."+profile,{},{"self":self}))
        return demographic_profile

class User:
    """
    Define a user of a recommender.
    """
    def __init__(self,item_score,user_id=0,arch=0,demo_profiles_set=0):
        """
        Set initial user attributes. pkg_profile gets the whole set of items,
        a random user_id is set if none was provided and the demographic
        profile defaults to 'desktop'.
        """
        self.item_score = item_score
        self.pkg_profile = self.items()
        self.arch = arch

        if user_id:
            self.user_id = user_id
        else:
            random.seed()
            self.id = random.getrandbits(128)

        if not demo_profiles_set:
            profiles_set = set(["desktop"])
        self.set_demographic_profile(profiles_set)

    def items(self):
        """
        Return the set of user items.
        """
        return self.item_score.keys()

    def set_demographic_profile(self,profiles_set):
        """
        Set demographic profle based on labels in 'profiles_set'.
        """
        self.demographic_profile = DemographicProfile()(profiles_set)

    def content_profile(self,items_repository,content,size,valid_tags=0):
        """
        Get user profile for a specific type of content: packages tags,
        description or both (mixed and half-half profiles)
        """
        if content == "tag":
            profile = self.tfidf_profile(items_repository,size,FilterTag(valid_tags))
        elif content == "desc":
            profile = self.tfidf_profile(items_repository,size,FilterDescription())
        elif content == "mix":
            profile = self.tfidf_profile(items_repository,size,FilterTag_or_Description(valid_tags))
        elif content == "half":
            tag_profile = self.tfidf_profile(items_repository,size,FilterTag(valid_tags))
            desc_profile = self.tfidf_profile(items_repository,size,FilterDescription())
            profile = tag_profile[:size/2]+desc_profile[:size/2]
        elif content == "tag_eset":
            profile = self.eset_profile(items_repository,size,FilterTag(valid_tags))
        elif content == "desc_eset":
            profile = self.eset_profile(items_repository,size,FilterDescription())
        elif content == "mix_eset":
            profile = self.eset_profile(items_repository,size,FilterTag_or_Description(valid_tags))
        elif content == "half_eset":
            tag_profile = self.eset_profile(items_repository,size,FilterTag(valid_tags))
            desc_profile = self.eset_profile(items_repository,size,FilterDescription())
            profile = tag_profile[:size/2]+desc_profile[:size/2]
        else:
            logging.debug("Unknown content type %s." % content)
            raise Error
        logging.debug("User %s profile: %s" % (content, profile))
        return profile

    def tfidf_profile(self,items_repository,size,content_filter):
        """
        Return the most relevant tags for the user list of packages based on
        the sublinear tfidf weight of packages' tags.
        """
        docs = data.axi_search_pkgs(items_repository,self.pkg_profile)
        #weights = data.tfidf_plus(items_repository,docs,content_filter)
        weights = data.tfidf_weighting(items_repository,docs,content_filter)
        # Eliminate duplicated stemmed term
        profile = self._eliminate_duplicated([w[0] for w in weights],size)
        return profile

    def eset_profile(self,items_repository,size,content_filter):
        """
        Return most relevant tags for a list of packages.
        """
        # Store package documents in a relevant set
        enquire = xapian.Enquire(items_repository)
        docs = data.axi_search_pkgs(items_repository,self.pkg_profile)
        rset_packages = xapian.RSet()
        for d in docs:
            rset_packages.add_document(d.docid)
        # Get expanded query terms (statistically good differentiators)
        eset_tags = enquire.get_eset(size*2,rset_packages,
                                     xapian.Enquire.INCLUDE_QUERY_TERMS,
                                     1,content_filter)
        # Eliminate duplicated stemmed term
        profile = self._eliminate_duplicated([res.term for res in eset_tags],size)
        return profile

    def _eliminate_duplicated(self,sorted_list,size):
        profile = sorted_list[:size]
        next_index = size
        duplicate = 1
        while duplicate:
            duplicate = 0
            for term in profile[:]:
                if term.startswith("Z"):
                    for p in profile[:]:
                        if p.startswith(term.lstrip("Z")):
                            duplicate = 1
                            profile.remove(p)
                            if len(sorted_list)>next_index:
                                profile.append(sorted_list[next_index])
                            next_index +=1
        return profile

    def filter_pkg_profile(self,filter_list_or_file):
        """
        Return list of packages from profile listed in the filter_file.
        """
        if type(filter_list_or_file).__name__ == "list":
            valid_pkgs = filter_list_or_file
        elif type(filter_list_or_file).__name__ == "str":
            try:
                with open(filter_list_or_file) as valid:
                    valid_pkgs = [line.strip() for line in valid]
            except IOError:
                logging.critical("Could not open profile filter file: %" %
                                 filter_list_or_file)
                raise Error
        else:
            logging.debug("No filter provided for user profiling.")
            return self.pkg_profile

        old_profile_size = len(self.pkg_profile)
        for pkg in self.pkg_profile[:]:     #iterate list copy
            if pkg not in valid_pkgs:
                self.pkg_profile.remove(pkg)
                logging.debug("Discarded package %s during profile filtering" % pkg)
        profile_size = len(self.pkg_profile)
        logging.debug("Filtered package profile: reduced packages profile size \
                       from %d to %d." % (old_profile_size, profile_size))
        return self.pkg_profile

    def maximal_pkg_profile(self):
        """
        Return list of packages that are not dependence of any other package in
        the list.
        """
        cache = apt.Cache()
        old_profile_size = len(self.pkg_profile)
        for p in self.pkg_profile[:]:     #iterate list copy
            try:
                if cache.has_key(p):
                    pkg = cache[p]
                    if pkg.candidate:
                        for dep in pkg.candidate.dependencies:
                            for or_dep in dep.or_dependencies:
                                if or_dep.name in self.pkg_profile:
                                    self.pkg_profile.remove(or_dep.name)
            except:
                logging.debug("Package not found in cache: %s" % p)
        profile_size = len(self.pkg_profile)
        logging.debug("Maximal package profile: reduced packages profile size \
                       from %d to %d." % (old_profile_size, profile_size))
        return self.pkg_profile

class RandomPopcon(User):
    def __init__(self,submissions_dir,arch=0,pkgs_filter=0):
        """
        Set initial parameters.
        """
        len_profile = 0
        match_arch = False
        while len_profile < 100 or not match_arch:
            path = random.choice([os.path.join(root, submission) for
                                  root, dirs, files in os.walk(submissions_dir)
                                  for submission in files])
            user = PopconSystem(path)
            print arch
            print user.arch
            if arch and user.arch==arch:
                match_arch = True
                print "match"
            if pkgs_filter:
                user.filter_pkg_profile(pkgs_filter)
            len_profile = len(user.pkg_profile)
            print "p",len_profile
        submission = data.PopconSubmission(path)
        User.__init__(self,submission.packages,submission.user_id,submission.arch)

class PopconSystem(User):
    def __init__(self,path,user_id=0):
        """
        Set initial parameters.
        """
        submission = data.PopconSubmission(path)
        if not user_id:
            user_id = submission.user_id
        User.__init__(self,submission.packages,user_id,submission.arch)

class PkgsListSystem(User):
    def __init__(self,pkgs_list_or_file,user_id=0):
        """
        Set initial parameters.
        """
        if type(pkgs_list_or_file).__name__ == "list":
            pkgs_list = filter_list_or_file
        elif type(pkgs_list_or_file).__name__ == "str":
            try:
                with open(pkgs_list_or_file) as pkgs_list_file:
                    pkgs_list = [line.split()[0] for line in pkgs_list_file if line.split()]
            except IOError:
                logging.critical("Could not open packages list file.")
                raise Error
        else:
            logging.debug("No packages provided for user profiling.")
            pkgs_list = []

        User.__init__(self,dict.fromkeys(pkgs_list,1),user_id)

class LocalSystem(User):
    """
    Extend the class User to consider the packages installed on the local
    system as the set of selected itens.
    """
    def __init__(self):
        """
        Set initial parameters.
        """
        item_score = {}
        dpkg_output = commands.getoutput('/usr/bin/dpkg --get-selections')
        for line in dpkg_output.splitlines():
            pkg = line.split('\t')[0]
            item_score[pkg] = 1
        self.user_id = "local-"+str(datetime.datetime.now())
        User.__init__(self,item_score)

    def no_auto_pkg_profile(self):
        """
        Return list of packages voluntarily installed.
        """
        cache = apt.Cache()
        old_profile_size = len(self.pkg_profile)
        for p in self.pkg_profile[:]:     #iterate list copy
            try:
                if cache.has_key(p):
                    pkg = cache[p]
                    if pkg.is_auto_installed:
                        self.pkg_profile.remove(p)
            except:
                logging.debug("Package not found in cache: %s" % p)
        profile_size = len(self.pkg_profile)
        logging.debug("No auto-intalled package profile: reduced packages \
                       profile size from %d to %d." %
                       (old_profile_size, profile_size))
        return self.pkg_profile
