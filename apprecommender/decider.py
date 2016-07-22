#!/usr/bin/env python

import apt
import commands
import re
import xapian

from sklearn.feature_extraction.stop_words import ENGLISH_STOP_WORDS


class PkgInitDecider():
    """
    Class used to decide if a package can be considered to recommended to an
    user or not.
    """

    INVALID_PREFIXES = {'ruby', 'python', 'python3', 'golang', 'gir',
                        'texlive'}
    INVALID_SUFFIXES = {'examples', 'dbg', 'data', 'dev', 'utils', 'common',
                        'fonts', 'png'}

    def __init__(self):
        self.cache = apt.Cache()
        self.user_role_programs = self.get_user_role_programs()

    def is_in_apt_cache(self, pkg):
        return pkg in self.cache

    def get_package_dependencies(self, pkg):
        return [dep[0].name for dep in pkg.dependencies]

    def get_user_installed_packages(self):
        manual_installed = commands.getoutput('apt-mark showmanual')
        return manual_installed.splitlines()

    def get_user_role_programs(self):
        user_pkgs = self.get_user_installed_packages()
        user_programs = set()

        for pkg in user_pkgs:
            if pkg in self.cache:
                pkg_candidate = self.cache[pkg].candidate
                pkg_tags = pkg_candidate.record.get('Tag', None)

                if not pkg_tags:
                    continue

                if 'role::program' in pkg_tags:
                    user_programs.add(pkg)

        return user_programs

    def is_valid_dependency(self, pkg_tags, pkg_section):
        tags_dep = 'role::program' in pkg_tags or 'devel::editor' in pkg_tags
        section_dep = pkg_section == 'interpreters'

        return tags_dep or section_dep

    def is_program_dependencies_installed(self, pkg):
        pkg_dependencies = self.get_package_dependencies(pkg)
        dep_programs = set()

        for dep in pkg_dependencies:
            if dep in self.cache:
                pkg = self.cache[dep].candidate

                if pkg is not None:
                    pkg_tags = pkg.record.get('Tag', None)
                    pkg_section = pkg.section

                    if pkg_tags is None:
                        continue

                    is_valid_dependency = self.is_valid_dependency(
                        pkg_tags, pkg_section)

                    if is_valid_dependency:
                        dep_programs.add(dep)

        return len(dep_programs - self.user_role_programs) == 0

    def is_pkg_a_prefix_or_suffix(self, pkg):
        splited_pkg = pkg.split('-')

        if len(splited_pkg) == 1:
            return False

        pkg_prefix = splited_pkg[0]
        for prefix in PkgInitDecider.INVALID_PREFIXES:
            if pkg_prefix.startswith(prefix):
                return True

        for suffix in PkgInitDecider.INVALID_SUFFIXES:
            if (splited_pkg[-1].endswith(suffix) or
               splited_pkg[-2].endswith(suffix)):
                return True

        return False

    def __call__(self, pkg):
        if not self.is_in_apt_cache(pkg):
            return False

        pkg_candidate = self.cache[pkg].candidate

        valid = (pkg_candidate and
                 self.is_program_dependencies_installed(pkg_candidate) and
                 not self.is_pkg_a_prefix_or_suffix(pkg))

        return valid


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
        xapian.ExpandDecider.__init__(self)
        self.stop_words = ENGLISH_STOP_WORDS

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
