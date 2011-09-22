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

import logging
from config import Config
from recommender import *
from user import *
from data import DebianPackage

import urllib

# avoid "RuntimeError: maximum recursion depth exceeded"
sys.setrecursionlimit(50000)

class Index:
    def GET(self):
        return render.index_survey()

class About:
    def GET(self):
        return render.about_survey()

class Thanks:
    def POST(self):
        web_input = web.input()
        user_id = web_input['user_id'].encode('utf8')
        with open("/var/www/AppRecommender/src/web/submissions/%s/personal" % user_id,'w') as ident:
            for key in ["name","email","comments"]:
                if web_input.has_key(key):
                    ident.write("# %s\n%s\n" % (key.capitalize(),web_input[key].encode("utf-8")))
        return render.thanks_id()

class Fake:
    def GET(self):
        return render_plain.fake()

class Save:
    def POST(self):
        web_input = web.input()
        logging.info("Saving user evaluation...")
        logging.info(web_input)
        user_id = web_input['user_id'].encode('utf8')
        with open("/var/www/AppRecommender/src/web/submissions/%s/uploaded_file" % user_id) as packages_list:
            pkgs_list = [line.strip() for line in packages_list.readlines()]
        strategy = web_input['strategy']
        logging.debug("Saving evaluation for user %s, strategy %s and packages..."
                      % (user_id,strategy))
        logging.debug(pkgs_list)
        evaluations = {}
        evaluations["poor"] = []
        evaluations["good"] = []
        evaluations["surprising"] = []
        for key, value in web_input.items():
            if key.startswith("evaluation-"):
                evaluations[value.encode('utf8')].append(key.lstrip("evaluation-"))
        output_dir = ("/var/www/AppRecommender/src/web/submissions/%s/%s/" % (user_id,strategy))
        for key,value in evaluations.items():
            with open(os.path.join(output_dir,key),'w') as output:
                for item in value:
                    output.write(item+"\n")
        with open(os.path.join(output_dir,"report"),'w') as report:
            report.write("# User: %s\n# Strategy: %s\n# TP FP S\n%d %d %d\n" %
                         (user_id,strategy,
                          len(evaluations["good"])+len(evaluations["surprising"]),
                          len(evaluations["poor"]),len(evaluations["surprising"])))
            if web_input.has_key("comments"):
                report.write("# Comments\n%s\n" % web_input['comments'].encode("utf-8"))
        if web_input.has_key('continue_button'):
            return Survey().POST()
        elif web_input.has_key('finish_button'):
            return render.thanks(user_id)
        else:
            return render.index_survey()

class Request:
    def __init__(self,web_input,submissions_dir):
        self.strategy = ""
        # Check if it is first round
        if web_input.has_key('user_id'):
            self.user_id = web_input['user_id'].encode('utf8')
            self.user_dir = os.path.join(submissions_dir, self.user_id)
            logging.info("New round for user %s" % self.user_id)
        else:
            self.user_dir = tempfile.mkdtemp(prefix='',dir=submissions_dir)
            self.user_id = self.user_dir.split("/")[-1]
            logging.info("Request from user %s" % self.user_id)
            logging.debug("Created dir %s" % self.user_dir)
        uploaded_file = os.path.join(self.user_dir,"uploaded_file")
        if not os.path.exists(uploaded_file):
            if web_input['pkgs_file'].value:
                lines = web_input['pkgs_file'].file.readlines()
                with open(uploaded_file, "w") as uploaded:
                    uploaded.writelines(lines)
        with open(uploaded_file) as uploaded:
            if uploaded.readline().startswith('POPULARITY-CONTEST'):
                self.user = PopconSystem(uploaded_file,self.user_id)
            else:
                self.user = PkgsListSystem(uploaded_file,self.user_id)

    def __str__(self):
        return "Request %s:\n %s" % (self.user.user_id,
                                     str(self.user.pkg_profile))

    def validates(self):
        self.errors = []
        if not self.user.pkg_profile:
            self.errors.append("No packages list provided.")
        if self.errors:
            return False
        return True

