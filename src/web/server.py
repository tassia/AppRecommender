#!/usr/bin/env python

import web
from web import form
import tempfile
import sys
import simplejson as json

sys.path.insert(0,"../")

from config import *
from recommender import *
from user import *

import urllib

class RequestForm(form.Form):
    def __init__(self):
        form.Form.__init__(self, \
            form.File("pkgs_file", size=35, description="Upload file"),
            form.Textarea("pkgs_list", description="Packages",
                          rows="4", cols="52"),
            form.Dropdown('limit', [(5, '05'), (10, '10'), (20, '20')],
                          description = "Limit"),
            form.Checkbox("strategy_cb", value=1, checked=False,
                          description="Content-based"),
            form.Checkbox("strategy_col", value=1, checked=False,
                          description="Collaborative"),
            form.Checkbox("strategy_hybrid", value="True", checked=False,
                          description="Hybrid"),
            form.Checkbox("strategy_hybrid_plus", value="True", checked=False,
                          description="Hybrid plus"),
            validators = [form.Validator("No packages list provided.",
                                  lambda f: f.has_key("pkgs_list") |
                                            f.has_key("pkgs_file") ),
                          form.Validator("No strategy selected.",
                                  lambda f: f.has_key("strategy_cb") |
                                            f.has_key("startegy_col") |
                                            f.has_key("strategy_hybrid") |
                                            f.has_key("strategy_hybrid_plus")) ])

class FeedbackForm(form.Form):
    def __init__(self,strategies):
        desc_dict = {"cta": "Content-based", "col": "Collaborative",
                     "hybrid": "Hybrib", "hybrid_plus": "Hybrid Plus"}
        fields = []
        for strategy in strategies:
            fields.append(form.Radio(desc_dict[strategy],
                [('1','1 '),('2','2 '),('3','3'),('4','4 '),('5','5')]))
        form.Form.__init__(self, *fields, validators = [])

class Index:
    def GET(self):
        return render.index("/apprec", "post", RequestForm())

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
        print json_data['r']['long_description']
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


class AppRecommender:
    def POST(self):
        outputdir = tempfile.mkdtemp(prefix='',dir='./submissions/')
        user_id = outputdir.lstrip('./submissions/')
        request = RequestForm()
        request_info = web.input(pkgs_file={})
        if not request.validates(request_info):
            return render.error(request)
        else:
            user_pkgs_list = []
            if request_info.has_key('pkgs_list'):
                user_pkgs_list = request_info['pkgs_list'].encode('utf8').split()
                print user_pkgs_list

            if request_info['pkgs_file'].value:
                f = open(outputdir + "/packages_list", "wb")
                lines = request_info['pkgs_file'].file.readlines()
                print lines
                if lines[0].startswith('POPULARITY-CONTEST'):
                    del lines[0]
                    del lines[-1]
                    package_name_field = 2
                else:
                    package_name_field = 0
                for line in lines:
                    user_pkgs_list.append(line.split()[package_name_field])
                    f.write(line)
                f.close()

            strategies = []
            if request_info.has_key('strategy_cb'): strategies.append("cta")
            ### Colaborative strategies can not go online yet
            if request_info.has_key('strategy_col'): strategies.append("col")
            if request_info.has_key('strategy_hybrid'):
                strategies.append("hybrid")
            if request_info.has_key('strategy_hybrid_plus'):
                strategies.append("hybrid_plus")
            recommends = self._recommends(user_id,user_pkgs_list,strategies, int(request_info['limit']))
            return render.apprec("/thanks", "post", recommends, FeedbackForm(strategies))

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

    def _get_pkg_attrs(self, pkg_name):
        pass

    def _recommends(self,user_id,user_pkgs_list,strategies,limit):
        user = User(dict.fromkeys(user_pkgs_list,1),user_id)
        user.maximal_pkg_profile()
        cfg = Config()
        rec = Recommender(cfg)
        results = dict()
        for strategy in strategies:
            ### Colaborative strategies can not go online yet
            #eval("rec."+strategy+"(cfg)")
            rec.cta(cfg)
            prediction = rec.get_recommendation(user).get_prediction(limit)
            results[rec.strategy.description] = \
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

urls = ('/',   			'Index',
        '/apprec',	  	'AppRecommender',
        '/thanks',   		'Thanks',
        '/package/(.*)',  	'Package'
       )

web.webapi.internalerror = web.debugerror

if __name__ == "__main__":
   apprec = web.application(urls, globals())
   apprec.add_processor(add_global_hook())
   apprec.run()

