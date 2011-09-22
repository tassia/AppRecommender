#!/usr/bin/env python

import os
import web
from web import form
import tempfile
import sys
import simplejson as json
import apt
import re
import socket

sys.path.insert(0,"/var/www/AppRecommender/src/")

from config import Config
from recommender import *
from user import *
from data import DebianPackage

import urllib

# avoid "RuntimeError: maximum recursion depth exceeded"
sys.setrecursionlimit(50000)

class Fake:
    def GET(self):
            return render_plain.fake()

class Index:
    def GET(self):
            return render.index()

class About:
    def GET(self):
        return render.about()

class Package:
    def GET(self, pkg_name):
        cfg = Config()
        pkg = DebianPackage(pkg_name) 
        pkg.load_details()
        return render_plain.package(pkg)

class AppRecommender:
    def __init__(self):
        logging.info("Setting up AppRecommender...")
        self.cfg = Config()
        self.rec = Recommender(self.cfg)
        self.requests_dir = "/var/www/AppRecommender/src/web/requests/"
        if not os.path.exists(self.requests_dir):
            os.makedirs(self.requests_dir)

    def POST(self):
        web_input = web.input(pkgs_file={})
        user_dir = tempfile.mkdtemp(prefix='',dir=self.requests_dir)
        user_id = user_dir.split("/")[-1]
        uploaded_file = os.path.join(user_dir,"uploaded_file")
        if web_input['pkgs_file'].value:
            lines = web_input['pkgs_file'].file.readlines()
            with open(uploaded_file, "w") as uploaded:
                uploaded.writelines(lines)
        with open(uploaded_file) as uploaded:
            if uploaded.readline().startswith('POPULARITY-CONTEST'):
                user = PopconSystem(uploaded_file,user_id)
            else:
                user = PkgsListSystem(uploaded_file,user_id)
        if len(user.pkg_profile) < 10:
            return render.error(["Could not extract profile from uploaded file. It must have at least 10 applications."],
                                 "/","RECOMMENDATION")
        else:
            self.rec.set_strategy("knn_eset")
            user.maximal_pkg_profile()
            prediction = self.rec.get_recommendation(user,12).get_prediction()
            logging.info("Prediction for user %s" % user.user_id)
            logging.info(str(prediction))
            recommendation = [result[0] for result in prediction]
            pkgs_details = []
            for pkg_name in recommendation:
                logging.info("Getting details of package %s" % pkg_name)
                pkg = DebianPackage(pkg_name)
                pkg.load_summary()
                pkgs_details.append(pkg)
            if pkgs_details:
                logging.info("Rendering recommendation...")
                return render.apprec(pkgs_details)
            else:
                return render.error(["No recommendation produced for the uploaded file."],"/","RECOMMENDATION")


# parsing json from screenshots - can be usefull in the future...
#    def _packages_attrs(self, recommends): #recommends is result of _recommends()
#        all_recommended_packages = []
#        recommended_pkgs_attrs = {}
#        json_file_path = 'static/json/screenshots.json' #FIXME: go to config file
#        json_file = open(json_file_path)
#        json_data = json.load(json_file)
#        for strategy, result in recommends.items():
#            all_recommended_packages.extend(result)
#        for pkg_attrs_dict in json_data['screenshots']:
#            if pkg_attrs_dict['name'] in all_recommended_packages:
#                recommended_pkgs_attrs[pkg_attrs_dict['name']] = pkg_attrs_dict
#        return recommended_pkgs_attrs

# to be used if it is not under apache
#def add_global_hook():
#    g = web.storage({"counter": "1"})
#    def _wrapper(handler):
#        web.ctx.globals = g
#        return handler()
#    return _wrapper

render = web.template.render('/var/www/AppRecommender/src/web/templates/', base='layout', globals={'hasattr':hasattr})
render_plain = web.template.render('/var/www/AppRecommender/src/web/templates/', globals={'hasattr':hasattr})

urls = ('/',                'Index',
        '/index',           'Index',
        '/apprec',	    'AppRecommender',
        '/support',         'Support',
        '/about',           'About',
        '/package/(.*)',    'Package'
       )

web.webapi.internalerror = web.debugerror

#if __name__ == "__main__":
cfg = Config()
app = web.application(urls, globals(), autoreload=False)
application = app.wsgifunc()

#   apprec = web.application(urls, globals())
#   apprec.add_processor(add_global_hook())
#   apprec.run()

