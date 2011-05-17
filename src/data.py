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
import gc
import re
import xapian
import axi
from debian import debtags
import logging
import hashlib

from error import Error
from singleton import Singleton

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

def load_debtags_db(db_path):
    """
    Load debtags database from the source file.
    """
    tag_filter = re.compile(r"^special::.+$|^.+::TODO$")
    try:
        db_file = open(db_path, "r")
        debtags_db = debtags.DB()
        debtags_db.read(db_file,lambda x: not tag_filter.match(x))
        db_file.close()
        return debtags_db
    except:
        logging.error("Could not load DebtagsDB from '%s'." % self.db_path)
        raise Error

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

        try:
            db_file = open(self.db_path)
        except IOError:
            logging.error("Could not load DebtagsDB from '%s'." % self.db_path)
            raise Error
        md5 = hashlib.md5()
        md5.update(db_file.read())
        self.db_md5 = md5.hexdigest()
        db_file.close()
        self.load_index(cfg.reindex)

#    def load_db(self):
#        """
#        Load debtags database from the source file.
#        """
#        tag_filter = re.compile(r"^special::.+$|^.+::TODO$")
#        try:
#            db_file = open(self.db_path, "r")
#            self.debtags_db.read(db_file,lambda x: not tag_filter.match(x))
#            db_file.close()
#        except:
#            logging.error("Could not load DebtagsDB from '%s'." % self.db_path)
#            raise Error

    def relevant_tags_from_db(self,pkgs_list,qtd_of_tags):
        """
        Return most relevant tags considering a list of packages.
        """
        if not self.debtags_db.package_count():
            self.debtags_db = load_debtags_db(self.db_path)
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
                logging.info("Could not open debtags index.")
                reindex =1

        if reindex:
            self.new_index()

    def new_index(self):
        """
        Create a xapian index for debtags info based on 'debtags_db' and
        place it at 'self.path'.
        """
        if not os.path.exists(self.path):
            os.makedirs(self.path)

        try:
            logging.info("Indexing debtags info from \'%s\'" %
                         self.db_path)
            logging.info("Creating new xapian index at \'%s\'" %
                         self.path)
            xapian.WritableDatabase.__init__(self,self.path,
                                             xapian.DB_CREATE_OR_OVERWRITE)
        except xapian.DatabaseError:
            logging.critical("Could not create xapian index.")
            raise Error

        self.debtags_db = load_debtags_db(self.db_path)
        self.set_metadata("md5",self.db_md5)

        for pkg,tags in self.debtags_db.iter_packages_tags():
            doc = xapian.Document()
            doc.set_data(pkg)
            for tag in tags:
                doc.add_term(normalize_tags(tag))
            doc_id = self.add_document(doc)
            logging.debug("Debtags Xapian: Indexing doc %d",doc_id)

class PopconXapianIndex(xapian.WritableDatabase,Singleton):
    """
    Data source for popcon submissions defined as a singleton xapian database.
    """
    def __init__(self,cfg):
        """
        Set initial attributes.
        """
        self.path = os.path.expanduser(cfg.popcon_index)
        self.popcon_dir = os.path.expanduser(cfg.popcon_dir)
        self.debtags_path = os.path.expanduser(cfg.tags_db)
        self.load_index()

    def parse_submission(self,submission_path,binary=1):
    	"""
    	Parse a popcon submission, generating the names of the valid packages
        in the vote.
    	"""
        submission = open(submission_path)
    	for line in submission:
            if not line.startswith("POPULARITY"):
                if not line.startswith("END-POPULARITY"):
                    data = line[:-1].split(" ")
                    if len(data) > 3:
                        if binary:
                            # every installed package has the same weight
                            yield data[2], 1
                        elif data[3] == '<NOFILES>':
                            # No executable files to track
                            yield data[2], 1
                        elif len(data) == 4:
                            # Recently used packages
                            yield data[2], 10
                        elif data[4] == '<OLD>':
                            # Unused packages
                            yield data[2], 3
                        elif data[4] == '<RECENT-CTIME>':
                            # Recently installed packages
                            yield data[2], 8

    def load_index(self):
        """
        Load an existing popcon index.
        """
        try:
            logging.info("Opening existing popcon xapian index at \'%s\'"
                          % self.path)
            xapian.Database.__init__(self,self.path)
        except xapian.DatabaseError:
            logging.info("Could not open popcon index.")
            self.new_index()

    def new_index(self):
        """
        Create a xapian index for popcon submissions at 'popcon_dir' and
        place it at 'self.path'.
        """
        if not os.path.exists(self.path):
            os.makedirs(self.path)
        debtags_db = load_debtags_db(self.debtags_path)

        try:
            logging.info("Indexing popcon submissions from \'%s\'" %
                         self.popcon_dir)
            logging.info("Creating new xapian index at \'%s\'" %
                         self.path)
            xapian.WritableDatabase.__init__(self,self.path,
                                             xapian.DB_CREATE_OR_OVERWRITE)
        except xapian.DatabaseError:
            logging.critical("Could not create popcon xapian index.")
            raise Error

        for root, dirs, files in os.walk(self.popcon_dir):
            for submission in files:
                submission_path = os.path.join(root, submission)
                doc = xapian.Document()
                doc.set_data(submission)
                logging.debug("Parsing popcon submission at \'%s\'" %
                              submission_path)
                for pkg, freq in self.parse_submission(submission_path):
                    doc.add_term(pkg,freq)
                    for tag in debtags_db.tags_of_package(pkg):
                        doc.add_term("XT"+tag,freq)
                doc_id = self.add_document(doc)
                logging.debug("Popcon Xapian: Indexing doc %d" % doc_id)
            # python garbage collector
        	gc.collect()
        # flush to disk database changes
        self.flush()
