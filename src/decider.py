#!/usr/bin/env python

import re
import xapian

from nltk.corpus import stopwords

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
        True if the package is not already installed and is not a lib or a doc.
        """
        pkg = doc.get_data()
        is_new = pkg not in self.pkgs_list
        is_new = is_new and ':' not in pkg

        if "kde" in pkg:
            return is_new and "kde" in self.pkgs_list
        if "gnome" in pkg:
            return is_new and "gnome" in self.pkgs_list

        if re.match(r'^lib.*', pkg) or re.match(r'.*doc$', pkg):
            return False

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

    def __init__(self):
        self.stop_words = set(stopwords.words('english'))

    def __call__(self, term):
        """
        Return true if the term or its stemmed version is part of a package
        description.
        """
        if term not in self.stop_words:
            return term.islower() and re.search('[a-z]', term)

        return False


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
