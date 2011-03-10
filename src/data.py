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

import os
import sys
import re
import xapian
import axi
from debian import debtags
import logging
import hashlib

class Item:
    """  """

class Package(Item):
    """  """
    def __init__(self,package_name):
        """  """
        self.package_name  = package_name

    def load_package_info(self):
        """  """
        print "debian pkg",self.id

def normalize_tags(string):
    """
    Normalize tag string so that it can be indexed and retrieved.
    """
    return string.replace(':','_').replace('-','\'')

class Singleton(object):
    def __new__(cls, *args, **kwargs):
        if '_inst' not in vars(cls):
            cls._inst = object.__new__(cls)
        return cls._inst

class DebtagsDB(debtags.DB,Singleton):
    def __init__(self,path):
        self.path = path

    def load(self):
        tag_filter = re.compile(r"^special::.+$|^.+::TODO$")
        try:
            self.read(open(self.path, "r"), lambda x: not tag_filter.match(x))
            return 1
        except IOError:
            logging.error("IOError: could not open debtags file \'%s\'" %
                          self.path)
            return 0

    def get_relevant_tags(self,pkgs_list,qtd_of_tags):
        """
        Return most relevant tags considering a list of packages.
        """
        relevant_db = self.choose_packages(pkgs_list)
        relevance_index = debtags.relevance_index_function(self,relevant_db)
        sorted_relevant_tags = sorted(relevant_db.iter_tags(),
                                      lambda a, b: cmp(relevance_index(a),
                                      relevance_index(b)))
        return normalize_tags(' '.join(sorted_relevant_tags[-qtd_of_tags:]))

class DebtagsIndex(xapian.WritableDatabase,Singleton):
    def __init__(self,path):
        self.path = path
        self.db_md5 = 0

    def load(self,debtags_db,reindex=0):
        """
        Load an existing debtags index.
        """
        self.debtags_db = debtags_db
        db = open(debtags_db.path)
        md5 = hashlib.md5()
        md5.update(db.read())
        self.db_md5 = md5.hexdigest()

        if not reindex:
            try:
                logging.info("Opening existing debtags xapian index at \'%s\'"
                              % self.path)
                xapian.Database.__init__(self,self.path)
                md5 = self.get_metadata("md5")
                if not md5 == self.db_md5:
                    logging.info("Index must be updated.")
                    reindex = 1
            except xapian.DatabaseError:
                logging.info("Could not open index.")
                reindex =1

        if reindex:
            self.create_index(debtags_db)

    def create_index(self,debtags_db):
        """
        Create a xapian index for debtags info based on file 'debtags_db' and
        place it at 'index_path'.
        """
        if not os.path.exists(self.path):
            os.makedirs(self.path)

        try:
            logging.info("Creating new xapian index for debtags at \'%s\'" %
                         self.path)
            xapian.WritableDatabase.__init__(self,self.path,
                                             xapian.DB_CREATE_OR_OVERWRITE)
        except xapian.DatabaseError:
            logging.critical("Could not create xapian index.")
            exit(1)

        self.set_metadata("md5",self.db_md5)
        for pkg,tags in debtags_db.iter_packages_tags():
            doc = xapian.Document()
            doc.set_data(pkg)
            for tag in tags:
                doc.add_term(normalize_tags(tag))
            doc_id = self.add_document(doc)
            logging.debug("Indexing doc %d",doc_id)
