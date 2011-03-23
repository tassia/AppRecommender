#!/usr/bin/python

#  data - python module for data sources classes and methods.
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

from error import Error

class Item:
    """
    Generic item definition.
    """

class Package(Item):
    """
    Definition of a GNU/Linux application as a recommender item.
    """
    def __init__(self,package_name):
        """
        Set initial attributes.
        """
        self.package_name  = package_name

def normalize_tags(string):
    """
    Substitute string characters : by _ and - by '.
    Examples:
        admin::package-management   ->   admin__package'management
        implemented-in::c++         ->   implemented-in__c++
    """
    return string.replace(':','_').replace('-','\'')

class Singleton(object):
    """
    Base class for inheritance of only-one-instance classes.
    Singleton design pattern.
    """
    def __new__(cls, *args, **kwargs):
        """
        Creates a new instance of the class only if none already exists.
        """
        if '_inst' not in vars(cls):
            cls._inst = object.__new__(cls)
        return cls._inst

class TagsXapianIndex(xapian.WritableDatabase,Singleton):
    """
    Data source for tags info defined as a singleton xapian database.
    """
    def __init__(self,cfg):
        """
        Set initial attributes.
        """
        self.path = os.path.expanduser(cfg.tags_index)
        self.db_path = os.path.expanduser(cfg.tags_db)
        self.debtags_db = debtags.DB()

        db = open(self.db_path)
        md5 = hashlib.md5()
        md5.update(db.read())
        self.db_md5 = md5.hexdigest()

        self.load_index(cfg.reindex)

    def load_db(self):
        """
        Load debtags database from the source file.
        """
        tag_filter = re.compile(r"^special::.+$|^.+::TODO$")
        try:
            db_file = open(self.db_path, "r")
            self.debtags_db.read(db_file,lambda x: not tag_filter.match(x))
        except IOError:  #FIXME try is not catching this
            logging.error("Could not load DebtagsDB from %s." % self.db_path)
            raise Error

    def relevant_tags_from_db(self,pkgs_list,qtd_of_tags):
        """
        Return most relevant tags considering a list of packages.
        """
        if not self.debtags_db.package_count():
            self.load_db()
        relevant_db = self.debtags_db.choose_packages(pkgs_list)
        relevance_index = debtags.relevance_index_function(self.debtags_db,
                                                           relevant_db)
        sorted_relevant_tags = sorted(relevant_db.iter_tags(),
                                      lambda a, b: cmp(relevance_index(a),
                                      relevance_index(b)))
        return normalize_tags(' '.join(sorted_relevant_tags[-qtd_of_tags:]))

    def load_index(self,reindex):
        """
        Load an existing debtags index.
        """
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
            self.new_index()

    def new_index(self):
        """
        Create a xapian index for debtags info based on 'debtags_db' and
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
            raise Error

        self.load_db()
        self.set_metadata("md5",self.db_md5)

        for pkg,tags in self.debtags_db.iter_packages_tags():
            doc = xapian.Document()
            doc.set_data(pkg)
            for tag in tags:
                doc.add_term(normalize_tags(tag))
            doc_id = self.add_document(doc)
            logging.debug("Indexing doc %d",doc_id)
