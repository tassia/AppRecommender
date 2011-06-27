#!/usr/bin/env python

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

class FeedbackForm(form.Form):
    def __init__(self,selected_strategies):
        desc_dict = {"cb": "Content-based", "cbt": "Content-based",
                     "cbd": "Content-based", "col": "Collaborative",
                     "hybrid": "Hybrib"}
        fields = []
        for strategy in selected_strategies:
            fields.append(form.Radio(desc_dict[strategy],
                [('1','1 '),('2','2 '),('3','3'),('4','4 '),('5','5')]))
        form.Form.__init__(self, *fields, validators = [])

class Index:
    def GET(self):
        return render.index()

class About:
    def GET(self):
        return render.about()

class Thanks:
    def POST(self):
        return render.thanks()

class Package:
    def GET(self, pkg):
        json_source = "http://dde.debian.net/dde/q/udd/packages/all/%s?t=json" % pkg #FIXME: url goes to config
        json_data = json.load(urllib.urlopen(json_source))
        # parsing tags:
        tags = self._debtags_list_to_dict(json_data['r']['tag'])
        json_data['r']['tag'] = tags
        # formatting long description
        json_data['r']['long_description'] = json_data['r']['long_description'].replace(' .\n','').replace('\n','<br />')
        return render_plain.package(json_data['r'])

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
    def __init__(self,web_input,user_id):
        self.user_id = user_id
        self.storage = web_input

        self.pkgs_list = []
        if web_input.has_key('pkgs_list'):
            self.pkgs_list = web_input['pkgs_list'].encode('utf8').split()
            print self.pkgs_list
        print web_input['pkgs_file']
        if web_input['pkgs_file']:
            f = open(outputdir + "/packages_list", "wb")
            lines = web_input['pkgs_file'].file.readlines()
            print lines
            if lines[0].startswith('POPULARITY-CONTEST'):
                del lines[0]
                del lines[-1]
                package_name_field = 2
            else:
                package_name_field = 0
            for line in lines:
                self.pkgs_list.append(line.split()[package_name_field])
                f.write(line)
            f.close()

        if web_input.has_key('limit'):
            self.limit = int(web_input['limit'])
        if web_input.has_key('profile_size'):
            self.profile_size = int(web_input['profile_size'])
        if web_input.has_key('weight'):
            self.weight = web_input['weight'].encode('utf8')

        self.selected_strategies = []
        if web_input.has_key('strategy'):
            if web_input['strategy'].encode('utf8') == "content":
                if (web_input.has_key('tag') and web_input.has_key('desc')):
                    self.selected_strategies.append("cb")
                elif web_input.has_key('desc'):
                    self.selected_strategies.append("cbd")
                else:
                    self.selected_strategies.append("cbt")
            if web_input['strategy'].encode('utf8') == "collab":
                self.selected_strategies.append("col")
            if web_input['strategy'].encode('utf8') == "hybrid":
                self.selected_strategies.append("hybrid")

        if web_input.has_key('cluster'):
            self.cluster = bool(web_input.has_key['cluster'].encode('utf8'))

        if web_input.has_key('neighbours'):
            self.neighbours = int(web_input['neighbours'])

        self.profiles_set = set()
        if web_input.has_key('profile_desktop'):
            self.profiles = self.profiles.add("desktop")
        if web_input.has_key('profile_admin'):
            self.profiles = self.profiles.add("admin")
        if web_input.has_key('profile_devel'):
            self.profiles = self.profiles.add("devel")
        if web_input.has_key('profile_science'):
            self.profiles = self.profiles.add("science")
        if web_input.has_key('profile_arts'):
            self.profiles = self.profiles.add("arts")

    def __str__(self):
        return self.storage

    def validates(self):
        self.errors = []
        if (not self.pkgs_list or not self.selected_strategies):
            self.errors.append("No upload file or packages list was provided.")
            return False
        if not self.selected_strategies:
            self.errors.append("No strategy was selected.")
            return False
        return True

    def get_strategy_details(self):
        return self.selected_strategies[0]

class AppRecommender:
    def POST(self):
        print "post",web.input()
        outputdir = tempfile.mkdtemp(prefix='',dir='./submissions/')
        user_id = outputdir.lstrip('./submissions/')
        print web.input(pkgs_file={})
        request = Request(web.input(pkgs_file={}),user_id)
        if not request.validates():
            return render.error(request.errors)
        else:
            recommendation = self._recommends(request)
            ### Getting package summary (short description) ###
            pkg_summaries = {}
            cache = apt.Cache()
            for strategy, result in recommendation.items():
                for pkg in result:
                    try:
                        pkg_summaries[pkg] = cache[pkg].candidate.summary
                    except:
                        pkg_summaries[pkg] = ""
            return render.apprec(recommendation, pkg_summaries,
                                 FeedbackForm(request.selected_strategies),request)

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

    def _recommends(self,request):
        user = User(dict.fromkeys(request.pkgs_list,1),request.user_id)
        user.maximal_pkg_profile()
        cfg = Config()
        rec = Recommender(cfg)
        results = dict()
        for strategy_str in request.selected_strategies:
            rec.set_strategy(strategy_str)
            prediction = rec.get_recommendation(user).get_prediction(request.limit)
            results[strategy_str] = \
                [result[0] for result in prediction]
        return results

def add_global_hook():
    g = web.storage({"counter": "1"})
    def _wrapper(handler):
        web.ctx.globals = g
        return handler()
    return _wrapper

render = web.template.render('templates/', base='layout')
render_plain = web.template.render('templates/')

urls = ('/',   			    'Index',
        '/apprec',	  	    'AppRecommender',
        '/thanks',   		'Thanks',
        '/about',           'About',
        '/package/(.*)',  	'Package'
       )

web.webapi.internalerror = web.debugerror

if __name__ == "__main__":
   apprec = web.application(urls, globals())
   apprec.add_processor(add_global_hook())
   apprec.run()

