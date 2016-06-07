#!/usr/bin/env python

import apt
import commands
import data
import datetime
import os
import shutil
import xapian

from apprecommender.config import Config


class Initialize:

    AXI_SAMPLES = ['sample', 'filter']
    DEFAULT_AXI_PATH = "/var/lib/apt-xapian-index/index"
    EXCLUDED_TAGS = ['culture::', 'devel::lang', 'hardware::',
                     'implemented-in::', 'interface::', 'iso15924::',
                     'made-of::', 'network::', 'protocol::', 'role::',
                     'scope::', 'secteam::', 'special::', 'uitoolkit::',
                     'x11::', 'TODO']

    def __init__(self):
        self.config = Config()
        self.cache = apt.Cache()

    def get_tags(self):
        command = "cat /var/lib/debtags/vocabulary" \
                  "| grep 'Tag:'" \
                  "| egrep -v '%s'" \
                  "| awk '{print $2}'" % '|'.join(Initialize.EXCLUDED_TAGS)

        tags = commands.getoutput(command).splitlines()

        return tags

    def get_axipkgs(self, axi_tag='XP', axi_path=DEFAULT_AXI_PATH):
        axi = xapian.Database(axi_path)
        all_terms = set()

        user_pkgs = self.get_user_installed_packages()
        user_role_programs = self.get_user_role_programs(user_pkgs)

        for n in range(1, axi.get_lastdocid()):
            doc = 0
            try:
                doc = axi.get_document(n)
            except:
                pass
            if doc:
                xp_terms = None

                for t in doc.termlist():
                    if t.term.startswith(axi_tag):
                        xp_terms = t.term
                        break

                if xp_terms:
                    pkg_name = xp_terms.lstrip(axi_tag)
                    if pkg_name.startswith('M'):
                        pkg_name = pkg_name.lstrip('M')

                    if pkg_name not in self.cache:
                        continue

                    pkg = self.cache[pkg_name].candidate

                    if not pkg or not self.is_section_valid(pkg.section):
                        continue

                    pkg_dependencies = self.get_package_dependencies(pkg)
                    is_dep_installed = self.is_program_dependencies_installed(
                        pkg_dependencies, user_role_programs)

                    if is_dep_installed:
                        all_terms.add(pkg_name)

        return all_terms

    def is_section_valid(self, pkg_section):
        if pkg_section == 'doc':
            return False

        return True

    def is_valid_dependency(self, pkg_tags, pkg_section):
        tags_dep = 'role::program' in pkg_tags or 'devel::editor' in pkg_tags
        section_dep = pkg_section == 'interpreters'

        return tags_dep or section_dep

    def is_program_dependencies_installed(self, pkg_dependencies,
                                          user_role_programs):
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

        return len(dep_programs - user_role_programs) == 0

    def get_package_dependencies(self, pkg):
        return [dep[0].name for dep in pkg.dependencies]

    def get_user_installed_packages(self):
        manual_installed = commands.getoutput('apt-mark showmanual')
        return manual_installed.splitlines()

    def get_user_role_programs(self, user_pkgs):
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

    def indexer_axi(self, axi_sample, filters_path, terms=[]):
        axi_path = Initialize.DEFAULT_AXI_PATH
        axi = xapian.Database(axi_path)
        base_dir = self.config.base_dir

        begin_time = datetime.datetime.now()

        # axi sample based on the pkgs sample provided by command line
        if axi_sample is 'sample':
            with open(filters_path) as valid:
                pkgs_list = [line.strip() for line in valid]
            filter_str = 'axi_' + filters_path.split('/')[-1]

            print"\nIndexing packages on xapian"
            index = data.SampleAptXapianIndex(pkgs_list, axi,
                                              os.path.join(base_dir,
                                                           filter_str))
            print "Axi size: %d" % axi.get_doccount()
            print "Packages list length: %d" % len(pkgs_list)
            print "Sample index size: %d" % index.get_doccount()

        # axi filtered by terms provided by command line
        if axi_sample is "filter":
            terms_str = "_".join([t.split("::")[-1] for t in terms])
            index = data.FilteredXapianIndex(terms, axi,
                                             os.path.join(base_dir,
                                                          "axi_" + terms_str))
            print "Axi size: %d" % axi.get_doccount()
            print "Terms filter: %s" % terms
            print "Filtered index size: %d" % index.get_doccount()

        end_time = datetime.datetime.now()
        print "Indexing completed at %s" % end_time
        delta = end_time - begin_time
        print "Time elapsed: %d seconds." % delta.seconds

    def prepare_data(self):
        if os.path.exists(self.config.base_dir):
            shutil.rmtree(self.config.base_dir)
        os.makedirs(self.config.base_dir)
        os.makedirs(self.config.filters_dir)

        tags = self.get_tags()
        tags_path = "{}/debtags".format(self.config.filters_dir)
        self.save_list(tags, tags_path)

        pkgs = self.get_axipkgs()
        pkgs_path = "{}/desktopapps".format(self.config.filters_dir)
        self.save_list(pkgs, pkgs_path)

        self.indexer_axi('sample', pkgs_path)

    def get_role_program_pkgs(self):
        command = "cat /var/lib/debtags/package-tags | " \
                  "grep 'role::program' | " \
                  "awk -F: '{ print $1}'"
        pkgs = commands.getoutput(command).splitlines()

        return pkgs

    def save_list(self, elements, path):
        with open(path, 'w') as text:
            text.write('\n'.join(elements) + '\n')
