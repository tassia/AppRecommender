#!/usr/bin/env python

import commands
import data
import datetime
import os
import xapian
import shutil

from config import Config


class Initialize:

    TAGS = ['XP', 'XT', 'Z']
    AXI_SAMPLES = ['sample', 'filter']
    DEFAULT_AXI_PATH = "/var/lib/apt-xapian-index/index"
    EXCLUDED_TAGS = ['culture::', 'devel::lang', 'hardware::',
                     'implemented-in::', 'interface::', 'iso15924::',
                     'made-of::', 'network::', 'protocol::', 'role::',
                     'scope::', 'secteam::', 'special::', 'uitoolkit::',
                     'x11::', 'TODO']

    def __init__(self):
        pass

    def get_tags(self):
        command = "cat /var/lib/debtags/vocabulary" \
                  "| grep 'Tag:'" \
                  "| egrep -v '%s'" \
                  "| awk '{print $2}'" % '|'.join(Initialize.EXCLUDED_TAGS)

        tags = commands.getoutput(command).splitlines()

        return tags

    def get_axipkgs(self, axi_tag=TAGS[0], axi_path=DEFAULT_AXI_PATH):
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
                    xp_terms = xp_terms.lstrip(axi_tag)
                    if xp_terms.startswith('M'):
                        xp_terms = xp_terms.lstrip('M')

                    all_terms.add(xp_terms.lstrip(axi_tag))

        return all_terms

    def indexer_axi(self, axi_sample, filters_path, terms=[]):
        axi_path = Initialize.DEFAULT_AXI_PATH
        axi = xapian.Database(axi_path)
        base_dir = Config().base_dir

        begin_time = datetime.datetime.now()

        # axi sample based on the pkgs sample provided by command line
        if axi_sample is 'sample':
            with open(filters_path) as valid:
                pkgs_list = [line.strip() for line in valid]
            filter_str = 'axi_' + filters_path.split('/')[-1]

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
        config = Config()

        shutil.rmtree(config.base_dir)
        os.makedirs(config.base_dir)
        os.makedirs(config.filters_dir)

        tags = self.get_tags()
        tags_path = "{}/debtags".format(config.filters_dir)
        with open(tags_path, 'w') as text:
            for tag in tags:
                text.write(tag + '\n')

        pkgs = self.get_axipkgs()
        pkgs_path = "{}/desktopapps".format(config.filters_dir)
        with open(pkgs_path, 'w') as text:
            for pkg in pkgs:
                text.write(pkg + '\n')

        self.indexer_axi('sample', pkgs_path)
