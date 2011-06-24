#!/usr/bin/env python

import web
from web import form
import tempfile
import sys

sys.path.insert(0,"../")

from config import *
from recommender import *
from user import *

def add_global_hook():
    g = web.storage({"counter": "1"})
    def _wrapper(handler):
        web.ctx.globals = g
        return handler()
    return _wrapper

class Index:
    def GET(self):
        form_action = "/feedback"
        form_method = "post"
        form = self._form()
        return render.index(form_action, form_method, form)

    def _form(self):
        send_form = form.Form(
            form.File("pkgs_file", description="Packages list"),
            form.Dropdown('limit', [('5', '05'), ('10', '10'), ('20', '20')],
                          description = "Limit"),
            form.Checkbox("strategy_cb", value="True", checked=False,
                          description="Content-based"),
            form.Checkbox("strategy_col", value="True", checked=False,
                          description="Collaborative"),
            form.Checkbox("strategy_hybrid", value="True", checked=False,
                          description="Hybrid"),
            form.Checkbox("strategy_hybrid_plus", value="True", checked=False,
                          description="Hybrid plus"),
            validators = [form.Validator("You must select at least one strategy",
                          lambda i: i.strategy_cb | i.startegy_col |
                                    i.strategy_hybrid | i.strategy_hybrid_plus)]
        )
        return send_form()

class FeedbackForm:
    def POST(self):
        action = "/thanks"
        method = "post"
        outputdir = tempfile.mkdtemp(prefix='',dir='./submissions/')
        user_id = outputdir.lstrip('./submissions/')
        x = web.input(pkgs_file={})
        f = open(outputdir + "/packages_list", "wb")
        #content = x['pkgs_file'].value
        self.pkgs_list = []
        for line in x['pkgs_file'].file:
            self.pkgs_list.append(line.split()[0])
            f.write(line)
       # while 1:
       #     chunk = x['pkgs_file'].file.read(10000)
       #     if not chunk:
       #         break
       #     f.write(chunk)
        f.close()

        strategies = []
        if 'strategy_cb' in x: strategies.append("cta")
        if 'strategy_col' in x: strategies.append("col")
        if 'strategy_hybrid' in x: strategies.append("hybrid")
        if 'strategy_hybrid+' in x: strategies.append("hybrid+")

        return render.feedbackForm(action, method,
                                   self._recommends(user_id,strategies),
                                   self._form())

    def _recommends(self,user_id,strategies):
        user = User(dict.fromkeys(self.pkgs_list,1),user_id)
        user.maximal_pkg_profile()
        cfg = Config()
        rec = Recommender(cfg)
        results = dict()
        for strategy in strategies:
            eval("rec."+strategy+"(cfg)")
            prediction = rec.get_recommendation(user).get_prediction()
            results[rec.strategy.description] = [result[0] for result in prediction]
        # Colaborative strategies can not go online yet
        results['Hybrid+'] = []
        results['Hybrid'] = []
        results['Collaborative'] = []
        return results

    def _form(self):
        send_form = form.Form(
            form.Radio('Content-based',
                       [('1','1 '),('2','2 '),('3','3 '),('4','4 '),('5','5')]),
            form.Radio('Collaborative',
                       [('1','1 '),('2','2 '),('3','3 '),('4','4 '),('5','5')]),
            form.Radio('Hybrid',
                       [('1','1 '),('2','2 '),('3','3 '),('4','4 '),('5','5')]),
            form.Radio('Hybrid+',
                       [('1','1 '),('2','2 '),('3','3 '),('4','4 '),('5','5')]),
            form.Dropdown('expertise',
                          ["Newbie", "Intermediate", "Advanced", "Guru", "Chuck Norris"],
                          description ='Debian expertise'),
            form.Textarea('comments', rows="7", cols="60",
                          description="Anything else to share?"),

        )
        return send_form

class FeedbackThanks:
    def POST(self):
        return render.feedbackThanks()

render = web.template.render('templates/', base='layout')

urls = ('/',    		'Index',
        '/feedback',	'FeedbackForm',
        '/thanks',  	'FeedbackThanks'
       )

web.webapi.internalerror = web.debugerror

if __name__ == "__main__":
   app = web.application(urls, globals())
   app.add_processor(add_global_hook())
   app.run()

