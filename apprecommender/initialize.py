#!/usr/bin/env python

import apt
import commands
import data
import datetime
import os
import shutil
import xapian

from apprecommender.config import Config
from apprecommender.decider import PkgInitDecider


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
        self.pkg_init_decider = PkgInitDecider()

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

                    if self.pkg_init_decider(pkg_name):
                        all_terms.add(pkg_name)

        return all_terms

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

        try:
            if os.path.exists(self.config.base_dir):
                if os.path.exists(self.config.user_data_dir):
                    shutil.rmtree(self.config.user_data_dir)

                if os.path.exists(self.config.axi_desktopapps):
                    shutil.rmtree(self.config.axi_desktopapps)

                if os.path.exists(self.config.filters_dir):
                    shutil.rmtree(self.config.filters_dir)

            os.makedirs(self.config.filters_dir)
        except OSError:
            raise

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
