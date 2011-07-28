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

#class FeedbackForm(form.Form):
#    def __init__(self,selected_strategies):
#        desc_dict = {"cb": "Content-based", "cbt": "Content-based",
#                     "cbd": "Content-based", "col": "Collaborative",
#                     "hybrid": "Hybrib"}
#        fields = []
#        for strategy in selected_strategies:
#            fields.append(form.Radio(desc_dict[strategy],
#                [('1','1 '),('2','2 '),('3','3'),('4','4 '),('5','5')]))
#        form.Form.__init__(self, *fields, validators = [])

class Index:
    def GET(self):
        if Config().survey_mode:
            return render.survey_index()
        else:
            return render.index()

class About:
    def GET(self):
        return render.about()

#class Support:
#    def GET(self):
#        return render.support()

class Thanks:
    def POST(self):
        return render.thanks()

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
    def __init__(self,web_input):
        submissions_dir = "./submissions/"
        if not os.path.exists(submissions_dir):
            os.makedirs(submissions_dir)
        outputdir = tempfile.mkdtemp(prefix='',dir=submissions_dir)
        user_id = outputdir.lstrip(submissions_dir)
        self.user_id = user_id
        self.storage = web_input

        self.pkgs_list = []
        if web_input.has_key('pkgs_list'):
            self.pkgs_list = web_input['pkgs_list'].encode('utf8').split()
        if web_input['pkgs_file'].value:
            f = open(outputdir + "/packages_list", "wb")
            lines = web_input['pkgs_file'].file.readlines()
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
            if (web_input['strategy'].encode('utf8') == "content" or
                web_input['strategy'].encode('utf8') == "hybrid"):
                if (web_input.has_key('tag') and web_input.has_key('desc')):
                    self.selected_strategies.append("cb")
                elif web_input.has_key('desc'):
                    self.selected_strategies.append("cbd")
                else:
                    self.selected_strategies.append("cbt")
            if (web_input['strategy'].encode('utf8') == "collab" or
                web_input['strategy'].encode('utf8') == "hybrid"):
                self.selected_strategies.append("col")

        if web_input.has_key('cluster'):
            self.cluster = web_input['cluster'].encode('utf8')

        if web_input.has_key('neighbours'):
            self.neighbours = int(web_input['neighbours'])

        self.profiles_set = set()
        if web_input.has_key('profile_desktop'):
            self.profiles_set.add("desktop")
        if web_input.has_key('profile_admin'):
            self.profiles_set.add("admin")
        if web_input.has_key('profile_devel'):
            self.profiles_set.add("devel")
        if web_input.has_key('profile_science'):
            self.profiles_set.add("science")
        if web_input.has_key('profile_arts'):
            self.profiles_set.add("arts")

    def __str__(self):
        return self.storage

    def validates(self):
        self.errors = []
        if not self.pkgs_list:
            self.errors.append("No upload file or packages list was provided.")
        if not self.selected_strategies:
            self.errors.append("No strategy was selected.")
        if self.errors:
            return False
        return True

    def get_details(self):
        details = {}
        details['User id'] = self.user_id
        if len(self.pkgs_list)>10:
            details['Packages list'] = (" ".join(self.pkgs_list[:5])
                                        +" ... ("+str(len(self.pkgs_list)-10)
                                        +" more)")
        else:
            details['Packages list'] = " ".join(self.pkgs_list)

        if self.storage.has_key('pkgs_list') and self.storage['pkgs_file']:
            details['User profile'] = "from upload file and packages list"
        elif self.storage.has_key('pkgs_list'):
            details['User profile'] = "from packages list"
        else:
            details['User profile'] = "from upload file"

        if self.storage.has_key('limit'):
            details['Recommendation size'] = self.limit
        if self.storage.has_key('profile_size'):
            details['Profile size'] = self.profile_size
        if self.storage.has_key('weight'):
            if self.weight == "trad":
                details['weight'] = "traditional"
            else:
                details['weight'] = "BM25"

        if self.profiles_set:
            details['Personal profile'] = " ".join(list(self.profiles_set))

        if len(self.selected_strategies) > 1: details['strategy'] = "Hybrid"
        for strategy in self.selected_strategies:
            if strategy == "col":
                if not details.has_key('strategy'):
                    details['Strategy'] = "Collaborative"
                if self.storage.has_key('cluster'):
                    details['Cluster'] = self.cluster
                if self.storage.has_key('neighbours'):
                    details['Neighbours'] = self.neighbours
                if not details.has_key('strategy'):
                    details['Strategy'] = "Collaborative"
            else:
                if not details.has_key('strategy'):
                    details['Strategy'] = "Content-based"
                if "cb" in self.selected_strategies:
                    details['Content representation'] = "tags and descriptions"
                elif "cbt" in self.selected_strategies:
                    details['Content representation'] = "packages tags"
                elif "cbd" in self.selected_strategies:
                    details['Content representation'] = "packages descriptions"

        print details
        return details

#class RandomRequest(Request):
#    def __init__(self):
#        pass
#        #self.storage = web.Storage()

class AppRecommender:
    def __init__(self):
        self.cfg = Config()
        self.rec = Recommender(self.cfg)

    def POST(self):
        request = Request(web.input(pkgs_file={}))
        if not request.validates():
            return render.error(request.errors)
        else:
            recommendation = self._recommends(request)
            ### Getting package summary (short description) ###
            pkg_summaries = {}
            pkg_details = []
            cache = apt.Cache()
            for strategy, result in recommendation.items():
                for pkg in result:
                    try:
                        pkg_summaries[pkg] = cache[pkg].candidate.summary
                        pkg_details.append(Package().get_details_from_dde(pkg))
                    except:
                        pkg_summaries[pkg] = ""
            if Config().survey_mode:
                return render.survey(recommendation, pkg_details,
                                     FeedbackForm(request.selected_strategies))
            else:
                return render.apprec(recommendation, pkg_summaries, request)

    def _recommends(self,request):
        user = User(dict.fromkeys(request.pkgs_list,1),request.user_id)
        user.maximal_pkg_profile()
        results = dict()
        for strategy_str in request.selected_strategies:
            self.rec.set_strategy(strategy_str)
            prediction = self.rec.get_recommendation(user,10).get_prediction()
            print prediction
            results[strategy_str] = \
                [result[0] for result in prediction]
        return results

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

def add_global_hook():
    g = web.storage({"counter": "1"})
    def _wrapper(handler):
        web.ctx.globals = g
        return handler()
    return _wrapper

render = web.template.render('templates/', base='layout')
render_plain = web.template.render('templates/')

urls = ('/',   		        'Index',
        '/apprec',		    'AppRecommender',
        '/thanks',   		'Thanks',
        '/support',         'Support',
        '/about',           'About',
        '/package/(.*)',  	'Package'
       )

web.webapi.internalerror = web.debugerror

if __name__ == "__main__":
   apprec = web.application(urls, globals())
   apprec.add_processor(add_global_hook())
   apprec.run()

