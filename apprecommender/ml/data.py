from os import path
from os import makedirs

import apt
import calendar
import pickle
import time
import re
import xapian
import Stemmer

import apprecommender.data_classification as data_cl

from apprecommender.ml.pkg_time import PkgTime
from apprecommender.config import Config
from apprecommender.decider import FilterTag, FilterDescription


class MachineLearningData():

    XAPIAN_DATABASE_PATH = path.expanduser(
        '~/.app-recommender/axi_desktopapps/')
    USER_DATA_DIR = Config().user_data_dir
    BASE_DIR = Config().base_dir

    PKG_DATA_PATH = USER_DATA_DIR + 'pkg_data.txt'

    PKGS_CLASSIFICATIONS = USER_DATA_DIR + 'pkgs_classifications.txt'
    MACHINE_LEARNING_TERMS = USER_DATA_DIR + 'machine_learning_terms.txt'
    MACHINE_LEARNING_DEBTAGS = USER_DATA_DIR + 'machine_learning_debtags.txt'
    MACHINE_LEARNING_TRAINING = USER_DATA_DIR + 'machine_learning_training.txt'

    def __init__(self):
        self.axi = xapian.Database(MachineLearningData.XAPIAN_DATABASE_PATH)
        self.stemmer = Stemmer.Stemmer('english')

        valid_tags = []
        with open(path.join(Config().filters_dir, "debtags")) as tags:
            valid_tags = [line.strip() for line in tags
                          if not line.startswith("#")]
        self.filter_tag = FilterTag(valid_tags)
        self.filter_description = FilterDescription()

    def create_data(self, labels):
        if not path.exists(MachineLearningData.USER_DATA_DIR):
            makedirs(MachineLearningData.USER_DATA_DIR)

        pkgs = self.get_pkgs_classification(data_cl.linear_percent_function,
                                            labels)

        cache = apt.Cache()

        terms_name = self.get_terms_for_all_pkgs(cache, pkgs.keys())
        debtags_name = self.get_debtags_for_all_pkgs(self.axi, pkgs.keys())

        debtags_name = self.filter_debtags(debtags_name)
        debtags_name = sorted(debtags_name)
        terms_name = self.filter_terms(terms_name)
        terms_name = sorted(terms_name)

        pkgs_classifications = (
            self.get_pkgs_table_classification(self.axi, pkgs,
                                               cache, debtags_name,
                                               terms_name))

        self.save_pkg_data(terms_name,
                           MachineLearningData.MACHINE_LEARNING_TERMS)
        self.save_pkg_data(debtags_name,
                           MachineLearningData.MACHINE_LEARNING_DEBTAGS)
        self.save_pkg_data(pkgs_classifications,
                           MachineLearningData.PKGS_CLASSIFICATIONS)

        return pkgs_classifications

    def get_pkgs_classification(self, percent_function, labels):
        pkgs_percent = {}
        pkgs_classification = {}
        time_now = calendar.timegm(time.gmtime())
        pkg_time = PkgTime()
        pkg_data = pkg_time.get_package_data()

        for name, time_values in pkg_data.iteritems():
            modify, access = time_values

            pkgs_percent[name] = percent_function(modify, access, time_now)
            # pkgs_percent[name] = access

        pkgs = pkgs_percent.keys()
        pkgs = sorted(pkgs, key=lambda pkg: pkgs_percent[pkg])
        pkgs = list(reversed(pkgs))

        size = len(pkgs) / len(labels)
        for index, label in enumerate(labels):
            index_begin = size * index
            index_end = index_begin + size
            classifications = dict.fromkeys(pkgs[index_begin:index_end], label)
            pkgs_classification.update(classifications)

        index_begin = size * len(labels)
        if index_begin < len(labels):
            classifications = dict.fromkeys(pkgs[index_begin], label[-1])
            pkgs_classification.update(classifications)

        return pkgs_classification

    def get_pkg_data(self, axi, pkg_name, data_type):
        pkg_name = 'XP' + pkg_name

        query = xapian.Query(xapian.Query.OP_OR, [pkg_name])
        enquire = xapian.Enquire(axi)
        enquire.set_query(query)

        mset = enquire.get_mset(0, 10)

        pkg_info = []
        for pkg in mset:
            for term in axi.get_document(pkg.docid).termlist():

                pkg_term = term.term

                if pkg_term.startswith(data_type):
                    pkg_info.append(pkg_term[len(data_type):])
                elif data_type == 'term':
                    if pkg_term[0].islower():
                        pkg_info.append(pkg_term)

        return pkg_info

    def get_pkg_debtags(self, axi, pkg_name):
        return self.get_pkg_data(axi, pkg_name, 'XT')

    def get_pkg_terms(self, cache, pkg_name):
        description = cache[pkg_name].candidate.description.strip()
        description = re.sub('[^a-zA-Z]', ' ', description)

        tokens = description.lower().split()
        stems = [self.stemmer.stemWord(token) for token in tokens
                 if self.filter_description(token)]

        return stems

    def get_pkg_section(self, cache, pkg_name):
        return cache[pkg_name].section

    def get_debtags_name(self, file_path):
        with open(file_path, 'r') as text:
            debtags_name = [debtag.strip() for debtag in text]

        return debtags_name

    def create_row_table_list(self, labels_name, pkg_elements):
        row_list = []

        for debtag in labels_name:
            row_list.append(1 if debtag in pkg_elements else 0)

        return row_list

    def get_terms_for_all_pkgs(self, cache, pkgs):
        pkg_terms = set()
        for pkg in pkgs:
            pkg_terms = pkg_terms | set(self.get_pkg_terms(cache, pkg))

        return pkg_terms

    def get_debtags_for_all_pkgs(self, axi, pkgs):
        pkg_debtags = set()
        for pkg in pkgs:
            pkg_debtags = pkg_debtags | set(self.get_pkg_debtags(axi, pkg))

        return pkg_debtags

    def filter_terms(self, terms):
        filtered_terms = []
        for term in terms:
            if self.filter_description(term):
                filtered_terms.append(term)

        return filtered_terms

    def filter_debtags(self, debtags):
        filtered_debtags = []
        for tag in debtags:
            if self.filter_tag('XT' + tag):
                filtered_debtags.append(tag)

        return filtered_debtags

    def get_pkgs_table_classification(self, axi, pkgs, cache,
                                      debtags_name, terms_name):
        pkgs_classification = {}

        for key, value in pkgs.iteritems():

            pkgs_classification[key] = []

            debtags = self.get_pkg_debtags(axi, key)
            debtags = self.create_row_table_list(debtags_name, debtags)
            pkgs_classification[key].extend(debtags)

            terms = self.get_pkg_terms(cache, key)
            terms = self.create_row_table_list(list(terms_name), terms)
            pkgs_classification[key].extend(terms)

            pkgs_classification[key].append(value)

        return pkgs_classification

    def save_pkg_data(self, pkg_data, file_path):
        with open(file_path, 'wb') as text:
            pickle.dump(pkg_data, text)
