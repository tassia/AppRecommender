#!/usr/bin/env python

import os
import web
from web import form
import tempfile
import sys
import simplejson as json
import apt
import re

sys.path.insert(0,"../")

from config import *
from recommender import *
from user import *

import urllib

class Index:
    def GET(self):
        return render.survey_index()

class About:
    def GET(self):
        return render.about()

class Thanks:
    def POST(self):
        web_input = web.input()
        user_id = web_input['user_id'].encode('utf8')
        with open("./submissions/%s/ident" % user_id,'w') as ident:
            for key in ["name","email","country","public","comments"]:
                if web_input.has_key(key):
                    ident.write("%s: %s\n" % (key,web_input[key]))
        return render.thanks_id()

class Package:
    def GET(self, pkg):
        result = self.get_details_from_dde(pkg)
        return render_plain.package(result)

    def get_details_from_dde(self, pkg):
        json_source = Config().dde_url % pkg
        json_data = json.load(urllib.urlopen(json_source))
        # parse tags
        tags = self._debtags_list_to_dict(json_data['r']['tag'])
        json_data['r']['tag'] = tags
        # format long description
        json_data['r']['long_description'] = json_data['r']['long_description'].replace(' .\n','').replace('\n','<br />')
        return json_data['r']

    def _debtags_list_to_dict(self, debtags_list):
        """ in:
        	['use::editing',
                'works-with-format::gif',
                'works-with-format::jpg',
                'works-with-format::pdf']
            out:
                {'use': [editing],
                'works-with-format': ['gif', 'jpg', 'pdf']'
                }
        """
        debtags = {}
        subtags = []
        for tag in debtags_list:
            match = re.search(r'^(.*)::(.*)$', tag)
            if not match:
                log.error("Could not parse debtags format from tag: %s", tag)
            facet, subtag = match.groups()
            subtags.append(subtag)
            if facet not in debtags:
               debtags[facet] = subtags
            else:
               debtags[facet].append(subtag)
            subtags = []
        return debtags

class Request:
    def __init__(self,web_input,submissions_dir,user_id=0,pkgs_list=0):
        self.strategy = ""
        print "Request from user",user_id
        if user_id:
            self.user_id = user_id
            self.outputdir = os.path.join(submissions_dir,user_id)
        else:
            self.outputdir = tempfile.mkdtemp(prefix='',dir=submissions_dir)
            print ("created dir %s" % self.outputdir)
            self.user_id = self.outputdir.lstrip(submissions_dir)

        if pkgs_list:
            self.pkgs_list = pkgs_list
        else:
            self.pkgs_list = []
            if web_input['pkgs_file'].value:
                f = open(self.outputdir + "/packages_list", "wb")
                lines = web_input['pkgs_file'].file.readlines()
                # popcon submission format
                if lines[0].startswith('POPULARITY-CONTEST'):
                    del lines[0]
                    del lines[-1]
                    package_name_field = 2
                else:
                    package_name_field = 0
                for line in lines:
                    self.pkgs_list.append(line.split()[package_name_field])
                for pkg in self.pkgs_list:
                    f.write(pkg+'\n')
                f.close()

    def __str__(self):
        return "Request %s:\n %s" % (self.user_id,str(self.pkgs_list))

    def validates(self):
        self.errors = []
        if not self.pkgs_list:
            self.errors.append("No packages list provided.")
        if self.errors:
            return False
        return True

class Save:
    def POST(self):
        web_input = web.input()
        print web_input
        user_id = web_input['user_id'].encode('utf8')
        with open("./submissions/%s/packages_list" % user_id) as packages_list:
            pkgs_list = [line.strip() for line in packages_list.readlines()]
        strategy = web_input['strategy']
        print user_id,strategy,pkgs_list
        output_dir = "./submissions/%s/%s/" % (user_id,strategy)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        evaluations = {}
        evaluations["poor"] = []
        evaluations["good"] = []
        evaluations["surprising"] = []
        for key, value in web_input.items():
            if key.startswith("evaluation-"):
                evaluations[value.encode('utf8')].append(key.lstrip("evaluation-"))
        for key,value in evaluations.items():
            with open(output_dir+key,'w') as output:
                for item in value:
                    output.write(item+"\n")
        with open(output_dir+"report",'w') as report:
            report.write("# User: %s\n# Strategy: %s\n# TP FP\n%d %d\n" %
                         (user_id,strategy,
                          len(evaluations["good"])+len(evaluations["surprising"]),
                          len(evaluations["poor"])))
        if web_input.has_key('strategy_button'):
            return Survey().POST()
        elif web_input.has_key('finish_button'):
            return render.thanks(user_id)
        else:
            return render.survey_index()

class Survey:
    def __init__(self):
        self.strategies = ["cb","cbd","cbt"]
        self.rec = Recommender(Config())
        self.submissions_dir = "./submissions/"
        if not os.path.exists(self.submissions_dir):
            os.makedirs(self.submissions_dir)

    def POST(self):
        web_input = web.input(pkgs_file={})
        print "WEB_INPUT",web_input
        # If it is not the first strategy round, save the previous evaluation
        if not web_input.has_key('user_id'):
            request = Request(web_input,self.submissions_dir)
        else:
            user_id = web_input['user_id'].encode('utf8')
            print "Continue", user_id
            with open("./submissions/%s/packages_list" % user_id) as packages_list:
                pkgs_list = [line.strip() for line in packages_list.readlines()]
            request = Request(web_input,self.submissions_dir,user_id,pkgs_list)
        if not request.validates():
            return render.error(request.errors)
        else:
            user = User(dict.fromkeys(request.pkgs_list,1),request.user_id)
            user.maximal_pkg_profile()
            results = dict()
            old_strategies = [dirs for root, dirs, files in
                              os.walk(os.path.join(self.submissions_dir,
                                                   request.user_id))]
            print "OLD Strategies", old_strategies[0]
            strategies = [s for s in self.strategies if s not in old_strategies[0]]
            print "LEFT",strategies
            if not strategies:
                return render.thanks(user_id)
            request.strategy = random.choice(strategies)
            print "selected",request.strategy
            self.rec.set_strategy(request.strategy)
            prediction = self.rec.get_recommendation(user,10).get_prediction()
            print prediction
            recommendation = [result[0] for result in prediction]
            pkg_summaries = {}
            pkg_details = []
            cache = apt.Cache()
            for pkg in recommendation:
                try:
                    pkg_details.append(Package().get_details_from_dde(pkg))
                    pkg_summaries[pkg] = cache[pkg].candidate.summary
                except:
                    pkg_summaries[pkg] = ""
            return render.survey(pkg_details, request)

def add_global_hook():
    g = web.storage({"counter": "1"})
    def _wrapper(handler):
        web.ctx.globals = g
        return handler()
    return _wrapper

render = web.template.render('templates/', base='layout')
render_plain = web.template.render('templates/')

urls = ('/',   		        'Index',
        '/survey',          'Survey',
        '/apprec',          'Survey',
        '/thanks',   		'Thanks',
        '/save',   		    'Save',
        '/thanks',   		'Thanks',
        '/about',           'About',
        '/package/(.*)',  	'Package'
       )

web.webapi.internalerror = web.debugerror

if __name__ == "__main__":
   apprec = web.application(urls, globals())
   apprec.add_processor(add_global_hook())
   apprec.run()