class Survey:
    def __init__(self):
        logging.info("Setting up survey...")
        self.cfg = Config()
        self.rec = Recommender(self.cfg)
        self.submissions_dir = "/var/www/AppRecommender/src/web/submissions/"
        if not os.path.exists(self.submissions_dir):
            os.makedirs(self.submissions_dir)

    def POST(self):
        web_input = web.input(pkgs_file={})
        logging.debug("Survey web_input %s" % str(web_input))
        self.strategies = ["cb","cbh","cb_eset","cbh_eset",
                           "knn","knn_eset","knn_plus",
                           "knnco","knnco_eset"]
        request = Request(web_input,self.submissions_dir)
        if len(request.user.pkg_profile)<10:
            return render.error(["Could not extract profile from uploaded file. It must have at least 10 applications."],
                                 "/survey/","START")
        else:
            ## Check the remaining strategies and select a new one
            #old_strategies = [dirs for root, dirs, files in
            #                  os.walk(os.path.join(self.submissions_dir,
            #                                       request.user_id))]
            #if old_strategies:
            #    strategies = [s for s in self.strategies if s not in old_strategies[0]]
            #    logging.info("Already used strategies %s" % old_strategies[0])
            #else:
            #    strategies = self.strategies
            #if not strategies:
            #    return render.thanks(request.user_id)
            #request.strategy = random.choice(strategies)
            #logging.info("Selected \'%s\' from %s" % (request.strategy,strategies))
            ## Get recommendation
            #self.rec.set_strategy(request.strategy)
            request.strategy = self.set_rec_strategy(request.user_id)
            prediction = self.rec.get_recommendation(request.user,10).get_prediction()
            logging.info("Prediction for user %s" % request.user_id)
            logging.info(str(prediction))
            strategy_dir = os.path.join(request.user_dir,request.strategy)
            os.makedirs(strategy_dir)
            with open(os.path.join(strategy_dir,"prediction"),"w") as prediction_file:
                for pkg,rating in prediction:
                    prediction_file.write("%s %f.2\n" % (pkg,rating))
            logging.debug("Saved %s/%s prediction to file" %
                          (request.user_id,request.strategy))
            recommendation = [result[0] for result in prediction]

            # Load packages details
            pkgs_details = []
            for pkg_name in recommendation:
                logging.info("Getting details of package %s" % pkg_name)
                pkg = DebianPackage(pkg_name)
                pkg.load_details()
                pkgs_details.append(pkg)

            if pkgs_details:
                logging.info("Rendering survey slide...")
                return render.survey(pkgs_details, request)
            else:
                return render.error(["No recommendation produced for the uploaded file."],"/survey/","START")

    def set_rec_strategy(self,user_id):
        # Check the remaining strategies and select a new one
        old_strategies = [dirs for root, dirs, files in
                          os.walk(os.path.join(self.submissions_dir,
                                               user_id))]
        if old_strategies:
            strategies = [s for s in self.strategies if s not in old_strategies[0]]
            logging.info("Already used strategies %s" % old_strategies[0])
        else:
            strategies = self.strategies
        if not strategies:
            return render.thanks(request.user_id)
        selected_strategy = random.choice(strategies)
        logging.info("Selected \'%s\' from %s" % (selected_strategy,strategies))
        k=50
        n=50
        if selected_strategy == "cb":
            pass
        if selected_strategy == "cbh":
            pass
        if selected_strategy == "cb_eset":
            pass
        if selected_strategy == "cbh_eset":
            pass
        if selected_strategy == "knn":
            pass
        if selected_strategy == "knn_eset":
            pass
        if selected_strategy == "knn_plus":
            pass
        if selected_strategy == "knnco":
            pass
        if selected_strategy == "knnco_eset":
            pass
        self.rec.set_strategy(selected_strategy,k,n)
        return selected_strategy

#def add_global_hook():
#    g = web.storage({"counter": "1"})
#    def _wrapper(handler):
#        web.ctx.globals = g
#        return handler()
#    return _wrapper

render = web.template.render('/var/www/AppRecommender/src/web/templates/', base='layout', globals={'hasattr':hasattr})

urls = ('',                'Index',
        '/', 	           'Index',
        '/survey',         'Survey',
        '/apprec',         'Survey',
        '/thanks',   	   'Thanks',
        '/save',   	   'Save',
        '/about',          'About',
       )

web.webapi.internalerror = web.debugerror

cfg = Config()
app = web.application(urls, globals(), autoreload=False)
application = app.wsgifunc()
