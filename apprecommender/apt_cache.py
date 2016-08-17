#!/usr/bin/env python

import apt
import xapian


class AptCache:

    DEFAULT_AXI_PATH = "/var/lib/apt-xapian-index/index"

    def __init__(self):
        self.axi = xapian.Database(AptCache.DEFAULT_AXI_PATH)

        self.cache = apt.Cache()

    def __getitem__(self, pkg_name):
        return self.get(pkg_name)

    def __contains__(self, pkg_name):
        return self.xapian_has_pkg(pkg_name) and pkg_name in self.cache

    def get(self, pkg_name):
        if self.xapian_has_pkg(pkg_name):
            return self.cache[pkg_name]

        raise KeyError("The cache has no package named '{}'".format(pkg_name))

    def xapian_has_pkg(self, pkg_name):
        term = 'XP' + pkg_name
        return self.axi.get_termfreq(term) > 0L
