# -*- coding: utf-8 -*-
from micolog_plugin import *
from model import *
import os
import locale
from xml.dom import minidom
import re
import datetime
#from google.appengine.ext import db
#from google.appengine.api import users
#from google.appengine.ext import webapp
class TweetsDigest(Plugin):
    def __init__(self):
        Plugin.__init__(self,__file__)
        self.author="LeiYue"
        self.authoruri="http://www.cqlianan.com"
        self.uri="http://www.cqlianan.com"
        self.description="TweetsDigest fetch user's timeline to post on Micolog from twitter."
        self.register_urlmap("twdigest",self.getRobot)
        self.name="TweetsDigest"
        self.version="0.1.1"

    def get(self,page):
        if page.param("reset")=='1':
            OptionSet.setValue("lastid", "0")
        name = OptionSet.getValue("name",default="leiyue")
        count = OptionSet.getValue("count",default="200")
        url = OptionSet.getValue("url",default="0")
        category = OptionSet.getValue("category",default="0")
        tags = OptionSet.getValue("tags",default="tweetsdigest")
        date = OptionSet.getValue("date",default=False)
        lastid = OptionSet.getValue("lastid",default="0")
        categories = Category.all()
        url = (url == "0") and None or url
        datechecked = date and 'checked="checked"' or ''
        domain = os.environ['HTTP_HOST']
        return self.render_content('TweetsDigest.html',{'name':name ,'count':count,'url':url,'categories':categories,'category':category,'tags':tags,'datechecked':datechecked,'lastid':lastid,'domain':domain})

    def post(self,page):
        number = (locale.atoi(page.param('count')) >= 200 ) and '200' or page.param('count')
        datechecked = page.param("date")
        date = (datechecked == "1") and True or False
        OptionSet.setValue("name",page.param("name"))
        OptionSet.setValue("count",number)
        OptionSet.setValue("url",('http://api.twitter.com/statuses/user_timeline/'+page.param('name')+'.xml?count='+number))
        OptionSet.setValue("category",page.param("category"))
        OptionSet.setValue("date",date)
        OptionSet.setValue("tags",page.param("tags"))
        return self.get(page)

    def make_clickable(self, tweet):
        link_regex = re.compile(r'((ht|f)tp:\/\/w{0,3}[a-zA-Z0-9_\-.:#/~}]+)')
        user_regex = re.compile(r'\s\@([A-Za-z0-9_]+)')
        hash_regex = re.compile(r'\s\#([A-Za-z0-9_]+)')
        tweet = link_regex.sub(lambda m: '<a href="%s">%s</a>' % (m.group(0), m.group(0)), tweet)
        tweet = user_regex.sub(lambda m: '<a href="http://twitter.com/%s">%s</a>' % (m.group(1), m.group(0)), tweet)
        tweet = hash_regex.sub(lambda m: '<a href="http://search.twitter.com/search?q=%%23%s">%s</a>' % (m.group(1), m.group(0)), tweet)
        return tweet

#setup a robot to fetch tweets and post it on Micolog
    def getRobot(self,page=None,*arg1,**arg2):
#        url = 'http://127.0.0.1/leiyue.xml'
        url=OptionSet.getValue("url")
        category=OptionSet.getValue("category")
        tags=OptionSet.getValue("tags")
        lastid=OptionSet.getValue("lastid")
        date = OptionSet.getValue("date")
        count=0

        result = urlfetch.fetch(url)
        if result.status_code == 200:
            html='<ul>\n'
            time_now = datetime.datetime.utcnow()
            time_earlier = time_now - datetime.timedelta(days=7)
            file_xml = minidom.parseString(result.content)
            statusList = file_xml.getElementsByTagName('status')
            for status in statusList:
                tweetid = status.getElementsByTagName('id')[0].firstChild.data
                if lastid == tweetid:
                    break
                tweet = self.make_clickable(status.getElementsByTagName('text')[0].firstChild.data)
                created_at = status.getElementsByTagName('created_at')[0].firstChild.data
                created_time = datetime.datetime.strptime(created_at, '%a %b %d %H:%M:%S +0000 %Y')
                if time_earlier > created_time:
                    break
                if date:
                    tweet += ' (' + datetime.datetime.strftime(created_time, '%Y-%m-%d') + ')'
                html += '<li>' + tweet + '</li>\n'
                count += 1
            html += '</ul>\n'
        else:
            return
        if not count == 0:
            entry = Entry()
            entry.title =' Weekly Twitter Digest ' + time_now.strftime('%F') + ' | ' + time_earlier.strftime('%F')
            entry.content = '<style type="text/css">ul{list-style: circle; list-style-type: circle; list-style-position: initial; list-style-image: initial; margin: 0px 0px 0px 25px;}</style>\n\n' + html
            if not category == '0':
                cs = Category.all().filter('name =',category)
                c=[]
                c.append(cs[0].key())
                entry.categorie_keys = c
            entry.settags(tags)
            entry.save(True)
            OptionSet.setValue("lastid",tweetid)
#            print 'Success!'
            return
