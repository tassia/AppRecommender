#!/usr/bin/env python

import web
from web import form
import tempfile

render = web.template.render('templates/', base='layout')

urls = ('/',		'Index',
        '/feedback',	'FeedbackForm',
        '/thanks',	'FeedbackThanks'
       )

web.webapi.internalerror = web.debugerror

def add_global_hook():
    g = web.storage({"counter": "1"})
    def _wrapper(handler):
        web.ctx.globals = g
        return handler()
    return _wrapper


if __name__ == "__main__":
   app = web.application(urls, globals())
   app.add_processor(add_global_hook())
   app.run()

class Index:
    def GET(self):
        action = "/feedback"
        method = "post"
        return render.index(action, method, self._form())

    def _form(self):
        send_form = form.Form(
            form.File("myfile", description="Packages list"),
            form.Dropdown('Limit results', [('5', '05'), ('10', '10'), ('20', '20')]),
            form.Checkbox("strategy_1", value="True", checked=True, description="Strategy 1"),
            form.Checkbox("strategy_2", value="True", checked=True, description="Strategy 2"),
            form.Checkbox("strategy_3", value="True", checked=True, description="Strategy 3"),
            form.Checkbox("strategy_4", value="True", checked=True, description="Strategy 4"),
            form.Checkbox("strategy_5", value="True", checked=True, description="Strategy 5"),
            form.Checkbox("strategy_6", value="True", checked=True, description="Strategy 6"),

        )
        return send_form()

class FeedbackForm:
    def POST(self):
        action = "/thanks"
        method = "post"
        outputdir = tempfile.mkdtemp() + '/'
        x = web.input(myfile={})
        f = open(outputdir + x['myfile'].filename, "wb")
        content = x['myfile'].value
        while 1:
            chunk = x['myfile'].file.read(10000)
            if not chunk:
                break
            f.write(chunk)
        f.close()
        return render.feedbackForm(action, method, self._recommends(), self._form())

    def _recommends(self):
        results = [['Strategy 1', 'gnome-subtitles', 'brasero', 'inkscape', 'kde'], ['Strategy 2', 'airstrike', 'gimp', 'gthumb', 'iceweasel']]
        return results

    def _form(self):
        send_form = form.Form(
            form.Radio('Strategy 1',[('1','1 '),('2','2 '),('3','3 '),('4','4 '),('5','5')]),
            form.Radio('Strategy 2',[('1','1 '),('2','2 '),('3','3 '),('4','4 '),('5','5')]),
            form.Radio('Strategy 3',[('1','1 '),('2','2 '),('3','3 '),('4','4 '),('5','5')]),
            form.Radio('Strategy 4',[('1','1 '),('2','2 '),('3','3 '),('4','4 '),('5','5')]),
            form.Radio('Strategy 5',[('1','1 '),('2','2 '),('3','3 '),('4','4 '),('5','5')]),
            form.Radio('Strategy 6',[('1','1 '),('2','2 '),('3','3 '),('4','4 '),('5','5')]),
            form.Dropdown('level', ["Newbie", "Intermediate", "Advanced", "Guru", "Chuck Norris"], description ='Expertise'),
            form.Textarea('anything', rows="7", cols="60", description='Anything to share?'),

        )
        return send_form

class FeedbackThanks:
    def POST(self):
        return render.feedbackThanks()
